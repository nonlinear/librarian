# Deprecated Scripts

These scripts are from the previous MCP implementation using Gemini embeddings.

**Status:** Reference only, not actively maintained.

## Migration Path

Old → New:

- `update_literature.py` → `generate_metadata.py` + `indexer.py` (TBD)
- `query_book.py` → MCP query handler (TBD)
- Gemini embeddings → local `all-MiniLM-L6-v2`
- Multiple `.rag-topics` files → single `metadata.json`

## Why Deprecated?

The new architecture prioritizes:

1. **Local-first** (no Gemini API calls)
2. **Lower latency** (FAISS instead of remote embeddings)
3. **Map ≠ Territory** (single metadata.json for navigation)
4. **Client-agnostic backend** (MCP as service, not VS Code specific)

Keep these for reference if needed to understand the old system.
