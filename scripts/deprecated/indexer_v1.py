#!/usr/bin/env python3
"""
Index books using LlamaIndex + local sentence-transformers embeddings
Auto-partitions by topic for MCP lazy-loading optimization
"""

import os
import sys
import json
import subprocess
from pathlib import Path

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import EpubReader

# Setup local embeddings (384-dim, no API key needed)
MODELS_DIR = Path(__file__).parent.parent / "models"
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder=str(MODELS_DIR)
)
Settings.embed_model = embed_model
Settings.chunk_size = 1024
Settings.chunk_overlap = 200
print("✓ Using local embedding model: all-MiniLM-L6-v2 (384-dim)")
print("✓ Chunking: 1024 chars, 200 overlap")

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
METADATA_FILE = BOOKS_DIR / "metadata.json"

print("📚 Indexing books with local embeddings")
print("=" * 50)

# Load metadata
print("\n1. Loading metadata...")
with open(METADATA_FILE, 'r') as f:
    metadata_json = json.load(f)

print(f"   Found {len(metadata_json['topics'])} topics")

# Load all documents
print("\n2. Loading books...")
all_documents = []
failed_books = []

for topic in metadata_json['topics']:
    topic_id = topic['id']
    topic_label = topic['label']

    # Handle nested topics (e.g., cybersecurity_applied → cybersecurity/applied/)
    # AND root topics with underscores (e.g., product_architecture → product architecture/)
    if '_' in topic_id:
        # Try nested path first
        nested_path = BOOKS_DIR / topic_id.replace('_', '/')

        if nested_path.exists():
            topic_dir = nested_path
        else:
            # Not nested - use label (which may have spaces)
            topic_dir = BOOKS_DIR / topic_label
    else:
        topic_dir = BOOKS_DIR / topic_label

    print(f"\n   Topic: {topic_label}")

    for book in topic['books']:
        book_path = topic_dir / book['filename']

        if not book_path.exists():
            print(f"      ⚠️  Not found: {book['filename']}")
            continue

        print(f"      Loading: {book['title']}")

        # Load EPUB
        reader = EpubReader()
        try:
            docs = reader.load_data(str(book_path))

            # Add metadata to each document
            for doc in docs:
                doc.metadata = {
                    'book_id': book['id'],
                    'book_title': book['title'],
                    'book_author': book['author'],
                    'topic_id': topic_id,
                    'topic_label': topic_label,
                    'tags': ','.join(book['tags'])
                }

            all_documents.extend(docs)
            print(f"         ✓ Loaded {len(docs)} chunks")

        except Exception as e:
            print(f"         ❌ Error: {e}")
            failed_books.append({
                'topic': topic_label,
                'book': book['title'],
                'filename': book['filename'],
                'error': str(e)
            })

print(f"\n   Total: {len(all_documents)} document chunks")

# Create index
print("\n3. Building vector index...")
print("   This will take ~1-2 minutes with local embeddings...")

index = VectorStoreIndex.from_documents(all_documents, show_progress=True)

print("   ✓ Index built")

# Save index temporarily (needed for partitioning)
print("\n4. Saving to temporary storage...")
import tempfile
temp_dir = tempfile.mkdtemp()
index.storage_context.persist(persist_dir=temp_dir)

# Partition by topic for lazy loading
print("\n5. Partitioning by topic for MCP optimization...")
import subprocess
partition_script = Path(__file__).parent / "partition_storage.py"
result = subprocess.run([sys.executable, str(partition_script), temp_dir], capture_output=True, text=True)
if result.returncode == 0:
    print("   ✓ Storage partitioned by topic")

    # Clean up temporary directory
    import shutil
    shutil.rmtree(temp_dir)
    print("   ✓ Cleaned up temporary files")
else:
    print(f"   ⚠️  Partitioning failed: {result.stderr}")

print("\n🎉 Indexing complete!")
print(f"   Documents: {len(all_documents):,}")
print(f"   Storage: books/<topic>/")
print(f"   Structure: topic-partitioned (lazy-loading ready)")

# Save failed books log as markdown
if failed_books:
    failed_md = Path(__file__).parent.parent / "engine" / "docs" / "FAILED.md"
    failed_md.parent.mkdir(parents=True, exist_ok=True)

    # Group by topic
    from collections import defaultdict
    by_topic = defaultdict(list)
    for book in failed_books:
        by_topic[book['topic']].append(book)

    # Write markdown
    with open(failed_md, 'w') as f:
        f.write("# Failed Books\n\n")
        f.write(f"Books that could not be indexed ({len(failed_books)} total)\n\n")
        f.write("---\n\n")

        for topic in sorted(by_topic.keys()):
            f.write(f"## {topic}\n\n")
            for book in by_topic[topic]:
                book_path = f"books/{topic}/{book['filename']}"
                f.write(f"- **{book['book']}**\n")
                f.write(f"  - File: [{book['filename']}](../../{book_path})\n")
                f.write(f"  - Error: `{book['error']}`\n\n")

    print(f"\n⚠️  {len(failed_books)} book(s) failed to index")
    print(f"   See: {failed_md}")
