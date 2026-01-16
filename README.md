# Personal Library MCP

> A BYOB (Bring Your Own Books) local MCP so you can consult your library as you build your projects.

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

## Installation

### Prerequisites

Before installation, you need:

1. Python 3.11 or higher

- macOS`brew install python@3.11`
- Ubuntu/Debian `sudo apt install python3.11`
- Windows [Download from python.org](https://www.python.org/downloads/)
- Verify: `python3.11 --version`

### Setup

1. Run setup script: `bash ./scripts/setup.sh`
   - Installs Python dependencies
   - Downloads local embedding model (all-MiniLM-L6-v2, ~90MB)
   - Model saved in `models/` directory (not tracked by git)

## Usage

1. Add your books to `books/TOPICNAME/*.epub`
2. Generate metadata: `bash python3.11 scripts/generate_metadata.py`
3. Build index (includes auto-partitioning): `bash python3.11 scripts/indexer.py`
   - Creates vector store in `storage/`
   - Auto-partitions by topic for MCP lazy-loading
   - ~90MB for 34 books (local embeddings)
4. Example query: `bash python3.11 scripts/query_partitioned.py "what books discuss AI ethics?" --topic ai`

### VS Code Extension

1. Install the Personal Library MCP extension
   - `bash code --install-extension https://github.com/nonlinear/personal-library/raw/main/.vscode/extensions/personal-library-mcp/personal-library-mcp-latest.vsix`
   - or [Download .vsix](https://github.com/nonlinear/personal-library/raw/main/.vscode/extensions/personal-library-mcp/personal-library-mcp-latest.vsix)

---

---

---

## Project progress roadmap

> 🤖🚨 FOR AI: Always check this section before starting any update on project. It tracks what's done and what's next.

### Foundation ✅ (COMPLETE)

- [x] `metadata.json` generation (`scripts/generate_metadata.py`)
- [x] LlamaIndex vector store setup
- [x] Local embedding model (sentence-transformers/all-MiniLM-L6-v2, 384-dim)
  - [x] Model cached in `models/` (90MB, not tracked by git)
  - [x] Zero API keys required
  - [x] Fully offline operation
- [x] CLI query tool (`scripts/query_partitioned.py`)
- [x] MCP server with 3 tools (query_library, list_topics, list_books)
- [x] Metadata-first query routing
- [x] Topic-partitioned storage (FAISS + pickle per topic)
- [x] Auto-partitioning integrated in `indexer.py`

### Phase 1: Database Optimization ✅ (COMPLETE)

**Problem**: `storage/docstore.json` (17MB) causes 30s MCP startup delay + Gemini API dependency

**Solution Implemented: Topic-Based Lazy Loading + Local Embeddings** 🎉

- [x] **Migrated to local embeddings** (Jan 15, 2026)
  - [x] Replaced Gemini (768-dim) → sentence-transformers (384-dim)
  - [x] Model stored in `models/` (90MB, gitignored)
  - [x] Zero API keys required - fully offline
  - [x] Updated: `indexer.py`, `query_partitioned.py`, `setup.sh`
  - [x] Removed: `.env` requirement, API key docs
- [x] Created `scripts/partition_storage.py`
- [x] **Integrated auto-partitioning in `indexer.py`** (no manual step)
- [x] Split storage into 12 topic-specific directories (automated)
- [x] Created `scripts/mcp_server_lazy.py`
  - [x] Loads ONLY `metadata.json` (19KB) on startup → **instant** (<100ms)
  - [x] Lazy-loads topics on first query (~2s per topic)
  - [x] Topic caching prevents reload
- [x] Binary format (pickle) for faster deserialization

### Phase 2: Delta Indexing 🔶 (PARTIAL)

**Infrastructure Complete, Automation Pending**

**✅ Done:**

- [x] Topic-partitioned storage (can reindex individual topics)
- [x] Metadata tracking (books/ → metadata.json)
- [x] Manual topic reindexing capability

**❌ Pending:**

- [ ] `scripts/update_delta.py` - automated change detection
  - [ ] Compare `books/` filesystem vs `metadata.json`
  - [ ] Identify deltas (added/removed/modified books)
  - [ ] Auto-reindex only affected topic directories
  - [ ] Incremental metadata.json updates
- [ ] CLI command: `python3.11 scripts/update_delta.py`
- [ ] Performance benchmarks (delta vs full reindex)

**Current workaround**: Manual full reindex (`python3.11 scripts/indexer.py`)

### Phase 3: MCP Integration 🔶 (PARTIAL)

**Server Complete, VS Code Testing Pending**

**✅ Done:**

- [x] Created `scripts/mcp_server_lazy.py`
- [x] Lazy-loading architecture (instant startup)
- [x] Re-enabled MCP in `~/Library/Application Support/Code/User/mcp.json`
- [x] Document troubleshooting in TROUBLESHOOTING.md

**❌ Pending:**

- [ ] Test `/research` end-to-end in VS Code
- [ ] Measure actual MCP startup time in production
- [ ] Validate no "Starting MCP servers... Skip?" dialog
- [ ] User acceptance testing

### Phase 4: Extension & Automation ❌ (NOT STARTED)

**Goal**: Seamless VS Code integration with automatic updates

**❌ All Pending:**

- [ ] **Embed `/research` prompt in VS Code extension**
  - [ ] Command palette entry: "Personal Library: Research"
  - [ ] Keyboard shortcut (e.g., Cmd+Shift+L)
  - [ ] Context menu integration
- [ ] **Filesystem watcher (`watchdog`)**
  - [ ] Monitor `books/` for file changes
  - [ ] Auto-regenerate `metadata.json`
  - [ ] Auto-reindex affected topics (uses Phase 2 delta logic)
  - [ ] Background indexing with progress indicator
  - [ ] Debounce mechanism
- [ ] **PDF support**
  - [ ] PDF text extraction (PyPDF2/pdfplumber)
  - [ ] PDF embedding pipeline
  - [ ] Update metadata schema
  - [ ] Test mixed EPUB/PDF libraries

### Future Enhancements

**Local Embedding Models** ✅ (COMPLETE):

- [x] Sentence Transformers (`all-MiniLM-L6-v2`)
  - Pros: Free, fast, offline, 384-dim
  - Model cached in `models/` (90MB)
- [ ] Test BGE embeddings (e.g., `BAAI/bge-small-en-v1.5`)
  - Pros: Better quality, still local, 384-dim
  - Cons: Larger model size
- [ ] Make embedding model swappable (config-based)

**Other Enhancements**:

- [ ] PDF support (currently EPUB only)
- [ ] Image extraction and indexing from books
- [ ] Response caching for repeated queries
- [ ] Clarification prompts when query is ambiguous
- [ ] Threading/multiprocessing for faster indexing
- [ ] Terminal client (standalone, non-MCP)
- [ ] API documentation
- [ ] Performance benchmarks documentation
