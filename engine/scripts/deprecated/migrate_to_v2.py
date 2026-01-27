#!/usr/bin/env python3
"""
Migrate metadata from v1.0 (monolithic) to v2.0 (per-topic)

Usage:
    python migrate_to_v2.py [--dry-run]

What it does:
1. Reads monolithic books/metadata.json
2. Creates per-topic .metadata.json files
3. Updates main metadata.json to registry format
4. Validates topic XOR rule (books OR subtopics, never both)
"""

import json
import os
import hashlib
from pathlib import Path
from collections import defaultdict
import argparse

# Paths
LIBRARY_ROOT = Path(__file__).parent.parent / "books"
MAIN_METADATA = LIBRARY_ROOT / ".library-index.json"


def slugify(text):
    """Convert text to slug (lowercase, underscores)"""
    return text.lower().replace(' ', '_').replace('/', '_')


def compute_content_hash(topic_path):
    """Hash folder contents: filenames + mtimes for delta detection"""
    if not topic_path.exists():
        return None

    files = sorted([
        f for f in os.listdir(topic_path)
        if f.endswith(('.pdf', '.epub'))
    ])

    if not files:
        return None

    hash_input = []
    for filename in files:
        filepath = topic_path / filename
        try:
            mtime = os.path.getmtime(filepath)
            hash_input.append(f"{filename}:{mtime}")
        except OSError:
            continue

    if not hash_input:
        return None

    combined = '|'.join(hash_input)
    return hashlib.sha256(combined.encode()).hexdigest()


def find_topic_path(topic_data):
    """
    Resolve topic path from topic data

    Priority:
    1. Use 'path' field (v2.0 format - may exist from partial migration)
    2. Use 'folder_path' field (v1.0 format)
    3. Try nested ID path (ai_policy → AI/policy/)
    4. Scan filesystem for matching folder
    """
    topic_id = topic_data['id']
    topic_label = topic_data.get('label', topic_id)

    # 1. Use path if present (v2.0 format)
    if 'path' in topic_data:
        return Path(topic_data['path'])

    # 2. Use folder_path if present (v1.0 format)
    if 'folder_path' in topic_data:
        return Path(topic_data['folder_path'])

    # 3. Try nested path (e.g., ai_policy → AI/policy/)
    if '_' in topic_id:
        nested_path = LIBRARY_ROOT / topic_id.replace('_', '/')
        if nested_path.exists():
            return nested_path.relative_to(LIBRARY_ROOT)

    # 4. Try label path (may have spaces)
    label_path = LIBRARY_ROOT / topic_label
    if label_path.exists():
        return label_path.relative_to(LIBRARY_ROOT)

    # 5. Fallback: convert ID to path
    return Path(topic_id.replace('_', '/'))


