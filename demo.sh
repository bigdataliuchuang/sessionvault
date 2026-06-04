#!/bin/bash
# SessionVault Demo Recording Script
# Usage: Install asciinema and agg, then run this script
# brew install asciinema agg

echo "=== SessionVault Demo ==="
echo ""
echo "This script demonstrates the key features."
echo "To record as GIF:"
echo "  1. asciinema rec demo.cast"
echo "  2. Run this script"
echo "  3. Ctrl+D to stop recording"
echo "  4. agg demo.cast demo.gif"
echo ""

# Demo 1: Stats
echo "📊 查看统计..."
sessionvault stats
echo ""
sleep 2

# Demo 2: Search
echo "🔍 搜索对话..."
sessionvault search "牙齿" --limit 3
echo ""
sleep 2

# Demo 3: Projects
echo "📁 列出项目..."
sessionvault projects
echo ""
sleep 2

# Demo 4: Sessions
echo "📋 列出会话..."
sessionvault sessions --limit 5
echo ""
sleep 2

echo "✅ Demo 完成！"
echo ""
echo "录制 GIF 步骤："
echo "  1. brew install asciinema agg"
echo "  2. asciinema rec demo.cast"
echo "  3. bash demo.sh"
echo "  4. Ctrl+D 停止录制"
echo "  5. agg demo.cast demo.gif"
echo "  6. 将 demo.gif 添加到 README.md"
