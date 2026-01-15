#!/usr/bin/env python3
"""
Index books using LlamaIndex + Gemini embeddings
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings, Document
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.readers.file import EpubReader

# Load environment
ENV_PATH = Path(__file__).parent.parent / ".env"
if not ENV_PATH.exists():
    ENV_PATH = Path.home() / "Documents/notes/.env"
load_dotenv(dotenv_path=ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found in .env")
    sys.exit(1)

# Setup embeddings
embed_model = GoogleGenAIEmbedding(
    model_name="models/embedding-001",
    api_key=GOOGLE_API_KEY
)
Settings.embed_model = embed_model

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"

print("📚 Indexing books with LlamaIndex + Gemini")
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
print("   This will take ~2-3 minutes with Gemini API...")

index = VectorStoreIndex.from_documents(all_documents, show_progress=True)

print("   ✓ Index built")

# Save index
print("\n4. Saving to storage...")
STORAGE_DIR.mkdir(exist_ok=True)
index.storage_context.persist(persist_dir=str(STORAGE_DIR))

print(f"   ✓ Saved to {STORAGE_DIR}")

print("\n🎉 Indexing complete!")
print(f"   Documents: {len(all_documents):,}")
print(f"   Storage: {STORAGE_DIR}")
