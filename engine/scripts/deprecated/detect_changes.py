#!/usr/bin/env python3
"""
Delta detection: Compare filesystem vs library-index.json (v2) to find changed books
Only reindex what's actually changed (massive time savings)

V2 Structure:
- library-index.json: Registry of all topics
- books/<topic>/topic-index.json: Per-topic book metadata with last_modified timestamps
"""

import json
import os
from pathlib import Path
from datetime import datetime


def get_file_mtime(filepath):
    """Get file modification time as Unix timestamp"""
    return os.path.getmtime(filepath)


def detect_changes(books_dir, library_index_file):
    """
    Compare filesystem state vs library-index.json (v2 schema)
    Returns: (new_books, modified_books, deleted_books)

    V2 structure:
    - library-index.json: Registry of topics
    - books/<topic>/topic-index.json: Per-topic book metadata
    """
    books_dir = Path(books_dir)
    library_index_file = Path(library_index_file)

    # Load library registry
    if library_index_file.exists():
        with open(library_index_file, 'r') as f:
            registry = json.load(f)
    else:
        print(f"⚠️  No library-index.json found")
        registry = {'topics': []}

    # Build lookup: book_path -> last_modified from topic-index.json files
    indexed_books = {}

    for topic in registry.get('topics', []):
        topic_path = topic['path']
        topic_dir = books_dir / topic_path
        topic_index = topic_dir / 'topic-index.json'

        if topic_index.exists():
            with open(topic_index, 'r') as f:
                topic_data = json.load(f)

            for book in topic_data.get('books', []):
                book_path = topic_dir / book['filename']
                last_modified = book.get('last_modified')
                indexed_books[str(book_path)] = last_modified

    # Scan filesystem for .epub and .pdf files
    new_books = []
    modified_books = []
    deleted_books = []

    # Find new and modified books
    for ext in ['*.epub', '*.pdf']:
        for book_file in books_dir.rglob(ext):
            # Skip index files and hidden files
            if book_file.name.startswith('.') or 'topic-index' in book_file.name:
                continue

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
    LIBRARY_INDEX = BOOKS_DIR / 'library-index.json'

    print("🔍 Delta Detection (v2)")
    print("=" * 50)

    new, modified, deleted = detect_changes(BOOKS_DIR, LIBRARY_INDEX)

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
