# Personal Library MCP - Changelog

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

### v0.3

#### ✅ Meta-Workflow Infrastructure

Established workflow infrastructure for epic-based development

- Created [CONTRIBUTING.md](../../.github/CONTRIBUTING.md) - Git workflow & branch strategy
- Defined branch-per-epic policy (`v{major}.{minor}-{epic-name}`)
- Documented rebase-only workflow (from `main`)
- Established merge workflow (whatsup → merge → tag → delete branch → announce)
- Branch deletion policy (recommended after merge, history preserved via tags)
- Semantic versioning guidelines for AI projects
- Standardized navigation across all status files
- README as single source of truth for navigation

✅ Always copy navigation block from README to status files
🗒️ Originally planned as "Delta Indexing" but pivoted to meta-workflow. Delta automation deferred.

---

### v0.2.6

#### ✅ Library cleanup

fixing subtopics as flat ones

- **Fixed partition_storage.py crash:** `UnboundLocalError: topic_label` when creating per-topic indices
  - Root cause: Variable used before assignment in loop
  - Impact: Full reindexing (indexer.py) would fail at partitioning step
  - Now works: `topic_label = topic_info[topic_id]['label']` added before use

**Library Maintenance:**

- Removed corrupted RPG/changeling topic (10 PDFs with "Bad Zip file" errors)
- Regenerated metadata after cleanup: 36 topics, 247 books (was 37 topics, 247 books)
- Verified hugo topic indexes correctly: 94 chunks from "Build Websites with Hugo"

**Files changed:**

- `scripts/partition_storage.py`: Added topic_label assignment (line 114)

**🔧 Migration:** None - just a bug fix

---

### v0.2.5

#### ✅ Path Resolution & Platform-Agnostic Prompt

**👥 Who needs to know:** Users with subtopics (AI/theory) or folder names with spaces (product architecture)

**📦 What's new:**

**Path Resolution Fix:**

- **Added `folder_path` field** to metadata.json for all topics
  - Solves ambiguity: `ai_theory` → `"AI/theory"` vs `product_architecture` → `"product architecture"`
  - No more guessing from topic IDs with underscores
- **Updated all scripts** to use `folder_path` from metadata:
  - `research.py` - FAISS index loading
  - `reindex_topic.py` - Topic folder location
  - `mcp_server.py` - MCP query routing
  - `partition_storage.py` - Storage partitioning
- **Citation links now work** for nested topics (was broken for subtopics)

**Prompt Improvements:**

- **Platform-agnostic research.prompt.md:**
  - Removed MCP-specific tool calls
  - Generic command execution: `python3.11 scripts/research.py "{query}" --topic {topic}`
  - Works with any AI provider: VS Code (run_in_terminal), Claude Desktop (MCP/shell), OpenAI (subprocess), Terminal (manual)
- **Background execution support:** Documents `isBackground: true` for silent queries

**Files changed:**

- `scripts/generate_metadata.py`: Adds `folder_path` field (e.g., `"AI/theory"`, `"product architecture"`)
- `scripts/research.py`: Uses `folder_path` instead of splitting topic_id
- `scripts/reindex_topic.py`: Uses `folder_path` for topic directory
- `scripts/mcp_server.py`: Uses `folder_path` for query routing
- `scripts/partition_storage.py`: Uses `folder_path` for storage paths
- `.github/prompts/research.prompt.md`: Platform-agnostic instructions with folder_path path calculation

**🔧 Migration:**

1. **Regenerate metadata:** `python3.11 scripts/generate_metadata.py` (adds folder_path to all topics)
2. No reindexing needed - existing indices work fine

**Example fixes:**

- Citation: `[Superintelligence.epub](../personal%20library/books/AI/theory/Superintelligence.epub)` ✅ (was: `books/ai_theory/` ❌)
- Path lookup: `books/product architecture/` ✅ (was: `books/product/architecture/` ❌)

---

### v0.2.4

#### ✅ Critical Chunking Bug Fix

**👥 Who needs to know:** ALL USERS - this fix improves search quality 400x

**📦 What's new:**

**Critical Bug Fixed:**

- **Chunking disaster:** Partitioning script was only saving 1 chunk per book instead of all chunks
  - **Before:** 137 chunks from 197 books (0.7 chunks/book) = unusable search
  - **After:** 54,962 chunks from 282 books (195 chunks/book avg) = proper granular search
  - **Impact:** Nearly 2x the health target (100+ chunks/book)
  - Search can now find specific passages instead of entire books

**Root cause:** `partition_storage.py` was iterating through docstore (original documents) instead of the chunked nodes created during indexing

**Files changed:**

- `scripts/partition_storage.py`: Fixed to save all chunks, not just documents
- Added `chunks.json` alongside `chunks.pkl` for easier debugging

**🔧 Migration:**

1. **Reindex required:** Run `python3.11 scripts/indexer.py` to rebuild all indices with proper chunking
2. Takes 5-10 minutes for full library (worth it for 400x improvement!)

**Example improvements:**

- Small books: 84-148 chunks (was 1)
- Medium books: 400-700 chunks (was 1)
- Large books: 700-5,000+ chunks (was 1-2)

**Discovered during:** NAS books reorganization + chunking diagnostics

---

### v0.2.3

#### ✅ Critical Bug Fixes

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

### v0.2.2

#### ✅ Failed Books Tracking

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

### v0.2.1

#### ✅ Infrastructure Improvements

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

### v0.2

#### ✅ PDF Support + Integrated Reindexing

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

### v0.1

#### ✅ Database Optimization

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

### Foundation

#### ✅ Initial Release

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
