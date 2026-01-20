# Personal Library MCP - Roadmap

**📋 Status Files Navigation**

> **Methodology files** (how we work):
>
> - 🤖 [CONTRIBUTING](../../.github/CONTRIBUTING.md) - Git workflow & branch strategy
> - 🤖 [whatsup.prompt.md](../../.github/prompts/whatsup.prompt.md) - Pre-commit workflow
>
> **Project status files** (what we're building):
>
> - 🤖 **ROADMAP** (you are here) - Planned features & in-progress work
> - 🤖 [CHANGELOG](CHANGELOG.md) - Version history & completed features
> - 🤖 [CHECKS](CHECKS.md) - Stability requirements & testing
>
> **File locations:**
>
> - Methodology: `.github/` (shareable across projects)
> - Project status: `engine/docs/` (project-specific)

---

## Epic Development Strategy

> 🤖 **Full workflow details:** See [.github/CONTRIBUTING.md](../../.github/CONTRIBUTING.md)

**Each epic = one feature branch:**

- Branch naming: `v{major}.{minor}-{feature-name}` (ex: `v0.3-delta-indexing`)
- Regular rebase from `main` to stay current
- When complete → merge to `main` → move to CHANGELOG.md
- CHANGELOG specifies: **What's new** + **Who needs to know**

**Semantic Versioning (for AI):**

- **Patch (v0.2.0 → v0.2.1):** Bug fixes only, no breaking changes, no reindexing
- **Minor (v0.2.x → v0.3.0):** New features, backward compatible, optional reindexing
- **Major (v0.x → v1.0):** Breaking changes, **requires full reindexing**, migration guide required

**When epic completes:**

1. Check ROADMAP.md current epic section
2. Mark checkboxes [x] for completed items
3. If ALL checkboxes complete → move entire section to CHANGELOG.md
4. Add "Impact:" and "Migration:" sections to CHANGELOG entry
5. Update version number in commit

---

## Epic v0.3: Delta Indexing 🔶 (IN PROGRESS)

**Branch:** `v0.3-delta-indexing` ✅ **Active**

**Target audience:** Developers building epic-based workflows for AI-assisted projects

**Goal:** Establish workflow infrastructure for epic-based development

**Status:** Meta-workflow complete, delta indexing automation pending

**✅ Done (Jan 20, 2026):**

- [x] **Meta Development Workflow**
  - [x] Created [CONTRIBUTING.md](../../.github/CONTRIBUTING.md) - Git workflow & branch strategy
  - [x] Defined branch-per-epic policy (`v{major}.{minor}-{epic-name}`)
  - [x] Documented rebase-only workflow (from `main`)
  - [x] Established merge workflow (whatsup → merge → tag → delete branch → announce)
  - [x] Branch deletion policy (recommended after merge, history preserved via tags)
  - [x] Semantic versioning guidelines for AI projects

- [x] **Status Files Navigation System**
  - [x] Standardized navigation across all status files
  - [x] Methodology files (`.github/`) - shareable across projects
  - [x] Project status (`engine/docs/`) - project-specific
  - [x] Consistent blockquote format with bullets
  - [x] Removed duplicate navigation from footers

**❌ Pending (Original Delta Indexing Scope):**

- [ ] **Diagnostic tool for topic health checks** (based on `test_chunking.py`)
  - [x] Created `scripts/test_chunking.py` - single-topic chunking diagnostics
  - [ ] Enhance with CLI argument: `python3.11 scripts/test_chunking.py <topic-id>`
  - [ ] Show per-book stats: filesize → text extracted → actual chunks created
  - [ ] Performance metrics: load time, index time, chunks/second
  - [ ] Efficiency report: expected vs actual chunks ratio
  - [ ] Use before/after reindexing to validate improvements

- [ ] **`scripts/update_delta.py` - automated change detection**
  - [ ] Compare `books/` filesystem vs `metadata.json`
  - [ ] Identify deltas (added/removed/modified books)
  - [ ] Auto-reindex only affected topic directories
  - [ ] Incremental metadata.json updates
  - [ ] **Stale index cleanup** - detect and remove orphaned indices
    - [ ] When topic splits into subfolders (e.g., `AI/` → `AI/theory/`, `AI/policy/`)
    - [ ] Delete parent indices: `books/AI/chunks.pkl`, `books/AI/faiss.index`
    - [ ] Create new subfolder indices: `books/AI/theory/chunks.pkl`, etc.
    - [ ] Detection: Parent folder has subfolders with books but no indices

- [ ] CLI command: `python3.11 scripts/update_delta.py`
- [ ] Performance benchmarks (delta vs full reindex)

**🚨 NOTE:** Epic pivoted to meta-workflow infrastructure (CONTRIBUTING.md, status files navigation). Original delta indexing scope deferred to v0.4 or separate epic.

**Current workaround:** Manual full reindex (`python3.11 scripts/indexer.py`) or per-topic (`python3.11 scripts/reindex_topic.py <topic>`)

---

## v0.4: Indexing Quality & Reporting ❌ (PLANNED)

**Branch:** `v0.4-indexing-quality` (when started)

**Target audience:** Users experiencing poor search quality or indexing failures

**Goal:** Visibility into indexing health and automatic detection of problems

**Status:** Not started (deferred from v0.3)

**🚨 CRITICAL ISSUE:** Current indexing creates only ~0.7 chunks/book (137 chunks from 197 books). Expected: 100+ chunks/book for typical 200-page books. Root cause unknown - needs investigation.

**❌ All Pending:**

- [ ] **Indexing report system** (replace FAILED.md with comprehensive REPORT)
  - [ ] Track timing metrics (total time, time per book, chunks per second)
  - [ ] Generate `engine/docs/REPORT.md` after each indexing run
  - [ ] **✅ Success section:** Topics indexed successfully with stats
    - Example: `✅ AI: 1224 chunks from 8 books (153 chunks/book avg) - 2.3min`
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

**Current workaround:** Manual inspection of FAILED.md, manual chunk count validation

---

## v0.5: Provider Integration 🔶 (IN PROGRESS)

**Branch:** `v0.5-provider-integration` (when started)

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

---

## v0.2: VS Code Extension Configuration ✅ (COMPLETED - 2026-01-20)

**Branch:** Direct to `main` (hotfix)

**Target audience:** VS Code users with different Python setups or library locations

**Goal:** Make extension work for any user - no hardcoded paths

**Problem:** v0.1.0 extension hardcoded `/opt/homebrew/bin/python3.11` and `books/` path

**✅ Completed:**

- [x] Added configuration settings to `package.json`
  - [x] `personalLibrary.pythonPath` - configurable Python interpreter
  - [x] `personalLibrary.booksPath` - configurable books directory (relative or absolute)
- [x] Updated `extension.ts` to read configuration values
  - [x] Python path from config (defaults to `python3`)
  - [x] Books path from config (defaults to `books`)
  - [x] Support for absolute and workspace-relative paths
- [x] Fixed `research.py` STORAGE_DIR bug (undefined variable → BOOKS_DIR)
- [x] Bumped extension version to 0.2.0
- [x] Created new `.vsix` package and `latest` symlink
- [x] Updated README.md with VS Code Setup section
  - [x] Installation instructions
  - [x] Configuration examples for macOS/Linux/Windows
  - [x] Platform-specific Python paths

**Impact:** Extension now portable across different setups

**Migration:** Users must add settings to `.vscode/settings.json`:

```json
{
  "personalLibrary.pythonPath": "python3",
  "personalLibrary.booksPath": "books"
}
```

---

## v0.5: VS Code Extension UX Epic ❌ (PLANNED)

**Branch:** `v0.5-vscode-ux` (when started)

**Target audience:** VS Code users doing research with /research prompt

**Goal:** Reduce guessing in AI tab - make books/folders directly referenceable

**Problem:** Currently AI must guess which book/topic user wants. With focused search (post-subfolder reorganization), precision matters more.

**Proposed solution:** Autocomplete for books/topics using `#` syntax

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

**Benefits:**

- No more guessing which topic AI will search
- Faster, more precise research queries
- Better UX for large libraries with many topics
- Leverages existing metadata.json infrastructure

---

## v0.6: Automation & Advanced Features ❌ (PLANNED)

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
