# Librarian Specifications

## What Happens on First Run

1. **Docker build** (~5-10 min)
   - Installs Python 3.11
   - Installs dependencies (torch, sentence-transformers, FAISS, etc.)
   - Downloads ~1-2GB of libraries
   - ✅ Tested and working

2. **Model download** (~1-2 min)
   - Downloads BAAI/bge-small-en-v1.5 embedding model (~130MB)
   - Cached in `engine/models/` for future runs
   - ✅ Tested and working

3. **Container starts** (~5 sec)
   - File watcher activates (auto-detects new books)
   - EPUB reader starts (http://localhost:8088)
   - MCP server ready
   - ✅ Tested and working

4. **Indexing** (~2-5 min per 100 books)
   - Extracts text from EPUB/PDF
   - Generates embeddings
   - Builds FAISS index
   - ⚠️ **Requires 16GB Docker memory**

**After first run:** Adding new books takes <10s (incremental indexing).

---

## MCP Connection

**Claude Desktop:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

**OpenClaw:** Edit with `openclaw config edit` or check existing with `openclaw config get mcp`

```json
{
  "mcpServers": {
    "librarian": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "librarian",
        "python3",
        "/app/engine/scripts/mcp_server_faiss.py"
      ]
    }
  }
}
```

Restart your AI client and test: "Search my library for books about design systems"

---

## Troubleshooting

### First Install Issues

#### Container crashes during indexing (code 137)
**Cause:** Docker out of memory (OOM)

**Fix:**
1. Open **Docker Desktop**
2. Go to **Settings → Resources**
3. Increase **Memory** to **16GB** (minimum)
4. Click **Apply & Restart**
5. Try again: `docker-compose up -d`

**Why:** Embedding model + torch + indexing uses ~8-12GB during first run

#### Docker build taking too long
**Normal:** First build downloads ~1-2GB of dependencies (torch, CUDA libs, etc.)
**Time:** 5-15 minutes depending on internet speed
**Fix:** Be patient, it's cached for future runs

#### Container exits immediately
```bash
# Check logs
docker logs librarian

# Common causes:
# 1. Port 8088 already in use → change in docker-compose.yml
# 2. Out of memory → close other apps or increase Docker RAM
```

#### Model download fails
```bash
# Manual download inside container
docker exec -it librarian bash
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5', cache_folder='/app/engine/models')"
exit

# Restart container
docker-compose restart
```

### Usage Issues

#### Indexing stuck
```bash
# Restart container
docker-compose restart

# Force reindex
docker exec librarian python3 /app/engine/scripts/indexer_v6.py
```

### No results for query
1. Check books indexed: `docker exec librarian cat /app/books/.index_state.json | jq .total_books`
2. Check FAISS loaded: `docker logs librarian | grep "FAISS loaded"`
3. Try broader terms

### Watcher not detecting new books
```bash
# Check watcher is running
docker logs librarian | grep "Watcher active"

# Restart watcher
docker-compose restart
```
