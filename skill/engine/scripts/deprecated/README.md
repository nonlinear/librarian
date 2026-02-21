# ⚠️ DEPRECATED SCRIPTS - DO NOT USE ⚠️

**Status:** Reference only, not actively maintained.

**❌ DO NOT:**

- Fix bugs in these files
- Run these scripts in production
- Reference these in documentation
- Waste time understanding their logic

**✅ INSTEAD USE:**

- `index_library.py` - ONE script for all indexing (replaces generate_metadata.py, indexer.py)
- `research.py` - CLI tool (stable, works)
- `mcp_server.py` - MCP wrapper (delegates to research.py)

---

## v2.0 Migration (2026-01-26)

Moved v1.0 schema scripts to deprecated:

### V1.0 Schema Scripts (OBSOLETE)

- `analyze_library.py` - uses `metadata.json` instead of `.library-index.json`
- `generate_metadata.py` - v1.0 schema generator
- `indexer.py` - v1.0 indexing logic, uses `metadata.json`
- `partition_storage.py` - v1.0 storage partitioning, uses `chunks.pkl`
- `reindex_all.py` - v1.0 reindexing, uses `metadata.json`
- `migrate_to_v2.py` - one-time migration script (already completed)

### Temporary/Test Files

- `tmp_stability_check.sh` - temporary stability check
- `test_chunking.py` - outdated chunking tests
- `mcp_server.py.old` - 562-line bloated MCP server (replaced with 170-line minimal wrapper)

### Current Architecture (v2.0)

**Active scripts:**

- `research.py` - Core query logic (single source of truth)
- `mcp_server.py` - Thin MCP protocol wrapper (delegates to research.py)
- `index_library.py` - v2.0 indexing
- `watch_library.py` - File watcher for auto-reindexing
- `setup.sh` / `start_watchdog.sh` - Environment setup

**Schema v2.0:**

- `.library-index.json` - Main registry (54 topics)
- `.topic-index.json` - Per-topic book metadata
- `.chunks.json` - Per-topic embeddings (JSON not pickle)
- `.faiss.index` - Per-topic vector index

**Design principles:**

1. **Single source of truth** - research.py contains all query logic
2. **Modularity** - MCP server is thin wrapper, doesn't duplicate logic
3. **Local-first** - no API calls, fully offline
4. **JSON over pickle** - human-readable storage

## Gemini Era Scripts (Pre-v1.0)

These are from the original Gemini embeddings implementation:

- `update_literature.py` → replaced by `index_library.py`
- `query_book.py` → replaced by `research.py`
- `literature_mcp_server.py` → replaced by `mcp_server.py`
- Gemini embeddings → local BAAI/bge-small-en-v1.5
- Multiple `.rag-topics` files → `.library-index.json` registry

Keep these for historical reference only.
