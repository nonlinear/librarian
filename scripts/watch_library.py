#!/usr/bin/env python3
"""
Watch library for changes and auto-reindex topics

Usage:
    python watch_library.py                # Watch all topics
    python watch_library.py --topics cooking ai_policy  # Watch specific topics

Background:
    nohup python watch_library.py &        # Run in background

Stop:
    ps aux | grep watch_library
    kill <PID>
"""

import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Paths
LIBRARY_ROOT = Path(__file__).parent.parent / "books"
INDEXER_SCRIPT = Path(__file__).parent / "indexer_v2.py"


class LibraryWatcher(FileSystemEventHandler):
    """Watch for PDF/EPUB changes and trigger reindexing"""

    def __init__(self, watch_topics=None):
        self.watch_topics = set(watch_topics) if watch_topics else None
        self.debounce = {}  # Prevent duplicate triggers
        self.debounce_seconds = 5

    def get_topic_from_path(self, file_path):
        """Extract topic ID from file path"""
        path = Path(file_path)

        # books/cooking/Book.pdf → cooking
        # books/AI/policy/Book.pdf → ai_policy

        relative = path.relative_to(LIBRARY_ROOT)
        parts = relative.parts[:-1]  # Remove filename

        if not parts:
            return None

        # Convert path to topic_id (cooking or ai_policy)
        topic_id = '_'.join(parts).lower().replace(' ', '_')
        return topic_id

    def should_process(self, topic_id):
        """Check if we should process this topic"""
        if not topic_id:
            return False

        # Filter by watch list if specified
        if self.watch_topics and topic_id not in self.watch_topics:
            return False

        # Debounce (avoid duplicate triggers within 5 seconds)
        now = time.time()
        last_trigger = self.debounce.get(topic_id, 0)

        if now - last_trigger < self.debounce_seconds:
            return False

        self.debounce[topic_id] = now
        return True

    def trigger_reindex(self, topic_id):
        """Run indexer_v2.py on the changed topic"""
        print(f"\n{'='*60}")
        print(f"🔄 Change detected in: {topic_id}")
        print(f"{'='*60}")
        print(f"⚡ Triggering reindex...")

        try:
            result = subprocess.run(
                [sys.executable, str(INDEXER_SCRIPT), topic_id],
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )

            # Show output
            if result.stdout:
                print(result.stdout)

            if result.returncode == 0:
                print(f"✅ Reindex completed successfully")
            else:
                print(f"❌ Reindex failed with code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"⏱️ Reindex timed out (>5 min)")

        except Exception as e:
            print(f"❌ Error running indexer: {e}")

        print(f"{'='*60}\n")

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return

        # Only watch PDF/EPUB files
        if not event.src_path.endswith(('.pdf', '.epub')):
            return

        topic_id = self.get_topic_from_path(event.src_path)

        if self.should_process(topic_id):
            self.trigger_reindex(topic_id)

    def on_created(self, event):
        """Handle file creation events"""
        self.on_modified(event)  # Same logic as modification

    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return

        if not event.src_path.endswith(('.pdf', '.epub')):
            return

        topic_id = self.get_topic_from_path(event.src_path)

        if self.should_process(topic_id):
            print(f"\n⚠️  Book deleted in {topic_id}: {Path(event.src_path).name}")
            self.trigger_reindex(topic_id)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Watch library and auto-reindex on changes')
    parser.add_argument('--topics', nargs='+', help='Specific topics to watch (default: all)')

    args = parser.parse_args()

    print("👀 Personal Library Watcher")
    print("=" * 60)
    print(f"📁 Watching: {LIBRARY_ROOT}")

    if args.topics:
        print(f"📋 Topics: {', '.join(args.topics)}")
    else:
        print(f"📋 Topics: All")

    print(f"⚡ Auto-reindex: Enabled (delta detection)")
    print(f"🔕 Debounce: 5 seconds")
    print("=" * 60)
    print("\n✅ Watching for changes... (Ctrl+C to stop)\n")

    # Create event handler
    event_handler = LibraryWatcher(watch_topics=args.topics)

    # Create observer
    observer = Observer()
    observer.schedule(event_handler, str(LIBRARY_ROOT), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping watcher...")
        observer.stop()

    observer.join()
    print("✅ Watcher stopped")


if __name__ == "__main__":
    main()
