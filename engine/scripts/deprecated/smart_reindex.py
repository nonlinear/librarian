#!/usr/bin/env python3
"""
Smart reindexing: Only reindex what changed (delta detection)
Replaces full reindexing with intelligent change detection
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from detect_changes import detect_changes, update_indexed_timestamp


def smart_reindex(force_all=False):
    """
    Smart reindexing with delta detection

    Args:
        force_all: If True, reindex everything (ignore timestamps)
    """
    BOOKS_DIR = Path(__file__).parent.parent / 'books'
    LIBRARY_INDEX = BOOKS_DIR / 'library-index.json'

    print("🧠 Smart Reindexing")
    print("=" * 50)

    if force_all:
        print("\n⚠️  --force flag: Reindexing ALL books")
        # Run full indexer v2
        import subprocess
        INDEXER_V2 = SCRIPTS_DIR / "indexer_v2.py"
        PYTHON = sys.executable
        result = subprocess.run([PYTHON, str(INDEXER_V2), "--all", "--force"])
        return

    # Detect changes
    print("\n1. Detecting changes...")
    new_books, modified_books, deleted_books = detect_changes(BOOKS_DIR, LIBRARY_INDEX)

    total_changes = len(new_books) + len(modified_books)

    print(f"\n📊 Changes detected:")
    print(f"   New: {len(new_books)}")
    print(f"   Modified: {len(modified_books)}")
    print(f"   Deleted: {len(deleted_books)}")

    if total_changes == 0:
        print("\n✅ No changes - nothing to reindex!")
        print("   Use --force to reindex everything anyway")
        return

    # Group changed books by topic
    topics_to_reindex = set()

    for book_path in new_books + modified_books:
        # Extract topic from path: books/theory/anthropocene/Book.pdf -> theory/anthropocene
        book_path_obj = Path(book_path)
        relative = book_path_obj.relative_to(BOOKS_DIR)
        topic_path = str(relative.parent)
        topics_to_reindex.add(topic_path)

    print(f"\n⚡ Reindexing {len(topics_to_reindex)} affected topics:")
    for topic in sorted(topics_to_reindex):
        print(f"   • {topic}")

    # Run indexer_v2.py for each affected topic
    import subprocess
    INDEXER_V2 = SCRIPTS_DIR / "indexer_v2.py"
    PYTHON = sys.executable

    print(f"\n🔄 Starting selective reindexing...")

    for topic_path in sorted(topics_to_reindex):
        print(f"\n   Reindexing: {topic_path}")
        result = subprocess.run(
            [PYTHON, str(INDEXER_V2), "--topic", topic_path, "--force"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"      ✅ Success")
        else:
            print(f"      ❌ Failed")
            if result.stderr:
                print(f"      Error: {result.stderr}")

    print(f"\n✅ Selective reindexing complete!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Smart reindexing with delta detection')
    parser.add_argument('--force', action='store_true',
                        help='Force reindex all books (ignore timestamps)')

    args = parser.parse_args()
    smart_reindex(force_all=args.force)
