# Metadata Schema v2.0

**Purpose:** Modularize metadata from monolithic to per-topic for portability, resilience, and git-friendliness

**Version:** 2.0
**Previous:** 1.0 (monolithic metadata.json)

---

## Architecture

### Current (v1.0 - Monolithic)

```
books/
  metadata.json          ← 6000+ lines, all 54 topics, all 430 books
  cooking/
    faiss.index
    chunks.json
```

**Problems:**

- ❌ Not portable (absolute paths, single-library coupling)
- ❌ Not resilient (corruption = entire library down)
- ❌ Git-unfriendly (6000-line diffs)
- ❌ Slow operations (parse 6000 lines to read 1 topic)

### New (v2.0 - Modular)

```
books/
  metadata.json          ← Registry only (~100 lines: topic list + global config)
  cooking/
    .metadata.json       ← Topic metadata (~20 lines: 1 book)
    faiss.index
    chunks.json
  AI/policy/
    .metadata.json       ← Topic metadata (~50 lines: 4 books)
    faiss.index
    chunks.json
```

**Benefits:**

- ✅ Portable (copy topic folder = copy everything)
- ✅ Resilient (corrupted topic ≠ dead library)
- ✅ Git-friendly (small, focused diffs)
- ✅ Fast operations (parse 20 lines, not 6000)

---

## Schema

### Main Registry (`books/metadata.json`)

```json
{
  "schema_version": "2.0",
  "library_path": "/absolute/path/to/books",
  "embedding_model": "all-MiniLM-L6-v2",
  "chunk_settings": {
    "size": 1024,
    "overlap": 200
  },
  "topics": [
    {
      "id": "cooking",
      "path": "cooking"
    },
    {
      "id": "ai_policy",
      "path": "AI/policy"
    }
  ]
}
```

**Fields:**

- `schema_version`: Metadata schema version (`"2.0"`)
- `library_path`: Absolute path to books directory (for absolute path resolution)
- `embedding_model`: Model used for all topics (must match for cross-topic queries)
- `chunk_settings`: Default chunking configuration
- `topics`: List of topic registrations
  - `id`: Slugified topic identifier (unique)
  - `path`: Relative path from `books/` directory

**Purpose:** Lightweight registry that points to topic metadata locations

---

### Per-Topic Metadata (`books/<topic>/.metadata.json`)

```json
{
  "schema_version": "2.0",
  "topic_id": "cooking",
  "embedding_model": "all-MiniLM-L6-v2",
  "chunk_settings": {
    "size": 1024,
    "overlap": 200
  },
  "last_indexed_at": 1737849600.0,
  "content_hash": "abc123def456...",
  "books": [
    {
      "id": "bread_handbook_pdf",
      "title": "Bread Handbook PDF",
      "author": "Unknown",
      "year": null,
      "tags": ["baking", "bread"],
      "filename": "Bread Handbook PDF.pdf",
      "filetype": "pdf",
      "last_modified": 1737849500.0
    }
  ]
}
```

**Fields:**

- `schema_version`: Metadata schema version (`"2.0"`)
- `topic_id`: Slugified topic identifier (matches registry)
- `embedding_model`: Model used for this topic's index
- `chunk_settings`: Chunking config for this topic
- `last_indexed_at`: Unix timestamp of last successful index
- `content_hash`: Hash of folder contents (for delta detection)
- `books`: Array of book metadata
  - `id`: Slugified book identifier (unique within topic)
  - `title`: Human-readable book title
  - `author`: Book author(s)
  - `year`: Publication year (nullable)
  - `tags`: Array of topic tags
  - `filename`: Book filename (portable, no paths)
  - `filetype`: File format (`"pdf"` or `"epub"`)
  - `last_modified`: Unix timestamp of file mtime

**Purpose:** Self-contained topic metadata for portable, sandboxed indexing

---

## Topic XOR Rule

**Critical constraint:** A topic folder contains **EITHER** books **OR** subtopics, **NEVER both**.

### Valid Examples

✅ **Leaf topic (books only):**

```
books/cooking/
  .metadata.json       ← Has books[]
  Bread Handbook.pdf
  faiss.index
  chunks.json
```

✅ **Parent topic (subtopics only):**

```
books/management/
  activism/
    .metadata.json     ← Has books[]
  commons/
    .metadata.json     ← Has books[]
  ideation/
    .metadata.json     ← Has books[]
  product/
    .metadata.json     ← Has books[]
```

❌ **Invalid (mixed):**

```
books/design/
  .metadata.json       ← Has books[]? ERROR!
  Some Book.pdf        ← Book in parent? ERROR!
  typography/          ← Subtopic? ERROR!
    .metadata.json
```

**Rationale:** Simplifies discovery, prevents ambiguity, enforces clean hierarchy

---

## Migration Strategy

### Phase 1: Create Per-Topic Metadata

```python
# For each topic in monolithic metadata.json:
1. Read topic metadata from monolithic file
2. Create topic folder if needed
3. Write .metadata.json to topic folder
4. Validate: topic has books OR parent has subtopics (XOR)
```

### Phase 2: Update Main Registry

```python
# Simplify metadata.json to registry:
1. Keep: schema_version, library_path, embedding_model, chunk_settings
2. Keep: topics[] (but only id + path, remove books)
3. Remove: All book-level data (now in per-topic files)
```

### Phase 3: Update Indexer

```python
# indexer.py changes:
1. Read registry (books/metadata.json)
2. For each topic in registry:
   a. Read topic metadata (books/<topic>/.metadata.json)
   b. Load books from topic folder
   c. Build index, save to topic folder
   d. Update topic .metadata.json with last_indexed_at
```

### Phase 4: Update MCP Server

```python
# mcp_server.py changes:
1. Auto-discover topics via registry
2. Lazy-load per-topic metadata on demand
3. Cache topic metadata (small files = fast)
```

---

## Content Hash Algorithm

**Purpose:** Detect topic changes for delta indexing

```python
import hashlib
import os

def compute_content_hash(topic_path):
    """Hash folder contents: filenames + mtimes"""
    files = sorted([
        f for f in os.listdir(topic_path)
        if f.endswith(('.pdf', '.epub'))
    ])

    hash_input = []
    for filename in files:
        filepath = topic_path / filename
        mtime = os.path.getmtime(filepath)
        hash_input.append(f"{filename}:{mtime}")

    combined = '|'.join(hash_input)
    return hashlib.sha256(combined.encode()).hexdigest()
```

**Logic:**

- Changed file (mtime) → hash changes → reindex topic
- New file (filename) → hash changes → reindex topic
- Deleted file (missing filename) → hash changes → reindex topic
- Unchanged → hash matches → skip topic

---

## Backward Compatibility

**v1.0 → v2.0:** No compatibility (migration required)

**Rationale:**

- Schema change too significant for gradual migration
- Monolithic metadata.json fundamentally incompatible with modular approach
- Clean break enables simpler code (no version branching)

**Migration path:**

1. Backup existing `metadata.json`
2. Run migration script (creates per-topic `.metadata.json`)
3. Update main `metadata.json` to registry format
4. Reindex all topics with new indexer.py
5. Validate: all topics queryable, failed topics documented

---

> 🤖: Part of Epic v0.5.0 Smart Indexing
> 🤖: See [v0.5.0 epic notes](../gaps/epic-notes/v0.5.0.md) for implementation details
> 🤖: See [chunks-v2.0.md](chunks-v2.0.md) for chunk schema changes
