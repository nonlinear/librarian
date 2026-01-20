# Personal Library MCP - Changelog

> Completed features and version history

---

## Release Format

Each release documents:

- 📦 **What's new:** Features and changes
- 👥 **Who needs to know:** Target audience and impact
- 🔧 **Migration:** Breaking changes and upgrade steps (if any)

---

## v0.2.3: Critical Bug Fixes ✅ (Jan 20, 2026)

**👥 Who needs to know:**

- All users with nested topics (e.g., `cybersecurity/applied/`)
- All users with root topics containing spaces (e.g., `product architecture/`)
- Anyone who ran `reindex_topic.py` manually

**📦 What's new:**

**Problems Fixed:**

1. **Path Resolution Bug:** Topics with underscores failed to resolve correctly
   - Nested topics: `cybersecurity_applied` didn't map to `books/cybersecurity/applied/`
   - Root topics with spaces: `product_architecture` didn't map to `books/product architecture/`
   - **Impact:** Books weren't being indexed, queries failed silently

2. **Critical Chunking Bug:** EPUB books weren't chunked properly
   - `reindex_topic.py` used raw documents instead of chunked nodes from index
   - **Result:** 1 chunk per book instead of ~200 chunks per book
   - **Example:** `product_architecture` had only 5 chunks from 5 books (should be ~1000+)
   - **Impact:** Severely degraded search quality - couldn't find specific passages

**Solutions Implemented:**

- [x] Fixed path resolution in `indexer.py`, `reindex_topic.py`, `mcp_server.py`
  - Try nested path first (`topic_id.replace('_', '/')`)
  - Fall back to label if nested path doesn't exist
  - Handles both nested topics and root topics with underscores
- [x] Fixed chunking in `reindex_topic.py`
  - Changed from iterating raw documents to extracting chunked nodes from index
  - Added explicit chunk settings (1024 chars, 200 overlap)
  - Added debug output showing chunk counts
- [x] Renamed scripts for clarity
  - `query_partitioned.py` → `research.py` (matches research.prompt.md)
  - `mcp_server_lazy.py` → `mcp_server.py` (production server)
- [x] Documentation improvements
  - Added happy path validation test to CHECKS.md
  - Added CHANGELOG append-only policy to whatsup.prompt.md
  - Designed comprehensive REPORT.md system in ROADMAP

**🔧 Migration:**

- **If you have nested topics or topics with underscores:** Re-run full indexer to rebuild with correct paths
  ```bash
  python3.11 scripts/indexer.py
  ```
- **If you manually reindexed topics:** Re-run those topics to get proper chunking
  ```bash
  python3.11 scripts/reindex_topic.py <topic-name>
  ```
- **Script renames:** Update any custom scripts or documentation referencing old names

**Impact:** Correct indexing for all topic types, dramatically improved search quality

---

## v0.2.2: Failed Books Tracking ✅ (Jan 19, 2026)

**👥 Who needs to know:**

- Users indexing books
- Anyone troubleshooting failed book imports

**📦 What's new:**

**Problem:** Books that fail to index (corrupted files, unsupported formats) errors were only shown during indexing with no persistent log

**Solution Implemented:** Failed Books Log

- [x] Added failed_books tracking to indexer.py
- [x] Created FAILED.md output (organized by topic with file links)
- [x] Updated README.md with troubleshooting reference

**Impact:** Easy troubleshooting for corrupted/unsupported books

**🔧 Migration:** None (automatic on next index run)

---

## v0.2.1: Infrastructure Improvements ✅ (Jan 19, 2026)

**👥 Who needs to know:**

- Contributors and maintainers
- AI assistants working with this codebase

**📦 What's new:**

**Problem:** Fragmented documentation, outdated tests, missing AI conventions

**Solution Implemented:** Workflow Consolidation 🧹

- [x] Migrated checklist → CHECKS.md (single source of truth)
- [x] Fixed stability tests (MCP query + file structure for lazy-loading architecture)
- [x] Established 🤖: marker convention for AI instructions
- [x] Added navigation menus to all status files
- [x] Updated whatsup.prompt.md with navigation menu auto-generation
- [x] Configured Copilot to recognize 🤖: markers
- [x] Cleaned up obsolete files (3 deleted)

**Impact:** Cleaner repo, accurate tests, better AI collaboration

**🔧 Migration:** None (documentation/tooling only)

---

## v0.2: PDF Support + Integrated Reindexing ✅ (Jan 18, 2026)

**Branch:** `main` (promoted from development)

**👥 Who needs to know:**

