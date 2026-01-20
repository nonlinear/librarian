# Personal Library MCP - Roadmap

## Version Control Strategy

**Each roadmap version = one feature branch:**

- Branch naming: `v{major}.{minor}-{feature-name}` (ex: `v0.3-delta-indexing`)
- Regular rebase from `main` to stay current
- When complete → merge to `main` → move to CHANGELOG.md
- CHANGELOG specifies: **What's new** + **Who needs to know**

**Semantic Versioning (for AI):**

- **Patch (v0.2.0 → v0.2.1):** Bug fixes only, no breaking changes, no reindexing
- **Minor (v0.2.x → v0.3.0):** New features, backward compatible, optional reindexing
- **Major (v0.x → v1.0):** Breaking changes, **requires full reindexing**, migration guide required

**When feature completes:**

1. Check ROADMAP.md current version section
2. Mark checkboxes [x] for completed items
3. If ALL checkboxes complete → move entire section to CHANGELOG.md
4. Add "Impact:" and "Migration:" sections to CHANGELOG entry
5. Update version number in commit

---

## v0.3: Delta Indexing 🔶 (IN PROGRESS)

**Branch:** `v0.3-delta-indexing` (when started)

**Target audience:** Users with large libraries who reindex frequently

**Goal:** Update only changed books instead of reindexing everything

**Status:** Infrastructure complete, automation pending

**✅ Done:**

- [x] Topic-partitioned storage (can reindex individual topics)
- [x] Metadata tracking (books/ → metadata.json)
- [x] Manual topic reindexing capability
- [x] Nested folder support (topics/subtopics with underscore flattening)
  - [x] `generate_metadata.py` - recursive folder scanning
  - [x] `reindex_topic.py` - nested path resolution
  - [x] `research.py` - underscore topic ID support
  - [x] Documentation updated (README.md with mermaid diagram)

**❌ Pending:**

- [ ] `scripts/update_delta.py` - automated change detection
  - [ ] Compare `books/` filesystem vs `metadata.json`
  - [ ] Identify deltas (added/removed/modified books)
  - [ ] Auto-reindex only affected topic directories
  - [ ] Incremental metadata.json updates
- [ ] CLI command: `python3.11 scripts/update_delta.py`
- [ ] Performance benchmarks (delta vs full reindex)

**Granular Indexing Quality Epic:**

- [ ] **Indexing report system** (replace FAILED.md with comprehensive REPORT)
  - [ ] Generate `engine/docs/REPORT.md` after each indexing run
  - [ ] **✅ Success section:** Topics indexed successfully with stats
    - Example: `✅ AI: 1224 chunks from 8 books (153 chunks/book avg)`
  - [ ] **⚠️ Alert section:** Suspicious chunking (health check failures)
    - Example: `⚠️ product_architecture: 5 chunks from 5MB (expected ~5000)`
    - Suggest re-index with `--force` flag
  - [ ] **❌ Error section:** Books that failed to index (current FAILED.md content)
    - Corrupted files, unsupported formats, parsing errors
  - [ ] Timestamp and indexer version in report header
  - [ ] Link from README → REPORT for visibility
- [ ] **Chunk health checks** (validate chunks proportional to filesize)
  - [ ] Calculate expected chunks from filesize
    - EPUB: ~1 chunk per 1KB (avg, based on 1024 char chunks)
    - PDF: ~1 chunk per 1.5KB (denser text)
  - [ ] Flag topics with suspiciously low chunk counts
  - [ ] Auto-detect indexing failures during reindex
  - [ ] Add `--validate` flag to `reindex_topic.py`
  - [ ] Report: `⚠️  Topic 'product_architecture': 5 chunks from 5MB (expected ~5000)`
  - [ ] Suggest: `Run: python3.11 scripts/reindex_topic.py product_architecture --force`
- [ ] **Chunk quality metrics**
  - [ ] Track chunks/MB ratio per topic
  - [ ] Detect outliers (too many/few chunks)
  - [ ] Store metrics in metadata.json
  - [ ] Dashboard/report of index health

**Current workaround:** Manual full reindex (`python3.11 scripts/indexer.py`)

---

## v0.4: Provider Integration 🔶 (IN PROGRESS)

**Branch:** `v0.4-provider-integration` (when started)

**Target audience:** Users of Claude Desktop, OpenAI, LM Studio, OpenWebUI

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
- [v0.5: Automation & Advanced Features ❌ (PLANNED)

**Branch:** `v0.5-automation` (when started)

**Target audience:** Power users who add books frequently

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

> 🤖: See [ROADMAP](engine/docs/ROADMAP.md) for planned features & in-progress work
> 🤖: See [CHANGELOG](engine/docs/CHANGELOG.md) for ersion history & completed features
> 🤖: See [CHECKS](engine/docs/CHECKS.md) for stability requirements & testing
> 👷: Consider using [/whatsup prompt](https://github.com/nonlinear/nonlinear.github.io/blob/main/.github/prompts/whatsup.prompt.md) for updates
