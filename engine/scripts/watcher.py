#!/usr/bin/env python3
"""
T019: File Watcher - Auto-detect and index new books

Watches the corpus root (resolved from config) for new EPUB/PDF files and triggers reindexing.
"""
import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/ for config
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[WATCHER] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

_cfg = get_config()
BOOKS_DIR = _cfg.corpus_path
INDEXER_SCRIPT = _cfg.engine_scripts_dir / "indexer.py"
DEBOUNCE_SECONDS = 5  # Wait for multiple files


class BookWatcher(FileSystemEventHandler):
    """Watch for new book files."""
    
    def __init__(self):
        self.pending_files = set()
        self.last_event_time = 0
    
    def on_created(self, event):
        """Handle new file creation."""
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Only watch EPUB/PDF
        if filepath.suffix.lower() not in ['.epub', '.pdf']:
            return
        
        # Ignore no-indexing folder
        if 'no-indexing' in filepath.parts:
            logger.info(f"Ignoring file in no-indexing/: {filepath.name}")
            return
        
        logger.info(f"New book detected: {filepath.name}")
        
        # Add to pending queue
        self.pending_files.add(filepath)
        self.last_event_time = time.time()
    
    def process_pending_files(self):
        """Process all pending files after debounce period."""
        if not self.pending_files:
            return
        
        # Check if debounce period has passed
        time_since_last = time.time() - self.last_event_time
        if time_since_last < DEBOUNCE_SECONDS:
            return
        
        # Wait for file write to complete (check size stability)
        for filepath in list(self.pending_files):
            if not self._is_file_stable(filepath):
                logger.info(f"Waiting for file write to complete: {filepath.name}")
                return
        
        logger.info(f"Processing {len(self.pending_files)} new book(s)...")
        
        # Spawn background indexer (fire-and-forget)
        try:
            self._trigger_reindex()
            logger.info("✅ Indexer spawned")
        except Exception as e:
            logger.error(f"❌ Spawn failed: {e}")
        finally:
            self.pending_files.clear()
    
    def _is_file_stable(self, filepath: Path, check_seconds: int = 2) -> bool:
        """Check if file size has stabilized (write complete)."""
        if not filepath.exists():
            return False
        
        try:
            size1 = filepath.stat().st_size
            time.sleep(check_seconds)
            size2 = filepath.stat().st_size
            return size1 == size2
        except Exception:
            return False
    
    def _trigger_reindex(self):
        """Spawn indexer job (fire-and-forget)."""
        logger.info(f"Spawning indexer for {len(self.pending_files)} file(s)...")
        
        # Spawn background process (non-blocking)
        subprocess.Popen(
            ["python3", "/app/engine/scripts/indexer.py", "--discipline", "home"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from watcher
        )
        
        logger.info("✅ Indexer spawned (background) — HTTP server will auto-reload on completion")
        # Note: indexer.py sends SIGHUP to HTTP server when done (T002)

def main():
    """Start watching for new books."""
    logger.info(f"Starting file watcher on {BOOKS_DIR}")
    logger.info(f"Debounce: {DEBOUNCE_SECONDS}s")
    
    event_handler = BookWatcher()
    observer = Observer()
    observer.schedule(event_handler, str(BOOKS_DIR), recursive=True)
    observer.start()
    
    logger.info("✅ Watcher active")
    
    try:
        while True:
            # Check pending files every second
            time.sleep(1)
            event_handler.process_pending_files()
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer.stop()
    
    observer.join()


if __name__ == "__main__":
    main()
