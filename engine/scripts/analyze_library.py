#!/usr/bin/env python3
"""Analyze library structure to find edge cases and validate architecture"""

import json
from pathlib import Path
from collections import defaultdict

BOOKS_DIR = Path(__file__).parent.parent / 'books'
METADATA_FILE = BOOKS_DIR / 'metadata.json'

with open(METADATA_FILE) as f:
    metadata = json.load(f)

print("=" * 60)
print("LIBRARY STRUCTURE ANALYSIS")
print("=" * 60)

# 1. Topic nesting patterns
print("\n1. TOPIC NESTING")
nested = [t for t in metadata['topics'] if '_' in t['id']]
root = [t for t in metadata['topics'] if '_' not in t['id']]
print(f"   Total topics: {len(metadata['topics'])}")
print(f"   Nested (with /): {len(nested)}")
print(f"   Root-level: {len(root)}")
print(f"\n   Root topics: {', '.join([t['id'] for t in root])}")

# 2. File format distribution
print("\n2. FILE FORMATS")
epub_topics = []
pdf_topics = []
mixed_topics = []

for topic in metadata['topics']:
    files = [b['filename'] for b in topic['books']]
    has_epub = any(f.endswith('.epub') for f in files)
    has_pdf = any(f.endswith('.pdf') for f in files)

    if has_epub and has_pdf:
        mixed_topics.append(topic['id'])
    elif has_epub:
        epub_topics.append(topic['id'])
    elif has_pdf:
        pdf_topics.append(topic['id'])

print(f"   EPUB only: {len(epub_topics)}")
print(f"   PDF only: {len(pdf_topics)}")
print(f"   Mixed (EPUB+PDF): {len(mixed_topics)}")
if mixed_topics:
    print(f"\n   Mixed topics: {', '.join(mixed_topics[:5])}")
    if len(mixed_topics) > 5:
        print(f"   ... and {len(mixed_topics) - 5} more")

# 3. Books per topic distribution
print("\n3. BOOKS PER TOPIC")
book_counts = [len(t['books']) for t in metadata['topics']]
print(f"   Min: {min(book_counts)} books")
print(f"   Max: {max(book_counts)} books")
print(f"   Avg: {sum(book_counts) / len(book_counts):.1f} books")

# Find outliers
large_topics = [(t['id'], len(t['books'])) for t in metadata['topics'] if len(t['books']) > 10]
small_topics = [(t['id'], len(t['books'])) for t in metadata['topics'] if len(t['books']) == 1]
print(f"\n   Topics with >10 books: {len(large_topics)}")
if large_topics:
    for tid, count in sorted(large_topics, key=lambda x: x[1], reverse=True)[:3]:
        print(f"     - {tid}: {count} books")
print(f"\n   Topics with 1 book: {len(small_topics)}")
if small_topics[:3]:
    print(f"     Examples: {', '.join([t[0] for t in small_topics[:3]])}")

# 4. Existing index files
print("\n4. EXISTING INDEX FILES")
topics_with_faiss = []
topics_with_chunks = []

for topic in metadata['topics']:
    folder_path = topic.get('folder_path', topic['label'])
    topic_dir = BOOKS_DIR / folder_path

    if (topic_dir / '.faiss.index').exists():
        topics_with_faiss.append(topic['id'])
    if (topic_dir / '.chunks.json').exists():
        topics_with_chunks.append(topic['id'])

print(f"   Topics with faiss.index: {len(topics_with_faiss)}/{len(metadata['topics'])}")
print(f"   Topics with chunks.json: {len(topics_with_chunks)}/{len(metadata['topics'])}")

# 5. Metadata fields consistency
print("\n5. METADATA COMPLETENESS")
has_folder_path = [t for t in metadata['topics'] if 'folder_path' in t]
has_description = [t for t in metadata['topics'] if 'description' in t and t['description']]
print(f"   Topics with 'folder_path': {len(has_folder_path)}/{len(metadata['topics'])}")
print(f"   Topics with 'description': {len(has_description)}/{len(metadata['topics'])}")

# Check book metadata
all_books = [b for t in metadata['topics'] for b in t['books']]
has_tags = [b for b in all_books if b.get('tags')]
has_year = [b for b in all_books if b.get('year')]
print(f"\n   Books with tags: {len(has_tags)}/{len(all_books)}")
print(f"   Books with year: {len(has_year)}/{len(all_books)}")

# 6. Filesystem vs metadata discrepancies
print("\n6. FILESYSTEM VALIDATION")
missing_folders = []
missing_files = []

for topic in metadata['topics']:
    folder_path = topic.get('folder_path', topic['label'])
    topic_dir = BOOKS_DIR / folder_path

    if not topic_dir.exists():
        missing_folders.append(topic['id'])
        continue

    for book in topic['books']:
        book_path = topic_dir / book['filename']
        if not book_path.exists():
            missing_files.append(f"{topic['id']}/{book['filename']}")

print(f"   Missing topic folders: {len(missing_folders)}")
if missing_folders:
    print(f"     {', '.join(missing_folders[:5])}")
print(f"   Missing book files: {len(missing_files)}")
if missing_files:
    print(f"     {missing_files[0]}")
    if len(missing_files) > 1:
        print(f"     ... and {len(missing_files) - 1} more")

# 7. EDGE CASES TO TEST
print("\n" + "=" * 60)
print("RECOMMENDED TEST TOPICS")
print("=" * 60)

recommendations = []

# Small topic (fast to test)
if small_topics:
    recommendations.append(("Small topic (1 book, fast test)", small_topics[0][0]))

# Root-level topic
if root:
    recommendations.append(("Root-level topic (no nesting)", root[0]['id']))

# Nested topic
if nested:
    recommendations.append(("Nested topic (subfolder)", nested[0]['id']))

# Mixed formats
if mixed_topics:
    recommendations.append(("Mixed EPUB+PDF", mixed_topics[0]))

# Large topic (stress test)
if large_topics:
    recommendations.append(("Large topic (stress test)", large_topics[0][0]))

for i, (reason, topic_id) in enumerate(recommendations, 1):
    topic = [t for t in metadata['topics'] if t['id'] == topic_id][0]
    folder_path = topic.get('folder_path', topic['label'])
    book_count = len(topic['books'])
    print(f"\n{i}. {reason}")
    print(f"   Topic ID: {topic_id}")
    print(f"   Path: books/{folder_path}/")
    print(f"   Books: {book_count}")

print("\n" + "=" * 60)
