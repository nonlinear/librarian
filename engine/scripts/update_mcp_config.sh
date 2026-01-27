#!/bin/bash
# Update VS Code global MCP config to point to new librarian path

SETTINGS_FILE="$HOME/Library/Application Support/Code/User/settings.json"
BACKUP_FILE="$HOME/Library/Application Support/Code/User/settings.json.backup.$(date +%Y%m%d_%H%M%S)"

echo "📋 Backing up settings to: $BACKUP_FILE"
cp "$SETTINGS_FILE" "$BACKUP_FILE"

echo "🔧 Updating MCP config..."

# Use Python for JSON manipulation to avoid breaking the file
python3 << 'EOF'
import json
from pathlib import Path

settings_file = Path.home() / "Library/Application Support/Code/User/settings.json"

with open(settings_file, 'r') as f:
    settings = json.load(f)

# Update MCP config
if "chat.mcp.servers" in settings:
    if "personal-library" in settings["chat.mcp.servers"]:
        # Update existing config
        settings["chat.mcp.servers"]["personal-library"]["command"] = "/opt/homebrew/bin/python3"
        settings["chat.mcp.servers"]["personal-library"]["args"] = [
            "/Users/nfrota/Documents/librarian/engine/scripts/mcp_server.py"
        ]
        settings["chat.mcp.servers"]["personal-library"]["description"] = "Personal book library RAG (v2.0)"
        print("✅ Updated existing 'personal-library' MCP config")
    else:
        # Add new config
        settings["chat.mcp.servers"]["librarian"] = {
            "command": "/opt/homebrew/bin/python3",
            "args": ["/Users/nfrota/Documents/librarian/engine/scripts/mcp_server.py"],
            "description": "Personal book library RAG (v2.0)",
            "enabled": True
        }
        print("✅ Added new 'librarian' MCP config")
else:
    # Create MCP config from scratch
    settings["chat.mcp.servers"] = {
        "librarian": {
            "command": "/opt/homebrew/bin/python3",
            "args": ["/Users/nfrota/Documents/librarian/engine/scripts/mcp_server.py"],
            "description": "Personal book library RAG (v2.0)",
            "enabled": True
        }
    }
    print("✅ Created MCP config section")

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("✅ Settings updated successfully")
EOF

echo ""
echo "🎯 Next steps:"
echo "   1. Reload VS Code: Cmd+Shift+P → 'Developer: Reload Window'"
echo "   2. Test MCP: Ask Copilot to 'list librarian topics'"
echo ""
echo "📝 Backup saved to: $BACKUP_FILE"
