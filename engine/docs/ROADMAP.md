# Personal Library MCP - Roadmap

> 🤖
>
> - [CHANGELOG](CHANGELOG.md) - What we did
> - [ROADMAP](ROADMAP.md) - What we wanna do
> - [CONTRIBUTING](../../.github/CONTRIBUTING.md) - How we do it
> - [CHECKS](CHECKS.md) - What we accept
> - [/whatsup](../../.github/prompts/whatsup.prompt.md) - The prompt that keeps us sane
>
> 🤖

---

### v0.4

#### ⏳ Delta indexing

More optimized reindexing

- [ ] Define logic: how system knows there is a mismatch?
- [ ] once mismatch is detected, thats the delta
- [ ] update metadata (only delta)
- [ ] update FAISS index (only delta)
- [ ] redo FAILED as REPORT, more complete

---

### v0.5

#### ⏳ Indexing Quality & Reporting

Visibility into indexing health and automatic detection of problems

- [ ] Track timing metrics (total time, time per book, chunks per second)
- [ ] Generate `engine/docs/REPORT.md` after each indexing run
- [ ] **✅ Success section:** Topics indexed successfully with stats
- [ ] **⚠️ Alert section:** Suspicious chunking (health check failures)
- [ ] **❌ Error section:** Books that failed to index
- [ ] Calculate expected chunks from filesize (EPUB: ~1 chunk/1KB, PDF: ~1 chunk/1.5KB)
- [ ] Flag topics with suspiciously low chunk counts
- [ ] Add `--validate` flag to `reindex_topic.py`
- [ ] Track chunks/MB ratio per topic
- [ ] Store metrics in metadata.json

**Current issue:** Only ~0.7 chunks/book (137 chunks from 197 books). Expected: 100+ chunks/book.

---

### v0.6

#### ⏳ Provider Integration

Make Personal Library MCP work with any AI provider

- [x] Created `scripts/mcp_server.py` (provider-agnostic)
- [x] Lazy-loading architecture (instant startup)
- [x] Terminal client working
- [x] VS Code integration (MCP + /research prompt)
- [x] Auto-rebuild on missing indices
- [x] Consolidated storage (books/ only)
- [ ] Claude Desktop config example
- [ ] OpenAI function calling wrapper
- [ ] LM Studio integration guide
- [ ] OpenWebUI custom tool
- [ ] Provider comparison benchmarks

---

### v0.2

#### ✅ VS Code Extension Configuration

Some last mile configurations for a tighter feedback loop

- [ ] rethink what an extension can do and if we even need it

---

### v0.7

#### ⏳ Direct mentions

A way for vscode AI tab to autocomplete list existing topics and books for more precise queries. how to surface metadata as autocomplete

- [ ] discuss possibility. extension?
- [ ] examples to copy?
- [ ] **# autocomplete for topics**
  - Example: User types `/research in #cyber` → suggests `#cybersecurity_applied`, `#cybersecurity_history`, `#cybersecurity_strategy`
  - Reads from `books/metadata.json` → topic IDs and labels
  - Filters as user types
- [ ] **# autocomplete for books**
  - Example: User types `/research in #Molecular` → suggests `#Molecular Red` from anthropocene topic
  - Shows book title + topic context in dropdown
  - Autocomplete shows: `#Molecular Red (anthropocene)`
- [ ] **Folder/subfolder awareness**
  - Support nested references: `#cybersecurity/applied` or just `#applied` if unambiguous
  - Show parent topic in autocomplete UI
- [ ] **Integration with /research prompt**
  - Parse `#` references before sending to MCP
  - Convert to proper topic/book filters
  - Example: `/research in #cybersecurity_applied what is SQL injection?`
- [ ] **Extension configuration**
  - Setting: `personalLibrary.enableAutocomplete` (default: true)
  - Setting: `personalLibrary.metadataPath` (auto-detected from workspace)
  - Refresh metadata on file change (watch `books/metadata.json`)

---

### v0.8

#### ⏳ Folder detection

Auto-detection of books folder for delta reindexing

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

### Future Ideas

#### 💡 Enhancements for later versions

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

**Meta Development Workflow:**

- [ ] **Implement epic-per-branch workflow**
  - [ ] Enforce: Each ROADMAP epic = dedicated feature branch
  - [ ] Branch naming: `v{major}.{minor}-{epic-name}` (e.g., `v0.3-delta-indexing`)
  - [ ] Workflow: Regular rebase from `main` to stay current
  - [ ] Completion criteria: Merge to `main` = move ROADMAP section → CHANGELOG
  - [ ] Add git hooks or CI checks to validate workflow compliance
  - [ ] Update whatsup.prompt.md to handle feature branch workflow
  - [ ] Document branch-based development in contributing guide
  - **Note:** Current workflow is direct commits to `main` (works for now)

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
