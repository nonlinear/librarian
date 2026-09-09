#!/usr/bin/env python3
"""
Init Index — Self-healing index bootstrap for Librarian v6.

Idempotent. Safe to run on every container start.

Behavior:
1. If FAISS index exists and is valid → quick health check, done.
2. If FAISS index is missing or corrupted → rebuild from scratch via v6.
3. Returns exit code 0 on success, non-zero on failure.

Checkpointing (v6 built-in):
- Saves index_state.json every 10 books
- If interrupted mid-way, next run picks up from last checkpoint
"""
import os
import sys
import json
import signal
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init-index")

# Paths — resolved via config (Boundary: engine knows no instance paths)
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/ for config
from config import get_config
_cfg = get_config()
LIBRARY_ROOT = _cfg.corpus_path
FAISS_INDEX_PATH = _cfg.index_path
METADATA_PATH = _cfg.metadata_path


def index_is_valid() -> bool:
    """Quick validation: FAISS index + metadata exist and are non-empty."""
    if not FAISS_INDEX_PATH.exists():
        logger.warning("FAISS index not found")
        return False
    if not METADATA_PATH.exists():
        logger.warning("Metadata file not found")
        return False

    faiss_size = FAISS_INDEX_PATH.stat().st_size
    meta_size = METADATA_PATH.stat().st_size

    if faiss_size < 1024:
        logger.warning(f"FAISS index too small: {faiss_size} bytes")
        return False
    if meta_size < 100:
        logger.warning(f"Metadata too small: {meta_size} bytes")
        return False

    # Try loading metadata to validate JSON
    try:
        with open(METADATA_PATH) as f:
            meta = json.load(f)
        chunks = meta.get("chunks", [])
        books = meta.get("books", [])
        if len(chunks) == 0:
            logger.warning("Metadata has zero chunks — need reindex")
            return False
        logger.info(f"Valid index: {len(chunks):,} chunks, {len(books)} books")
        return True
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Metadata corrupted: {e}")
        return False


def signal_http_server():
    """Sends SIGHUP to the running librarian_http process if it exists."""
    pid_file = Path("/tmp/librarian_http.pid")
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGHUP)
            logger.info(f"Sent SIGHUP to PID {pid} (librarian_http)")
        except (ProcessLookupError, ValueError, OSError) as e:
            logger.warning(f"Could not signal reload: {e}")
    else:
        logger.info("No librarian_http PID file — server probably not running yet")


def main():
    """Idempotent entry point.
    
    SKIP_REBUILD=1 → validate only, never rebuild.
    Use when you know the index is good and don't want init_index touching it.
    """
    skip_rebuild = os.environ.get("SKIP_REBUILD", "0") == "1"
    
    logger.info("=" * 60)
    logger.info("Init Index — checking FAISS index status")
    if skip_rebuild:
        logger.info("SKIP_REBUILD=1 — validate only, no rebuild")
    logger.info("=" * 60)

    if index_is_valid():
        logger.info("✅ Index valid, no action needed")
        return 0
    
    if skip_rebuild:
        logger.warning("Index invalid but SKIP_REBUILD=1 — NOT rebuilding. Server may serve degraded.")
        return 0

    logger.info("🔨 Index missing or invalid — rebuilding via v6 indexer...")
    import time
    start = time.time()

    try:
        # Import and run v6 incremental indexer
        from indexer_v6 import index_incremental
        index_incremental()
        elapsed = time.time() - start
        
        # Verify result
        if index_is_valid():
            logger.info(f"✅ Index built successfully ({elapsed:.0f}s)")
            signal_http_server()
            return 0
        else:
            logger.error(f"❌ Index build completed but index is still invalid ({elapsed:.0f}s)")
            return 1
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"❌ Index build FAILED after {elapsed:.0f}s: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
