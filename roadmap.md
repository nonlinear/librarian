# Personal Library MCP - Roadmap

> 🤖🚨 FOR AI: Always check this before starting work. Shows what's planned and in progress.

**See also:** [Release Notes](release-notes.md) for completed features.

---

## Phase 2: Delta Indexing 🔶 (IN PROGRESS)

**Goal:** Update only changed books instead of reindexing everything

**Status:** Infrastructure complete, automation pending

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

**Current workaround:** Manual full reindex (`python3.11 scripts/indexer.py`)

---

## Phase 3: Provider Integration 🔶 (IN PROGRESS)

**Goal:** Make Personal Library MCP work with any AI provider

**Status:** Core MCP complete, community integrations pending

**✅ Done:**

- [x] Created `scripts/mcp_server_lazy.py` (provider-agnostic)
- [x] Lazy-loading architecture (instant startup)
- [x] Terminal client working
- [x] VS Code integration (MCP + /research prompt)
- [x] Auto-rebuild on missing indices
- [x] Consolidated storage (books/ only)

**🤝 Community Contributions Needed:**

- [ ] Claude Desktop config example
- [ ] OpenAI function calling wrapper
- [ ] LM Studio integration guide
- [ ] OpenWebUI custom tool
- [ ] Provider comparison benchmarks
- [ ] Integration testing across providers

---

## Phase 4: Automation & Advanced Features ❌ (PLANNED)

**Goal:** Zero-friction daily usage across all providers

**Status:** Not started

**❌ All Pending:**

- [ ] **Filesystem watcher (`watchdog`)**
  - [ ] Monitor `books/` for file changes
  - [ ] Auto-regenerate `metadata.json`
  - [ ] Auto-reindex affected topics (uses Phase 2 delta logic)
  - [ ] Background indexing with progress indicator
  - [ ] Debounce mechanism
- [x] **PDF support** ✅ (Jan 18, 2026)
  - [x] PDF text extraction (PyMuPDF/fitz)
  - [x] PDF embedding pipeline (PyMuPDFReader)
  - [x] Update metadata schema
  - [x] Test mixed EPUB/PDF libraries (computer vision: 4 PDFs, 2 EPUBs)
  - ⚠️ MuPDF ICC profile warnings (cosmetic, don't affect indexing)

---

## Future Enhancements

**Ideas for later versions**

**Local Embedding Models:**

- [x] Sentence Transformers (`all-MiniLM-L6-v2`) ✅ ACTIVE
  - Pros: Free, fast, offline, 384-dim
  - Model cached in `models/` (90MB)
  - Stable, no crashes
- [x] Tested `all-mpnet-base-v2` (Jan 18, 2026) ❌ ABANDONED
  - Pros: Better semantic quality (768-dim)
  - Cons: Crashes during reindexing on M3 Mac, 2x slower
  - Decision: Reverted to MiniLM for stability
- [ ] Test BGE embeddings (e.g., `BAAI/bge-small-en-v1.5`)
  - Pros: Better quality, still local, 384-dim
  - Cons: Larger model size
- [ ] Make embedding model swappable (config-based)

**Other Enhancements:**

- [ ] **Clean up folder structure**
  - [ ] Reorganize into 2 top-level folders: `books/` and one for everything else
  - [ ] Update all scripts to handle new structure
  - [ ] Test indexer, metadata generation, MCP server
  - [ ] Update documentation with new structure
  - [ ] Requires careful testing - breaking change
- [ ] PDF support (currently EPUB only)
- [ ] Image extraction and indexing from books
- [ ] Response caching for repeated queries
- [ ] Clarification prompts when query is ambiguous
- [ ] Threading/multiprocessing for faster indexing
- [ ] Terminal client (standalone, non-MCP)
- [ ] API documentation
- [ ] Performance benchmarks documentation
- [ ] **Deep linking to search results** ([concept](https://nonlinear.nyc/ideas/search-path))
  - [ ] Research EPUB/PDF viewers with URI scheme support
  - [ ] Provider-specific citation formats (VS Code pills, terminal hyperlinks, etc.)
  - [ ] Format: `viewer://file=path&search=query`
  - [ ] One-click navigation from citations to exact location in book
  - [ ] Integration with MCP response format

---

**See also:** [Release Notes](release-notes.md) for completed features.
