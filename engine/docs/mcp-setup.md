# MCP Server Setup

## Configuration Location

MCP servers can be configured at two levels:

1. **Global** (all VS Code workspaces)

   - File: `~/Library/Application Support/Code/User/settings.json` (macOS)
   - Affects all projects

2. **Workspace** (this project only)
   - File: `.vscode/settings.json`
   - Affects only this workspace

**Recommendation:** Use **workspace** level for project-specific MCPs.

---

## Setup Personal Library MCP

### Option 1: Via VS Code UI (Easiest)

1. Open Command Palette (`Cmd+Shift+P`)
2. Search: "Preferences: Open User Settings (JSON)" or "Preferences: Open Workspace Settings (JSON)"
3. Add this configuration:

```json
{
  "chat.mcp.servers": {
    "personal-library": {
      "command": "/opt/homebrew/bin/python3.11",
      "args": [
        "/Users/nfrota/Documents/personal library/scripts/mcp_server.py"
      ],
      "description": "Personal book library RAG",
      "enabled": true
    }
  }
}
```

4. Save and reload VS Code
5. Check "MCP Servers" view - should show "personal-library" running

---

### Option 2: Manual Edit

**Workspace-level** (recommended):

```bash
# Edit workspace settings
code .vscode/settings.json
```

Add the MCP configuration from [mcp-config.json](mcp-config.json).

**Global-level:**

```bash
# Edit global settings
code ~/Library/Application\ Support/Code/User/settings.json
```

---

## Remove Old Literature MCP

If you see "literature" with error status:

1. Find where it's configured (global or workspace settings)
2. Remove or disable:

```json
{
  "chat.mcp.servers": {
    "literature": {
      "enabled": false // Disable old MCP
    }
  }
}
```

Or delete the entire "literature" entry.

---

## Verify MCP is Running

### In VS Code:

1. Open "MCP Servers" view (sidebar)
2. Look for "personal-library"
3. Status should be "Running"

### Test via terminal:

```bash
# Start MCP manually
python3.11 scripts/mcp_server.py
```

Should show:

```
Personal Library MCP Server started
Loading embedding model...
Loading FAISS index...
✅ Resources loaded (11,764 vectors)
```

Then try sending JSON request:

```json
{ "method": "tools/list" }
```

Should return available tools.

---

## Troubleshooting

**"Process exited with code 2"**

- MCP script crashed
- Check logs: Look for Python errors in MCP Servers view
- Run manually to see error: `python3.11 scripts/mcp_server.py`

**"MCP not connected"**

- Settings not loaded
- Reload VS Code window
- Check settings syntax (valid JSON)

**"Cannot find module"**

- Missing dependencies
- Run: `./scripts/setup.sh`
- Verify: `python3.11 -c "import faiss; import sentence_transformers"`

**Path issues:**

- Update paths in config to match your installation
- Use absolute paths (not `~` or `./`)
- Escape spaces: `/Users/nfrota/Documents/personal\ library/`

---

## Configuration Reference

| Setting       | Description            | Required           |
| ------------- | ---------------------- | ------------------ |
| `command`     | Python executable path | Yes                |
| `args`        | Script path            | Yes                |
| `description` | Human-readable name    | No                 |
| `enabled`     | Enable/disable server  | No (default: true) |
| `env`         | Environment variables  | No                 |

**Example with env vars:**

```json
{
  "chat.mcp.servers": {
    "personal-library": {
      "command": "/opt/homebrew/bin/python3.11",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/custom/modules",
        "LOG_LEVEL": "DEBUG"
      },
      "enabled": true
    }
  }
}
```

---

## Multiple MCPs

You can run multiple MCP servers:

```json
{
  "chat.mcp.servers": {
    "personal-library": { ... },
    "figma": { ... },
    "pylance": { ... }
  }
}
```

Each runs independently.
