# Personal Library MCP - Troubleshooting

**Repo**: https://github.com/nonlinear/personal-library (private)

## Problem

MCP server takes **30+ seconds** to start, causing VS Code blocking dialog:

- "Starting MCP servers Personal Library... Skip?"
- Blocks all work, forces user to click Skip
- `/research` never becomes available

## Root Cause

**`storage/docstore.json` = 17MB** with huge chunks (entire book indexes)

- Python parsing 17MB JSON is the bottleneck
- `faiss.index` (75KB) and `metadata.json` (19KB) load fast
- Example: chunk 0 contains full remissive index of "The Open Organization"

## Current Solution: Background Loading (Testing)

**Status**: Committed (32f6080), running in terminal now - **NOT YET CONFIRMED**

**Logic**:

- Load `metadata.json` (19KB) synchronously in `main()`
- Spawn daemon thread to load FAISS + docstore (17MB) in background
- Server responds "ready" immediately (<1s target)
- First query waits if loading not complete

**Modified file**: [`scripts/mcp_server.py`](https://github.com/nonlinear/personal-library/blob/main/scripts/mcp_server.py)

## Failed Attempts

1. **Lazy loading** - Still blocked on first query
2. **FAISS migration** - Hit Gemini API quota (3000/min)
3. **ChromaDB** - Added 19MB dependencies, protobuf conflicts

## Alternatives if Background Loading Fails

### Option 1: Partitioned Docstore (User Suggestion) ⭐

Split `docstore.json` into 9 topic-specific files:

- `storage/activism/docstore.json` (~2MB each)
- True lazy loading: load only relevant topics
- **Cons**: Full reindexing needed, query complexity

### Option 2: Filter Large Chunks

Reindex excluding chunks >10KB (book indexes):

- Reduce docstore from 17MB → ~5MB
- Better response quality (no useless indexes)
- **Cons**: Slow reindexing (API quota), may lose context

### Option 3: Disable MCP Temporarily

Edit `~/Library/Application Support/Code/User/mcp.json`:

- Allows normal work while debugging
- No pressure testing

### Option 4: Revert to Deprecated System

Old `.rag-topics.md` per folder:

- Reindexed every query (slow but worked)
- No startup delay, no persistence

## Architecture

**Stack**: Python 3.11 + FAISS + Gemini embeddings + MCP stdio

**Storage**:

- [`storage/faiss.index`](https://github.com/nonlinear/personal-library/blob/main/storage/faiss.index) (75KB) - vectors only
- [`storage/metadata.json`](https://github.com/nonlinear/personal-library/blob/main/storage/metadata.json) (19KB) - topics/books map
- [`storage/docstore.json`](https://github.com/nonlinear/personal-library/blob/main/storage/docstore.json) (17MB) - actual text chunks ← **bottleneck**

**Query flow**: Question → Gemini embedding → FAISS search → docstore lookup → return chunks

## Performance Metrics

- **Target**: <1s startup, no VS Code blocking
- **Current**: 30+ seconds, always blocks
- **Expected (FAISS)**: ~1s load, 350ms query
- **Current (LlamaIndex)**: 12-30s load, 400ms query

## Next Steps

1. Check terminal logs (ID: `1f594fbf-772c-4615-831d-155f12697b6d`)
2. **If SUCCESS**: Test `/research`, celebrate 🎉
3. **If FAILED**:
   - Debug why thread didn't return "ready" fast
   - Consider Option 1 (partitioned) or Option 2 (filter chunks)

## Migration History

1. `.rag-topics.md` files (deprecated, but fast)
2. FAISS attempt (blocked by API quota)
3. LlamaIndex 92MB JSON (current, slow)
4. Background loading (testing now)

## Key Files

- `~/Library/Application Support/Code/User/mcp.json` - VS Code MCP config (local)
- [`.github/prompts/research.prompt.md`](https://github.com/nonlinear/personal-library/blob/main/.github/prompts/research.prompt.md) - `/research` instructions
- [`scripts/mcp_server.py`](https://github.com/nonlinear/personal-library/blob/main/scripts/mcp_server.py) - MCP server (modified with threading)

## Notes

- Repo is **private** (contains PII)
- User extremely frustrated with 30s startup blocking workflow
- Background loading is **last attempt** before architectural rethink
- **We don't know yet** if background loading actually works
