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
print("✓ Using local embedding model: all-MiniLM-L6-v2 (384-dim)")

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"

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

for topic in metadata_json['topics']:
    topic_id = topic['id']
    topic_label = topic['label']
    topic_dir = BOOKS_DIR / topic_id

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

print(f"\n   Total: {len(all_documents)} document chunks")

# Create index
print("\n3. Building vector index...")
print("   This will take ~1-2 minutes with local embeddings...")

index = VectorStoreIndex.from_documents(all_documents, show_progress=True)

print("   ✓ Index built")

# Save index temporarily (needed for partitioning)
print("\n4. Saving to temporary storage...")
STORAGE_DIR.mkdir(exist_ok=True)
index.storage_context.persist(persist_dir=str(STORAGE_DIR))

# Partition by topic for lazy loading
print("\n5. Partitioning by topic for MCP optimization...")
import subprocess
partition_script = Path(__file__).parent / "partition_storage.py"
result = subprocess.run([sys.executable, str(partition_script)], capture_output=True, text=True)
if result.returncode == 0:
    print("   ✓ Storage partitioned by topic")

    # Clean up temporary monolithic files (now using partitioned storage)
    import os
    deprecated_files = [
        STORAGE_DIR / "default__vector_store.json",
        STORAGE_DIR / "docstore.json",
        STORAGE_DIR / "graph_store.json",
        STORAGE_DIR / "image__vector_store.json",
        STORAGE_DIR / "index_store.json"
    ]
    for f in deprecated_files:
        if f.exists():
            os.remove(f)
    print("   ✓ Cleaned up temporary files")
else:
    print(f"   ⚠️  Partitioning failed: {result.stderr}")

print("\n🎉 Indexing complete!")
print(f"   Documents: {len(all_documents):,}")
print(f"   Storage: {STORAGE_DIR}")
print(f"   Structure: topic-partitioned (lazy-loading ready)")