def validate_topic_xor(topic_path):
    """
    Validate topic XOR rule: folder has books OR subtopics, never both

    Returns:
        tuple: (has_books: bool, has_subtopics: bool, is_valid: bool)
    """
    if not topic_path.exists():
        return (False, False, False)

    books = list(topic_path.glob('*.epub')) + list(topic_path.glob('*.pdf'))
    subdirs = [d for d in topic_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

    has_books = len(books) > 0
    has_subtopics = len(subdirs) > 0

    # Valid if XOR: (books AND NOT subtopics) OR (subtopics AND NOT books)
    is_valid = has_books != has_subtopics  # XOR

    return (has_books, has_subtopics, is_valid)


def migrate_to_v2(dry_run=False):
    """
    Migrate metadata from v1.0 to v2.0

    Args:
        dry_run: If True, only validate and show what would be done
    """
    print("=" * 60)
    print("📦 Metadata Migration: v1.0 → v2.0")
    print("=" * 60)

    # 1. Load monolithic metadata
    print("\n1. Loading monolithic metadata...")

    if not MAIN_METADATA.exists():
        print(f"   ❌ Not found: {MAIN_METADATA}")
        return False

    with open(MAIN_METADATA, 'r') as f:
        old_metadata = json.load(f)

    topics_count = len(old_metadata['topics'])
    books_count = sum(len(t.get('books', [])) for t in old_metadata['topics'])

    print(f"   ✓ Found: {topics_count} topics, {books_count} books")

    # 2. Validate topics and build registry
    print("\n2. Validating topic structure...")

    registry_topics = []
    per_topic_metadata = {}
    validation_errors = []

    for topic in old_metadata['topics']:
        topic_id = topic['id']
        topic_label = topic.get('label', topic_id)

        # Resolve topic path
        topic_rel_path = find_topic_path(topic)
        topic_abs_path = LIBRARY_ROOT / topic_rel_path

        # Validate XOR rule
        has_books, has_subtopics, is_valid = validate_topic_xor(topic_abs_path)

        if not is_valid:
            error_msg = f"   ❌ {topic_id}: XOR violation (books={has_books}, subtopics={has_subtopics})"
            validation_errors.append(error_msg)
            print(error_msg)
            continue

        # Skip parent topics (they have subtopics, not books)
        if has_subtopics:
            print(f"   ↪ {topic_id}: Parent topic (has {len(list(topic_abs_path.iterdir()))} subtopics)")
            continue

        # Leaf topic: create per-topic metadata
        if has_books:
            # Get books from old metadata if available
            old_books = topic.get('books', [])

            # If no books in metadata, scan filesystem
            if not old_books:
                print(f"   ⚠️  {topic_id}: Scanning filesystem (no metadata books)")
                book_files = list(topic_abs_path.glob('*.epub')) + list(topic_abs_path.glob('*.pdf'))
                old_books = []
                for book_file in book_files:
                    # Generate minimal book metadata
                    filename = book_file.name
                    book_id = slugify(book_file.stem)
                    old_books.append({
                        'id': book_id,
                        'title': book_file.stem,
                        'author': 'Unknown',
                        'year': None,
                        'tags': [],
                        'filename': filename
                    })

            num_books = len(old_books)
            print(f"   ✓ {topic_id}: Leaf topic ({num_books} books)")

            # Compute content hash
            content_hash = compute_content_hash(topic_abs_path)

            # Build per-topic metadata
            per_topic_metadata[topic_id] = {
                "schema_version": "2.0",
                "topic_id": topic_id,
                "embedding_model": old_metadata.get('embedding_model', 'all-MiniLM-L6-v2'),
                "chunk_settings": old_metadata.get('chunk_settings', {
                    "size": 1024,
                    "overlap": 200
                }),
                "last_indexed_at": None,  # Will be set on reindexing
                "content_hash": content_hash,
                "books": []
            }

            # Add books with filetype detection
            for book in old_books:
                filename = book['filename']
                filetype = 'pdf' if filename.endswith('.pdf') else 'epub'

                book_path = topic_abs_path / filename
                last_modified = None
                if book_path.exists():
                    last_modified = os.path.getmtime(book_path)

                per_topic_metadata[topic_id]['books'].append({
                    "id": book['id'],
                    "title": book['title'],
                    "author": book.get('author', 'Unknown'),
                    "year": book.get('year'),
                    "tags": book.get('tags', []),
                    "filename": filename,
                    "filetype": filetype,
                    "last_modified": last_modified
                })

            # Add to registry
            registry_topics.append({
                "id": topic_id,
                "path": str(topic_rel_path)
            })

    if validation_errors:
        print(f"\n   ⚠️  {len(validation_errors)} topics have XOR violations")
        print("   Fix these manually before migrating")
        return False

    print(f"\n   ✓ Validated: {len(registry_topics)} leaf topics")

    # 3. Write per-topic metadata files
    print("\n3. Writing per-topic metadata...")

    if dry_run:
        print("   [DRY RUN] Would create:")

    for topic_id, metadata in per_topic_metadata.items():
        # Find topic data to get path
        topic_data = next(t for t in old_metadata['topics'] if t['id'] == topic_id)
        topic_path = LIBRARY_ROOT / find_topic_path(topic_data)
        metadata_file = topic_path / ".topic-index.json"

        if dry_run:
            print(f"   • {metadata_file.relative_to(LIBRARY_ROOT.parent)}")
        else:
            metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"   ✓ {metadata_file.relative_to(LIBRARY_ROOT.parent)}")

    # 4. Update main metadata to registry format
    print("\n4. Updating main metadata.json...")

    new_main_metadata = {
        "schema_version": "2.0",
        "library_path": str(LIBRARY_ROOT.absolute()),
        "embedding_model": old_metadata.get('embedding_model', 'all-MiniLM-L6-v2'),
        "chunk_settings": old_metadata.get('chunk_settings', {
            "size": 1024,
            "overlap": 200
        }),
        "topics": sorted(registry_topics, key=lambda t: t['id'])
    }

    if dry_run:
        print("   [DRY RUN] Would update:")
        print(f"   • {MAIN_METADATA.relative_to(LIBRARY_ROOT.parent)}")
        print(f"   • Topics: {len(registry_topics)}")
        print(f"   • Size: ~{len(json.dumps(new_main_metadata, indent=2))} bytes")
    else:
        # Backup old metadata
        backup_file = MAIN_METADATA.with_suffix('.json.v1.backup')
        with open(backup_file, 'w') as f:
            json.dump(old_metadata, f, indent=2)
        print(f"   ✓ Backed up: {backup_file.name}")

        # Write new metadata
        with open(MAIN_METADATA, 'w') as f:
            json.dump(new_main_metadata, f, indent=2)
        print(f"   ✓ Updated: {MAIN_METADATA.name}")
        print(f"   • Topics: {len(registry_topics)}")
        print(f"   • Size: {len(json.dumps(new_main_metadata, indent=2)):,} bytes (was {len(json.dumps(old_metadata, indent=2)):,})")

    # 5. Summary
    print("\n" + "=" * 60)
    print("✅ Migration complete!" if not dry_run else "✅ Dry run complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   • Leaf topics: {len(per_topic_metadata)}")
    print(f"   • Total books: {sum(len(m['books']) for m in per_topic_metadata.values())}")
    print(f"   • Registry topics: {len(registry_topics)}")

    if dry_run:
        print(f"\n💡 Run without --dry-run to apply changes")
    else:
        print(f"\n⚠️  Next steps:")
        print(f"   1. Verify per-topic .metadata.json files")
        print(f"   2. Reindex all topics with updated indexer.py")
        print(f"   3. Test MCP server with new metadata structure")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Migrate metadata from v1.0 to v2.0')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    args = parser.parse_args()

    success = migrate_to_v2(dry_run=args.dry_run)
    exit(0 if success else 1)
