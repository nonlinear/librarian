# Personal Library MCP Extension

VS Code extension that registers the Personal Library MCP server for searching your book collection.

## Features

- **Instant activation** - No stdio timeout issues
- **Lazy loading** - Topics load on first query (~2s), then cached
- **7 indexed topics** - AI, activism, anthropocene, fiction, oracles, urbanism, usability

## Usage

1. Extension auto-activates on VS Code startup
2. Use `/research` in GitHub Copilot chat
3. Ask questions about your books: "what books discuss AI ethics?"

## Architecture

- **Extension** - Registers MCP server with VS Code
- **Python server** - `scripts/mcp_server_lazy.py` handles queries
- **Storage** - `storage/` contains partitioned FAISS indices

## Development

```bash
cd .vscode/extensions/personal-library-mcp
npm install
npm run compile
```

Reload VS Code (Cmd+R) to test changes.
