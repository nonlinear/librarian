#!/usr/bin/env python3
"""
Smart reindexing: Only reindex what changed (delta detection)
Replaces full reindexing with intelligent change detection
"""

import os
import sys
import json
import argparse
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
    METADATA_FILE = BOOKS_DIR / 'metadata.json'

    print("🧠 Smart Reindexing")
    print("=" * 50)

    if force_all:
        print("\n⚠️  --force flag: Reindexing ALL books")
        # Run full indexer
        from scripts.indexer import main as full_indexer
        full_indexer()
        return

    # Detect changes
    print("\n1. Detecting changes...")
    new_books, modified_books, deleted_books = detect_changes(BOOKS_DIR, METADATA_FILE)

    total_changes = len(new_books) + len(modified_books)

    print(f"\n📊 Changes detected:")
    print(f"   New: {len(new_books)}")
    print(f"   Modified: {len(modified_books)}")
    print(f"   Deleted: {len(deleted_books)}")

    if total_changes == 0:
        print("\n✅ No changes - nothing to reindex!")
        print("   Use --force to reindex everything anyway")
        return

    # TODO: Implement selective reindexing
    # For now, just show what would be reindexed
    print(f"\n⚡ Would reindex {total_changes} books (not all)")
    print("\n🚧 Selective reindexing not yet implemented")
    print("   For now, use: python3.11 scripts/indexer.py")
    print("   Coming soon: Only reindex changed books")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Smart reindexing with delta detection')
    parser.add_argument('--force', action='store_true',
                        help='Force reindex all books (ignore timestamps)')

    args = parser.parse_args()
    smart_reindex(force_all=args.force)
