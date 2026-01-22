# Personal Library MCP - Changelog

### Epic-per-branch workflow

[commit](https://github.com/nonlinear/personal-library/commit/3c201e47b)

Branch-based development for each roadmap epic.

- [x] Enforce: Each ROADMAP epic = dedicated feature branch
- [x] Branch naming: `v{major}.{minor}-{epic-name}` (e.g., `v0.3-delta-indexing`)
- [x] Workflow: Regular rebase from `main` to stay current
- [x] Completion criteria: Merge to `main` = move ROADMAP section → CHANGELOG
- [x] Add git hooks or CI checks to validate workflow compliance
- [x] Update whatsup.prompt.md to handle feature branch workflow
- [x] Document branch-based development in contributing guide
- **Note:** Current workflow is direct commits to `main` (works for now)

## v0.3

[commit](https://github.com/nonlinear/personal-library/commit/caf6d7fa7)

### Meta-Workflow Infrastructure

Established workflow infrastructure for epic-based development

✅ Always copy navigation block from README to status files
🗒️ Originally planned as "Delta Indexing" but pivoted to meta-workflow. Delta automation deferred.

## v0.2.6

[commit](https://github.com/nonlinear/personal-library/commit/709410687)

### Library cleanup

fixing subtopics as flat ones

- Root cause: Variable used before assignment in loop
- Impact: Full reindexing (indexer.py) would fail at partitioning step
- Now works: `topic_label = topic_info[topic_id]['label']` added before use

**Library Maintenance:**

**Files changed:**

**🔧 Migration:** None - just a bug fix

## v0.2.5

[commit](https://github.com/nonlinear/personal-library/commit/75a26cd9e)

### Path Resolution & Platform-Agnostic Prompt

**👥 Who needs to know:** Users with subtopics (AI/theory) or folder names with spaces (product architecture)

**📦 What's new:**

**Path Resolution Fix:**

- Solves ambiguity: `ai_theory` → `"AI/theory"` vs `product_architecture` → `"product architecture"`
- No more guessing from topic IDs with underscores
- `research.py` - FAISS index loading
- `reindex_topic.py` - Topic folder location
- `mcp_server.py` - MCP query routing
- `partition_storage.py` - Storage partitioning

**Prompt Improvements:**

- Removed MCP-specific tool calls
- Generic command execution: `python3.11 scripts/research.py "{query}" --topic {topic}`
- Works with any AI provider: VS Code (run_in_terminal), Claude Desktop (MCP/shell), OpenAI (subprocess), Terminal (manual)

**Files changed:**

**🔧 Migration:**

1. **Regenerate metadata:** `python3.11 scripts/generate_metadata.py` (adds folder_path to all topics)
2. No reindexing needed - existing indices work fine

**Example fixes:**

## v0.2.4

[commit](https://github.com/nonlinear/personal-library/commit/3b3aa17a0)

### Critical Chunking Bug Fix

**👥 Who needs to know:** ALL USERS - this fix improves search quality 400x

**📦 What's new:**

**Critical Bug Fixed:**

- **Before:** 137 chunks from 197 books (0.7 chunks/book) = unusable search
- **After:** 54,962 chunks from 282 books (195 chunks/book avg) = proper granular search
- **Impact:** Nearly 2x the health target (100+ chunks/book)
- Search can now find specific passages instead of entire books

**Root cause:** `partition_storage.py` was iterating through docstore (original documents) instead of the chunked nodes created during indexing

**Files changed:**

**🔧 Migration:**

1. **Reindex required:** Run `python3.11 scripts/indexer.py` to rebuild all indices with proper chunking
2. Takes 5-10 minutes for full library (worth it for 400x improvement!)

**Example improvements:**

**Discovered during:** NAS books reorganization + chunking diagnostics

## v0.2.3

[commit](https://github.com/nonlinear/personal-library/commit/cd4d46db8)

### Critical Bug Fixes

**👥 Who needs to know:**

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

- Try nested path first (`topic_id.replace('_', '/')`)
- Fall back to label if nested path doesn't exist
- Handles both nested topics and root topics with underscores
- Changed from iterating raw documents to extracting chunked nodes from index
- Added explicit chunk settings (1024 chars, 200 overlap)
- Added debug output showing chunk counts
- `query_partitioned.py` → `research.py` (matches research.prompt.md)
- `mcp_server_lazy.py` → `mcp_server.py` (production server)
- Added happy path validation test to CHECKS.md
- Added CHANGELOG append-only policy to whatsup.prompt.md
- Designed comprehensive REPORT.md system in ROADMAP

**🔧 Migration:**

```bash
python3.11 scripts/indexer.py
```

```bash
python3.11 scripts/reindex_topic.py <topic-name>
```

**Impact:** Correct indexing for all topic types, dramatically improved search quality

## v0.2.2

[commit](https://github.com/nonlinear/personal-library/commit/34bc3405e)

### Failed Books Tracking

**👥 Who needs to know:**

**📦 What's new:**

**Problem:** Books that fail to index (corrupted files, unsupported formats) errors were only shown during indexing with no persistent log

**Solution Implemented:** Failed Books Log

**Impact:** Easy troubleshooting for corrupted/unsupported books

**🔧 Migration:** None (automatic on next index run)

## v0.2.1

[commit](https://github.com/nonlinear/personal-library/commit/c671038c7)

### Infrastructure Improvements

**👥 Who needs to know:**

**📦 What's new:**

**Problem:** Fragmented documentation, outdated tests, missing AI conventions

**Solution Implemented:** Workflow Consolidation 🧹

**Impact:** Cleaner repo, accurate tests, better AI collaboration

**🔧 Migration:** None (documentation/tooling only)

## v0.2

[commit](https://github.com/nonlinear/personal-library/commit/517420bf9)

### PDF Support + Integrated Reindexing

**👥 Who needs to know:**

**📦 What's new:**

**Problem:** Only EPUBs supported, reindexing loaded model 23 times (memory inefficient)

**Solution Implemented:** PDF Support + Single-Process Reindexing 🎉

- [x] PyMuPDF (fitz) for text extraction
- [x] Updated `generate_metadata.py` for PDF metadata extraction
- [x] Updated `reindex_topic.py` with file type detection (.epub vs .pdf)
- [x] Updated `mcp_server_lazy.py` to handle PDF documents
- [x] Tested with 4 PDFs in computer vision topic (2460 chunks indexed)
- ⚠️ MuPDF ICC profile warnings (cosmetic, don't affect indexing)
- [x] Created `scripts/reindex_all.py`
- [x] Loads embedding model **once**, reuses for all 23 topics
- [x] 23× more memory efficient than subprocess approach
- [x] Prevents Python crashes from repeated model loading
- [x] Tested `all-mpnet-base-v2` (768-dim) for better quality
- [x] Crashes on M3 Mac during reindexing (leaked semaphores)
- [x] Decided to keep `all-MiniLM-L6-v2` (384-dim) for stability

**Impact:** Mixed EPUB/PDF libraries now supported, 23× more efficient reindexing

**🔧 Migration:** None (backward compatible)

## v0.1

[commit](https://github.com/nonlinear/personal-library/commit/418d98ef7)

### Database Optimization

**👥 Who needs to know:**

**📦 What's new:**

**Problem:** `storage/docstore.json` (17MB) caused 30s MCP startup delay + Gemini API dependency

**Solution Implemented:** Topic-Based Lazy Loading + Local Embeddings 🎉

- [x] Replaced Gemini (768-dim) → sentence-transformers (384-dim)
- [x] Model stored in `models/` (90MB, gitignored)
- [x] Zero API keys required - fully offline
- [x] Updated: `indexer.py`, `research.py`, `setup.sh`
- [x] Removed: `.env` requirement, API key docs
- [x] Loads ONLY `metadata.json` (19KB) on startup → **instant** (<100ms)
- [x] Lazy-loads topics on first query (~2s per topic)
- [x] Topic caching prevents reload

**🔧 Migration:** Run `python3.11 scripts/indexer.py` to regenerate partitioned storage

**Impact:** Mixed EPUB/PDF libraries now supported, 23× more efficient reindexing

### Foundation

### Initial Release

**Core infrastructure for Personal Library MCP**

- [x] Model cached in `models/` (90MB, not tracked by git)
- [x] Zero API keys required
- [x] Fully offline operation

**Impact:** Full local MCP infrastructure for book queries

> 🤖
>
> - [README](./README.md) - Our project
> - [CHANGELOG](./engine/docs/CHANGELOG.md) — What we did
> - [ROADMAP](./engine/docs/ROADMAP.md) — What we wanna do
> - [CONTRIBUTING](./engine/docs/CONTRIBUTING.md) — How we do it
> - [CHECKS](./engine/docs/CHECKS.md) — What we accept
> - [/whatsup](./.github/prompts/whatsup.prompt.md) — The prompt that keeps us sane
>
> 🤖
