# Personal Library MCP

> A BYOB (Bring Your Own Books) local MCP so you can consult your library as you build your projects.

---

## 🚨 FOR AI AGENTS: Always check the Roadmap section before starting any work. It tracks what's done and what's next.

---

## Core Principles

**Every millisecond matters.**

This system is a **semantic orientation tool**, not a conversational assistant.

- **Map ≠ Territory**: Uses a single metadata file for navigation, not content replication
- **Explicit invocation only**: No automatic exploration or unsolicited responses
- **Delta indexing**: Only reindexes what changed
- **Client-agnostic backend**: VS Code is just one possible interface

---

## Architecture

### Vault Structure

```
books/
├── topic_a/
│   ├── book1.epub
│   └── book2.pdf
├── topic_b/
│   └── book3.epub
```

**Rules:**

- Exactly 1 folder level below `books/`
- Each folder = 1 topic
- Only EPUBs and PDFs inside

## The Map: `metadata.json`

**Purpose:** Minimal abstraction for rapid AI decision-making.

**Not:**

- A content copy
- A search index
- A documentation system

**Design decisions:**

- Tags exist only on books (semantic signal)
- Topics have: name + short description
- No text duplication
- Every field serves navigation

---

```mermaid
graph TD
    QUERY([research prompt+<br>specific book query]) --> MAP[Read metadata.json]
    MAP --> SIM[Semantic Similarity]

    SIM --> T1[Topic: philosophy<br/>Score: 0.89]
    SIM --> T2[Topic: AI<br/>Score: 0.32]

    T1 --> B1[Book: Psychopolitics<br/>Tags: power, discipline<br/>Score: 0.91]

    B1 --> DECISION1{Confident match?}
    T2 --> DECISION2{Confident match?}

    DECISION1 -->|Yes| VEC[Query Vector Store<br/>Scope: philosophy/Psychopolitics]
    DECISION2 -->|No| ASK[System asks for clarification]

    ASK --> CLARIFY[Clarification query]
    CLARIFY --> MAP

    VEC --> ANSWER([Precise answer from<br>relevant book chunks])
```

**Rule:** Never reindex everything. Only delta changes.

## Query Flow Principles

**Steps:**

1. User asks a question
2. AI reads **only** `metadata.json`
3. AI calculates semantic similarity (query ↔ topics/tags)
4. AI selects best topic + books
5. **Only then** does vector store query execute
6. If unclear → request clarification

**Never:**

- Explore the vault without direction
- Load large contexts speculatively
- Attempt "smart" auto-discovery
- Make guesses when uncertain

---

## File Watching & Indexing

**Trigger:** Book added/removed from vault

**Process:**

1. `watchdog` detects filesystem change
2. Extract delta (new/removed files only)
3. Update embeddings (incremental)
4. Update `metadata.json`
5. Persist to LlamaIndex storage

**No full reindexing unless explicitly requested.**

---

## Quick Start

### Prerequisites

Before installation, you need:

1. Python 3.11 or higher

