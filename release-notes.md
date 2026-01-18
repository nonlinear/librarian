# Personal Library MCP - Release Notes

> Completed features and deployments

**See also:** [Roadmap](roadmap.md) for planned features.

---

## Phase 1: Database Optimization ✅ (Jan 15, 2026)

**Problem:** `storage/docstore.json` (17MB) caused 30s MCP startup delay + Gemini API dependency

**Solution Implemented:** Topic-Based Lazy Loading + Local Embeddings 🎉

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

**Impact:** Startup time reduced from 30s to <100ms, zero API dependencies

---

## Phase 2: PDF Support + Integrated Reindexing ✅ (Jan 18, 2026)

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

---

## Foundation ✅ (Initial Release)

**Core infrastructure for Personal Library MCP**

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

**Impact:** Full local MCP infrastructure for book queries

---

**See also:** [Roadmap](roadmap.md) for planned features.
