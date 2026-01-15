#!/usr/bin/env python3
"""
Rebuilds RAG index from scratch.
Triggered by CLI: python3 scripts/rebuild_index.py (interactive, wipes and rebuilds index)
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import shutil

sys.path.insert(0, str(Path(__file__).parent))

from literature_watchdog import index_book, BOOKS_DIR, STORAGE_DIR

load_dotenv()


def main():
    print("=" * 60)
    print("🔄 Rebuilding Literature RAG Index")
    print("=" * 60)

    # Confirm
    print("\n⚠️  This will delete the existing index and rebuild from scratch.")
    response = input("Continue? (yes/no): ")

    if response.lower() != 'yes':
        print("❌ Cancelled")
        return

    # Delete existing index
    if STORAGE_DIR.exists():
        print(f"\n🗑️  Deleting existing index...")
        shutil.rmtree(STORAGE_DIR)
        print("   ✓ Deleted")

    # Find all books
    books = []
    for folder in BOOKS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue

        for item in folder.iterdir():
            if item.suffix == '.epub' or (item.is_dir() and item.suffix == '.epub'):
                books.append(item)

    print(f"\n📚 Found {len(books)} books to index\n")

    # Index each book
    for i, book_path in enumerate(books, 1):
        print(f"[{i}/{len(books)}] ", end='')
        try:
            index_book(book_path)
        except Exception as e:
            print(f"❌ Error: {e}\n")

    print("\n" + "=" * 60)
    print("✅ Rebuild complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
