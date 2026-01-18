#!/usr/bin/env python3
"""
Reindex ALL topics at once (loads model once, reuses for all topics)
Prevents memory crashes from loading MPNet 23 times
"""

import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from llama_index.readers.file import EpubReader, PyMuPDFReader
import warnings
import logging

# Suppress MuPDF ICC profile warnings (cosmetic errors, don't affect text extraction)
warnings.filterwarnings("ignore")
logging.getLogger("fitz").setLevel(logging.ERROR)

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
METADATA_FILE = BOOKS_DIR / "metadata.json"
MODELS_DIR = Path(__file__).parent.parent / "models"

# Setup embeddings ONCE
import os
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(MODELS_DIR)

print("Loading MiniLM model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(f"✅ Model loaded (dim: {model.get_sentence_embedding_dimension()})\n")

# Load metadata
with open(METADATA_FILE, 'r') as f:
    metadata = json.load(f)

# Readers
epub_reader = EpubReader()
pdf_reader = PyMuPDFReader()

print(f"📚 Reindexing {len(metadata['topics'])} topics...\n")

for i, topic_data in enumerate(metadata['topics'], 1):
    topic_id = topic_data['id']
    topic_label = topic_data['label']
    topic_dir = BOOKS_DIR / topic_label

    print(f"[{i}/{len(metadata['topics'])}] 🔄 {topic_label} ({len(topic_data['books'])} books)")

    # Load books for this topic
    documents = []

    for book in topic_data['books']:
        book_path = topic_dir / book['filename']

        if not book_path.exists():
            print(f"  ⚠️  Skipping {book['filename']} (not found)")
            continue

        try:
            # Detect file type
            file_ext = book_path.suffix.lower()

            if file_ext == '.epub':
                docs = epub_reader.load_data(str(book_path))
            elif file_ext == '.pdf':
                docs = pdf_reader.load_data(str(book_path))
            else:
                print(f"  ⚠️  Unsupported: {file_ext}")
                continue

            # Add metadata
            for doc in docs:
                doc.metadata = {
                    'book_id': book['id'],
                    'book_title': book['title'],
                    'book_author': book['author'],
                    'topic_id': topic_id,
                    'topic_label': topic_label,
                    'tags': ','.join(book['tags'])
                }

            documents.extend(docs)

        except Exception as e:
            print(f"  ⚠️  Error loading {book['filename']}: {e}")

    if not documents:
        print(f"  ❌ No documents loaded\n")
        continue

    print(f"  📝 Generating embeddings for {len(documents)} chunks...")

    # Generate embeddings
    texts = [doc.text for doc in documents]
    embeddings_list = model.encode(texts, show_progress_bar=False, batch_size=32)

    # Store chunks with metadata
    chunks_list = []
    for i, doc in enumerate(documents):
        chunks_list.append({
            'chunk_full': doc.text,
            'book_id': doc.metadata.get('book_id'),
            'book_title': doc.metadata.get('book_title'),
            'book_author': doc.metadata.get('book_author'),
            'topic_id': doc.metadata.get('topic_id'),
            'topic_label': doc.metadata.get('topic_label'),
            'chunk_index': i
        })

    # Build FAISS index
    embeddings_array = np.array(embeddings_list, dtype=np.float32)
    dimension = embeddings_array.shape[1]

    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings_array)

    # Save to topic folder
    index_file = topic_dir / "faiss.index"
    chunks_file = topic_dir / "chunks.json"

    faiss.write_index(faiss_index, str(index_file))

    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_list, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {len(documents)} chunks indexed → {index_file.name}\n")

print("🎉 All topics reindexed!")