- Users with PDF books who couldn't use MCP before
- Users experiencing crashes during reindexing (M3 Mac fix)

**📦 What's new:**

**Problem:** Only EPUBs supported, reindexing loaded model 23 times (memory inefficient)

**Solution Implemented:** PDF Support + Single-Process Reindexing 🎉

- [x] **PDF Support Added**
  - [x] PyMuPDF (fitz) for text extraction
  - [x] Updated `generate_metadata.py` for PDF metadata extraction
  - [x] Updated `reindex_topic.py` with file type detection (.epub vs .pdf)
  - [x] Updated `mcp_server_lazy.py` to handle PDF documents
  - [x] Tested with 4 PDFs in computer vision topic (2460 chunks indexed)
  - ⚠️ MuPDF ICC profile warnings (cosmetic, don't affect indexing)
- [x] **Integrated Reindexing Architecture**
  - [x] Created `scripts/reindex_all.py`
  - [x] Loads embedding model **once**, reuses for all 23 topics
  - [x] 23× more memory efficient than subprocess approach
  - [x] Prevents Python crashes from repeated model loading
- [x] **Embedding Model Evaluation**
  - [x] Tested `all-mpnet-base-v2` (768-dim) for better quality
  - [x] Crashes on M3 Mac during reindexing (leaked semaphores)
  - [x] Decided to keep `all-MiniLM-L6-v2` (384-dim) for stability

**Impact:** Mixed EPUB/PDF libraries now supported, 23× more efficient reindexing

**🔧 Migration:** None (backward compatible)

---

## v0.1: Database Optimization ✅ (Jan 15, 2026)

**Branch:** `main` (promoted from development)

**👥 Who needs to know:**

- Users experiencing slow MCP startup (30s → <100ms)
- Users who don't want API dependencies

**📦 What's new:**

**Problem:** `storage/docstore.json` (17MB) caused 30s MCP startup delay + Gemini API dependency

**Solution Implemented:** Topic-Based Lazy Loading + Local Embeddings 🎉

- [x] **Migrated to local embeddings** (Jan 15, 2026)
  - [x] Replaced Gemini (768-dim) → sentence-transformers (384-dim)
  - [x] Model stored in `models/` (90MB, gitignored)
  - [x] Zero API keys required - fully offline
  - [x] Updated: `indexer.py`, `research.py`, `setup.sh`
  - [x] Removed: `.env` requirement, API key docs
- [x] Created `scripts/partition_storage.py`
- [x] **Integrated auto-partitioning in `indexer.py`** (no manual step)
- [x] Split storage into 12 topic-specific directories (automated)
- [x] Created `scripts/mcp_server_lazy.py`
  - [x] Loads ONLY `metadata.json` (19KB) on startup → **instant** (<100ms)
  - [x] Lazy-loads topics on first query (~2s per topic)
  - [x] Topic caching prevents reload
- [x] Binary format (pickle) for faster deserialization

**🔧 Migration:** Run `python3.11 scripts/indexer.py` to regenerate partitioned storage

**Impact:** Mixed EPUB/PDF libraries now supported, 23× more efficient reindexing

---

## Foundation ✅ (Initial Release)

**Core infrastructure for Personal Library MCP**

- [x] `metadata.json` generation (`scripts/generate_metadata.py`)
- [x] LlamaIndex vector store setup
- [x] Local embedding model (sentence-transformers/all-MiniLM-L6-v2, 384-dim)
  - [x] Model cached in `models/` (90MB, not tracked by git)
  - [x] Zero API keys required
  - [x] Fully offline operation
- [x] CLI query tool (`scripts/research.py`)
- [x] MCP server with 3 tools (query_library, list_topics, list_books)
- [x] Metadata-first query routing
- [x] Topic-partitioned storage (FAISS + pickle per topic)
- [x] Auto-partitioning integrated in `indexer.py`

**Impact:** Full local MCP infrastructure for book queries

---

> 🤖: See [ROADMAP](engine/docs/ROADMAP.md) for planned features & in-progress work
> 🤖: See [CHANGELOG](engine/docs/CHANGELOG.md) for ersion history & completed features
> 🤖: See [CHECKS](engine/docs/CHECKS.md) for stability requirements & testing
> 👷: Consider using [/whatsup prompt](https://github.com/nonlinear/nonlinear.github.io/blob/main/.github/prompts/whatsup.prompt.md) for updates

v0.0: Foundation ✅ (Initial Release)

**Branch:** `main` (initial commit)

**👥 Who needs to know:** All users (initial setup)

**📦 What's new:**
