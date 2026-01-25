#!/usr/bin/env python3
"""
Delta detection: Compare filesystem vs metadata.json to find changed books
Only reindex what's actually changed (massive time savings)
"""

import json
import os
from pathlib import Path
from datetime import datetime


def get_file_mtime(filepath):
    """Get file modification time as Unix timestamp"""
    return os.path.getmtime(filepath)


def detect_changes(books_dir, metadata_file):
    """
    Compare filesystem state vs metadata.json
    Returns: (new_books, modified_books, deleted_books)
    """
    books_dir = Path(books_dir)
    metadata_file = Path(metadata_file)

    # Load existing metadata
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {'topics': []}

    # Build lookup: book_path -> last_indexed_time
    indexed_books = {}
    for topic in metadata.get('topics', []):
        topic_folder = topic.get('folder_path', topic['label'])
        for book in topic.get('books', []):
            book_path = books_dir / topic_folder / book['filename']
            last_indexed = book.get('last_indexed_at')
            indexed_books[str(book_path)] = last_indexed

    # Scan filesystem
    new_books = []
    modified_books = []
    deleted_books = []

    # Find new and modified books
    for book_file in books_dir.rglob('*.epub'):
        book_path = str(book_file)

        if book_path not in indexed_books:
            # New book (never indexed)
            new_books.append(book_path)
        else:
            last_indexed = indexed_books[book_path]
            if last_indexed is None:
                # Book exists in metadata but never indexed
                modified_books.append(book_path)
            else:
                # Check if file was modified after last indexing
                file_mtime = get_file_mtime(book_path)
                if file_mtime > last_indexed:
                    modified_books.append(book_path)

    # Find deleted books (in metadata but not on filesystem)
    for book_path, last_indexed in indexed_books.items():
        if not Path(book_path).exists():
            deleted_books.append(book_path)

    return new_books, modified_books, deleted_books


def update_indexed_timestamp(metadata_file, book_filename, topic_id):
    """Update last_indexed_at timestamp for a specific book"""
    metadata_file = Path(metadata_file)

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    # Find and update book
    for topic in metadata['topics']:
        if topic['id'] == topic_id:
            for book in topic['books']:
                if book['filename'] == book_filename:
                    book['last_indexed_at'] = datetime.now().timestamp()
                    break

    # Write back
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    # Demo
    BOOKS_DIR = Path(__file__).parent.parent / 'books'
    METADATA_FILE = BOOKS_DIR / 'metadata.json'

    print("🔍 Delta Detection")
    print("=" * 50)

    new, modified, deleted = detect_changes(BOOKS_DIR, METADATA_FILE)

    print(f"\n📊 Results:")
    print(f"   New books: {len(new)}")
    print(f"   Modified books: {len(modified)}")
    print(f"   Deleted books: {len(deleted)}")

    if new:
        print(f"\n📚 New books:")
        for book in new[:5]:  # Show first 5
            print(f"   + {Path(book).name}")
        if len(new) > 5:
            print(f"   ... and {len(new) - 5} more")

    if modified:
        print(f"\n✏️  Modified books:")
        for book in modified[:5]:
            print(f"   ~ {Path(book).name}")
        if len(modified) > 5:
            print(f"   ... and {len(modified) - 5} more")

    if deleted:
        print(f"\n🗑️  Deleted books:")
        for book in deleted[:5]:
            print(f"   - {Path(book).name}")
        if len(deleted) > 5:
            print(f"   ... and {len(deleted) - 5} more")

    total_changes = len(new) + len(modified) + len(deleted)
    if total_changes == 0:
        print("\n✅ No changes detected - nothing to reindex!")
    else:
        print(f"\n⚡ Only need to reindex {len(new) + len(modified)} books (not all {len(new) + len(modified) + len(deleted)})!")
