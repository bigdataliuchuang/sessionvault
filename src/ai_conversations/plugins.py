"""External plugin system for SessionVault.

Plugins are Python files placed in ~/.sessionvault/plugins/.
Each plugin must define:
    TOOL_NAME: str               — unique tool identifier (e.g. "my-tool")
    EXTRACTOR_CLASS: type        — optional; a BaseExtractor subclass.
                                   If omitted, EXTRACT function is wrapped automatically.

    def extract(since=None, project=None) -> Generator[Conversation, None, None]:
        ...

Alternatively, plugins may provide an EXTRACTOR_CLASS that inherits from
BaseExtractor directly, in which case TOOL_NAME is read from the class.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Generator, Optional, Type

from .extractors.base import BaseExtractor
from .models import Conversation
from .paths import get_data_dir

logger = logging.getLogger(__name__)

PLUGIN_DIR = get_data_dir() / "plugins"


class PluginExtractor(BaseExtractor):
    """Wraps a plain plugin module's extract() as a BaseExtractor."""

    def __init__(self, module: ModuleType) -> None:
        self._module = module
        self.tool_name = getattr(module, "TOOL_NAME", module.__name__)

    def extract(
        self,
        since: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Generator[Conversation, None, None]:
        yield from self._module.extract(since=since, project=project)


def _load_module_from_file(path: Path) -> Optional[ModuleType]:
    """Load a single Python file as a module, returning None on failure."""
    module_name = f"sessionvault_plugin_{path.stem}"
    # Avoid double-loading if already in sys.modules
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        logger.warning("Cannot load plugin spec from %s", path)
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception:
        logger.exception("Failed to load plugin %s", path)
        return None

    sys.modules[module_name] = module
    return module


def _make_extractor(module: ModuleType) -> Optional[BaseExtractor]:
    """Create a BaseExtractor from a plugin module."""
    # If the plugin provides its own extractor class, use it.
    extractor_cls: Optional[Type[BaseExtractor]] = getattr(
        module, "EXTRACTOR_CLASS", None
    )
    if extractor_cls is not None and (
        isinstance(extractor_cls, type) and issubclass(extractor_cls, BaseExtractor)
    ):
        return extractor_cls()

    # Otherwise wrap the module-level extract() function.
    extract_fn = getattr(module, "extract", None)
    if not callable(extract_fn):
        logger.warning(
            "Plugin %s has no extract() function or EXTRACTOR_CLASS; skipping",
            module.__name__,
        )
        return None

    return PluginExtractor(module)


def load_plugins() -> Dict[str, BaseExtractor]:
    """Discover and load all plugins from ~/.sessionvault/plugins/.

    Returns a dict mapping tool_name -> extractor instance.
    """
    registry: Dict[str, BaseExtractor] = {}

    if not PLUGIN_DIR.is_dir():
        return registry

    for py_file in sorted(PLUGIN_DIR.glob("*.py")):
        if py_file.name.startswith("_"):
            continue  # skip private/helper files

        module = _load_module_from_file(py_file)
        if module is None:
            continue

        extractor = _make_extractor(module)
        if extractor is None:
            continue

        tool_name = extractor.tool_name
        if not tool_name:
            logger.warning(
                "Plugin %s has empty TOOL_NAME; using filename", py_file.name
            )
            tool_name = py_file.stem

        logger.info("Loaded plugin: %s (%s)", tool_name, py_file.name)
        registry[tool_name] = extractor

    return registry
