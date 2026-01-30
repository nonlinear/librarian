# Advanced Usage

Advanced features and troubleshooting for Librarian MCP.

## Command-Line Flags

### `index_library.py`

Main indexing script with delta detection and model selection.

```bash
# Smart mode: detect file changes, only reindex affected topics
python3.11 engine/scripts/index_library.py --smart

# Index all topics (with hash-based delta detection)
python3.11 engine/scripts/index_library.py --all

# Index specific topic
python3.11 engine/scripts/index_library.py --topic "theory/anthropocene"

# Force reindex (ignore delta detection)
python3.11 engine/scripts/index_library.py --all --force

# Use different embedding model
python3.11 engine/scripts/index_library.py --all --model bge      # Better quality, slower
python3.11 engine/scripts/index_library.py --all --model minilm   # Faster, lightweight

# Show help
python3.11 engine/scripts/index_library.py --help
```

**Flags:**

- `--smart`: Smart mode - detect file-level changes, only reindex affected topics
- `--all`: Index all topics (with hash-based delta detection)
- `--topic <name>`: Index single topic (e.g., "AI/policy", "theory/anthropocene")
- `--force`: Skip delta detection, reindex everything
- `--model <name>`: Embedding model: `bge` (better quality, default) or `minilm` (faster)
- `--help`: Show usage information

**Delta Detection:**
Without `--force`, indexer only reindexes topics where files changed (using content hashes).

⚠️ **Note:** `reindex_topic.py` is deprecated. Use `index_library.py --topic "topic_name"` instead.

---

### `research.py`

CLI wrapper for querying (used by VS Code extension).

```bash
# Search all topics
python3.11 engine/scripts/research.py "design patterns" --top-k 5

# Search specific topic
python3.11 engine/scripts/research.py "permaculture" --topic "plants" --top-k 3

# List available topics
python3.11 engine/scripts/research.py --list-topics
```

**Flags:**

- `--topic <name>`: Search within specific topic
- `--top-k <n>`: Number of results (default: 5)
- `--list-topics`: Show all indexed topics

**Output:** JSON array (for VS Code extension integration)

---

## Troubleshooting

### MCP Server Won't Start

**Symptom:** `mcp_server.py` fails with "metadata.json not found"

**Solution:** Server uses **v2.0 schema** (`library-index.json`) with fallback to v1.0 (`metadata.json`).

Check if indexed:

```bash
ls -la books/library-index.json
```

If missing, run:

```bash
python3.11 engine/scripts/index_library.py --all
```

---

### Query Returns No Results

**Possible causes:**

1. Topic not indexed
2. Faiss index corrupted
3. Wrong topic name

**Debug steps:**

```bash
# List all indexed topics
python3.11 engine/scripts/research.py --list-topics

# Check topic has index files
ls -la books/<topic>/

# Should have:
#   - topic-index.json
#   - chunks.json
#   - faiss.index
```

**Force rebuild:**

```bash
python3.11 engine/scripts/index_library.py --topic "<topic>" --force
```

---

### Watch Library Not Detecting Changes

**Symptom:** File changes don't trigger reindex

**Check:**

1. `watch_library.py` running?
2. Changes inside `books/<topic>/`?
3. File extension is `.epub`, `.pdf`, `.txt`?

**Manual trigger:**

```bash
# Kill watch_library.py (Ctrl+C)
# Manually reindex
python3.11 engine/scripts/index_library.py --topic "<changed-topic>"
# Restart watch
python3.11 engine/scripts/watch_library.py
```

---

### Indexer Fails on EPUB

**Symptom:** "Failed to process <file.epub>"

**Possible causes:**

1. Corrupted EPUB
2. DRM-protected file
3. Missing Python dependencies

**Test file manually:**

```bash
python3.11 -c "
from ebooklib import epub
book = epub.read_epub('books/topic/file.epub')
for item in book.get_items():
    print(item)
"
```

**If file is DRM-protected:** Remove DRM first (Calibre + DeDRM plugin)

---

## Advanced Configuration

### Custom Embedding Model

Default: `sentence-transformers/all-MiniLM-L6-v2` (90MB, fast)

**Switch to better model:**

```python
# In mcp_server.py and index_library.py, change:
model = SentenceTransformer('all-mpnet-base-v2')  # 420MB, more accurate
```

See [embedding-models.md](embedding-models.md) for comparison.

---

### Partition Storage

**Current:** Per-topic indices (`books/<topic>/faiss.index`)wihch faile? why

**Why:** Delta detection, faster queries on single topics

**Trade-off:** Cross-topic search requires merging results

---

### FAISS Index Types

Current: `IndexFlatIP` (inner product, exact search)

**Alternatives:**

- `IndexIVFFlat`: Approximate search, faster on huge libraries (>100k chunks)
- `IndexHNSWFlat`: Graph-based, very fast queries

**When to switch:** If library grows >50k chunks per topic

---

## Migration

### v1.0 → v2.0 (Smart Indexing)

**Schema change:** `metadata.json` → `library-index.json`

**Migrate:**

```bash
python3.11 engine/scripts/migrate_to_v2.py
```

**Result:**

- Old: Single `metadata.json` + `books.pkl`
- New: `library-index.json` + per-topic `topic-index.json`

**Backwards compatible:** `mcp_server.py` has failsafe (tries v2, falls back to v1)

---

### Personal Library → Librarian (v1.0.0)

**Breaking changes:**

- MCP server name: `personal-library` → `librarian`
- Folder: `~/Documents/personal library` → `~/Documents/librarian`

**Update MCP config:**

```json
{
  "chat.mcp.servers": {
    "librarian": {
      // Changed from "personal-library"
      "command": "/opt/homebrew/bin/python3.11",
      "args": ["/Users/YOUR_USER/Documents/librarian/engine/scripts/mcp_server.py"]
    }
  }
}
```

**Update paths:** Search for `personal library` or `personal-library` in your configs

---

## Validation

### Pre-Commit Checks

Run before pushing to GitHub:

```bash
# All checks
cat MGMT/CHECKS.md

# Quick test
python3.11 engine/scripts/research.py "test query" --top-k 1
python3.11 engine/scripts/mcp_server.py  # Should start without errors (Ctrl+C to stop)
```

---

## Performance

### Indexing Speed

- **Small topic** (5 books): ~10 seconds
- **Medium topic** (20 books): ~45 seconds
- **Large topic** (100 books): ~5 minutes

**Bottleneck:** EPUB chunking + embedding generation

**Optimization:** Delta detection (only reindex changed topics)

---

### Query Speed

- **Single topic:** <100ms
- **All topics:** ~500ms (merges results from all topic indices)

**Tip:** Use `--topic` flag for faster queries when you know the topic

---

## Development

### Adding New Scripts

1. Add script to `engine/scripts/`
2. Update [CHECKS.md](CHECKS.md) with test
3. Add documentation to this file
4. Update [CHANGELOG.md](CHANGELOG.md)

---

### Debugging MCP Server

**Enable verbose logging:**

```python
# In mcp_server.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test queries manually:**

```bash
# Start server
python3.11 engine/scripts/mcp_server.py

# In another terminal:
python3.11 engine/scripts/research.py "your query" --top-k 5
```

---

## See Also

- [README.md](../../README.md) - Setup & basic usage
- [CHECKS.md](CHECKS.md) - Validation tests
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [ROADMAP.md](ROADMAP.md) - Future features
- [mcp-setup.md](mcp-setup.md) - MCP configuration
- [embedding-models.md](embedding-models.md) - Model comparison