- macOS`brew install python@3.11`
- Ubuntu/Debian `sudo apt install python3.11`
- Windows [Download from python.org](https://www.python.org/downloads/)
- Verify: `python3.11 --version`

## Setup

3. Rename `.env-template` as `.env`
4. [Get Google Gemini API Key](https://aistudio.google.com/app/apikey)
5. Add your key to `.env`
   - ⚠️ Maske sure `.env` is in `.gitignore`
6. Run setup script: `bash ./scripts/setup.sh` (installs all Python dependencies automatically)

**Manual setup (if needed):**

```bash
python3.11 -m pip install -r requirements.txt
```

## Usage

1. Add your books

- `books/TOPICNAME/(epub files)

2. Generate metadata: `bash python3.11 scripts/generate_metadata.py`
3. Build index: `bash python3.11 scripts/indexer.py` (soon: folder watch)

- Creates vector store in `storage/` (~92MB for 25 books)

4. Test query your library: `bash python3.11 scripts/query.py "what books discuss AI ethics?"`

## What This System Is Not

- ❌ Not a chat interface
- ❌ Not cloud-dependent
- ❌ Not a general-purpose MCP
- ❌ Not trying to be "smart" beyond navigation

**It is:**

- ✅ A navigation layer for your books
- ✅ A semantic index with minimal latency
- ✅ A local-first, privacy-preserving tool

## Roadmap

### Foundation (Completed)

- [x] `metadata.json` generation (`scripts/generate_metadata.py`)
- [x] LlamaIndex vector store setup
- [x] Gemini embedding pipeline (768-dim, embedding-001)
- [x] CLI query tool (`scripts/query.py`)
- [x] MCP server with 3 tools (query_library, list_topics, list_books)
- [x] Metadata-first query routing
- [x] FAISS index (75KB) + docstore.json (17MB) architecture

### Phase 1: Database Optimization ✅ (COMPLETE)

**Problem**: `storage/docstore.json` (17MB) causes 30s MCP startup delay

**Solution Implemented: Topic-Based Lazy Loading** 🎉

- [x] Created `scripts/partition_storage.py`
- [x] Split storage into 12 topic-specific directories:
  - [x] `storage/ai/` (12KB FAISS + 1.42MB chunks)
  - [x] `storage/activism/` (6KB FAISS + 1.97MB chunks)
  - [x] `storage/anthropocene/` (15KB FAISS + 3.05MB chunks)
  - [x] `storage/fiction/` (9KB FAISS + 2.93MB chunks)
  - [x] `storage/oracles/` (21KB FAISS + 4.90MB chunks)
  - [x] `storage/urbanism/` (3KB FAISS + 1.13MB chunks)
  - [x] `storage/usability/` (9KB FAISS + 1.24MB chunks)
  - [x] 5 empty topics (not yet indexed)
- [x] Created `scripts/mcp_server_lazy.py`
  - [x] Loads ONLY `metadata.json` (19KB) on startup → **instant** (<100ms)
  - [x] Lazy-loads topics on first query (~2s per topic)
  - [x] Topic caching prevents reload
  - [x] Topic inference from query/book/explicit param
- [x] Re-enabled MCP in VS Code config
- [x] Binary format (pickle) for faster deserialization

**Performance**:

- Startup: **30s → <100ms** (300x improvement)
- First query per topic: ~2s (lazy load)
- Subsequent queries: instant (cached)

**Abandoned Approaches**:

- ❌ Background loading (worked in terminal, failed in MCP stdio)
- ❌ Full FAISS reindex (wasteful, cancelled)
- ❌ Monolithic pickle conversion (only 2% size reduction)

### Phase 2: Incremental Updates (Delta Indexing) ⭐ (NEXT)

**Current**: Full reindexing on every change (slow, wasteful)

- [ ] Rewrite `scripts/update_delta.py` for partitioned storage
  - [ ] Compare current `books/` structure with `metadata.json`
  - [ ] Identify deltas (added/removed/modified books)
  - [ ] Update only affected topic directories
  - [ ] Regenerate topic's FAISS index + chunks.pkl
  - [ ] Update `metadata.json` incrementally
- [ ] Update `scripts/query.py` CLI tool for partitioned storage
- [ ] Test delta update vs full reindex performance

**Future Automation:**

- [ ] Integrate `watchdog` library for filesystem monitoring
- [ ] Auto-trigger `update_delta.py` on file changes
- [ ] Real-time index updates (no manual intervention)

### Phase 3: MCP Performance & Integration

**Current state**: MCP re-enabled with lazy loading server ✅

- [x] Created `scripts/mcp_server_lazy.py`
- [x] Re-enabled MCP in `~/Library/Application Support/Code/User/mcp.json`
- [ ] Test `/research` end-to-end in VS Code (pending reload)
- [ ] Measure actual MCP startup time in VS Code
- [ ] Validate no "Starting MCP servers... Skip?" dialog
- [x] Document troubleshooting in TROUBLESHOOTING.md

**Pending validation**:

- User needs to reload VS Code (Cmd+R) to test

### Future Enhancements

**Local Embedding Models** (Privacy + Speed):

- [ ] Test Sentence Transformers (e.g., `all-MiniLM-L6-v2`)
  - Pros: Free, fast, offline, 384-dim
  - Cons: Lower quality than Gemini
- [ ] Test BGE embeddings (e.g., `BAAI/bge-small-en-v1.5`)
  - Pros: Better quality, still local, 384-dim
  - Cons: Larger model size
- [ ] Make embedding model swappable (config-based)
- [ ] Compare local vs Gemini quality on test queries

**Other Enhancements**:

- [ ] PDF support (currently EPUB only)
- [ ] Image extraction and indexing from books
- [ ] Response caching for repeated queries
- [ ] Clarification prompts when query is ambiguous
- [ ] Threading/multiprocessing for faster indexing
- [ ] Terminal client (standalone, non-MCP)
- [ ] API documentation
- [ ] Performance benchmarks documentation
