#!/usr/bin/env python3
"""
T019: File Watcher - Auto-detect and index new books

Watches /app/books/ for new EPUB/PDF files and triggers reindexing.
"""
import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[WATCHER] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BOOKS_DIR = Path("/app/books")
INDEXER_SCRIPT = Path("/app/engine/scripts/indexer_v5.py")
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
        
        # Trigger full reindex (handles duplicates + unindexable)
        try:
            self._trigger_reindex()
            self._reload_mcp()
            logger.info("✅ Reindex + reload complete")
        except Exception as e:
            logger.error(f"❌ Reindex failed: {e}")
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
        """Run indexer to process new books."""
        logger.info("Running incremental indexer...")
        result = subprocess.run(
            ["python3", "/app/engine/scripts/indexer_v6.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Indexer failed: {result.stderr}")
            raise RuntimeError("Indexer failed")
        
        logger.info("Indexer completed")
    
    def _reload_mcp(self):
        """Trigger MCP hot-reload via SIGHUP."""
        logger.info("Reloading MCP...")
        try:
            # Send SIGHUP to mcp_server_faiss.py process
            subprocess.run(
                ["pkill", "-HUP", "-f", "mcp_server_faiss.py"],
                check=True
            )
            logger.info("MCP reload signal sent")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to send reload signal: {e}")


def main():
    """Start watching for new books."""
    logger.info(f"Starting file watcher on {BOOKS_DIR}")
    logger.info(f"Debounce: {DEBOUNCE_SECONDS}s")
    
    # Create observer
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
