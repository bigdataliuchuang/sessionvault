"""Configuration management for sessionvault."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Global configuration."""
    data_dir: Path = field(default_factory=lambda: Path.home() / ".sessionvault")
    log_level: str = "INFO"
    db_name: str = "data.db"
    retention_days: int = 30

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_name


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
        # Override from environment
        if v := os.environ.get("SESSIONVAULT_DATA_DIR"):
            _config.data_dir = Path(v)
        if v := os.environ.get("SESSIONVAULT_LOG_LEVEL"):
            _config.log_level = v
        _config.data_dir.mkdir(parents=True, exist_ok=True)
    return _config


def set_config(config: Config) -> None:
    global _config
    _config = config
