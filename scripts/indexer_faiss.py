#!/usr/bin/env python3
"""
Build FAISS index with Gemini embeddings.
Fast binary storage, fast loading.
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import faiss
from dotenv import load_dotenv
import google.generativeai as genai
from llama_index.readers.file import EpubReader
from tqdm import tqdm

# Load environment
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found in .env")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"
INDEX_FILE = STORAGE_DIR / "faiss.index"
DOCSTORE_FILE = STORAGE_DIR / "docstore.json"

print("📚 Building FAISS index with Gemini embeddings")
print("=" * 60)

# Load metadata
print("\n1. Loading metadata...")
with open(METADATA_FILE, 'r') as f:
    metadata_json = json.load(f)

print(f"   Found {len(metadata_json['topics'])} topics")

# Load all documents
print("\n2. Loading books...")
all_documents = []
doc_metadata = []

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

        reader = EpubReader()
        try:
            docs = reader.load_data(str(book_path))

            # Split into chunks if needed
            for doc in docs:
                # Break into sentences/paragraphs if text is too long
                text = doc.text.strip()
                if len(text) < 100:  # Skip very short chunks
                    continue

                # Simple chunking: split by double newline (paragraphs)
                chunks = [chunk.strip() for chunk in text.split('\n\n') if len(chunk.strip()) > 100]

                for chunk in chunks:
                    all_documents.append(chunk)
                    doc_metadata.append({
                        'book_id': book['id'],
                        'book_title': book['title'],
                        'book_author': book['author'],
                        'topic_id': topic_id,
                        'topic_label': topic_label,
                        'tags': book['tags']
                    })

            print(f"         ✓ {len(chunks) if docs else 0} chunks")

        except Exception as e:
            print(f"         ❌ Error: {e}")

print(f"\n   Total: {len(all_documents)} chunks")

# Generate embeddings
print("\n3. Generating embeddings with Gemini...")
print("   This will take ~2-3 minutes...")

embeddings_list = []
batch_size = 100  # Gemini API limit

for i in tqdm(range(0, len(all_documents), batch_size), desc="   Embedding batches"):
    batch = all_documents[i:i+batch_size]

    # Gemini embedding API
    result = genai.embed_content(
        model="models/embedding-001",
        content=batch,
        task_type="retrieval_document"
    )

    embeddings_list.extend(result['embedding'])

embeddings = np.array(embeddings_list, dtype='float32')
print(f"   ✓ Generated {len(embeddings)} embeddings (768-dim)")

# Build FAISS index
print("\n4. Building FAISS index...")
dimension = embeddings.shape[1]  # 768 for Gemini
index = faiss.IndexFlatL2(dimension)  # L2 distance
index.add(embeddings)

print(f"   ✓ Index built with {index.ntotal:,} vectors")

# Save
print("\n5. Saving to storage...")

# Save FAISS index (binary, fast)
faiss.write_index(index, str(INDEX_FILE))
print(f"   ✓ FAISS index: {INDEX_FILE}")

# Save docstore (metadata for each chunk)
docstore = {}
for i, (text, meta) in enumerate(zip(all_documents, doc_metadata)):
    docstore[i] = {
        'text': text,
        'metadata': meta
    }

with open(DOCSTORE_FILE, 'w', encoding='utf-8') as f:
    json.dump(docstore, f, ensure_ascii=False, indent=2)

print(f"   ✓ Docstore: {DOCSTORE_FILE}")

print("\n🎉 Indexing complete!")
print(f"   Chunks: {len(all_documents)}")
print(f"   Storage: {STORAGE_DIR}")
