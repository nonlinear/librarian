#!/usr/bin/env python3
"""
Reindex ALL topics or specific topic (loads model once)
Usage:
  python3.11 reindex_all.py              # All topics
  python3.11 reindex_all.py --topic cooking
"""

import argparse
import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from llama_index.core import Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import EpubReader, PyMuPDFReader
import warnings
import logging

# Suppress MuPDF ICC profile warnings (cosmetic errors, don't affect text extraction)
warnings.filterwarnings("ignore")
logging.getLogger("fitz").setLevel(logging.ERROR)

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
LIBRARY_INDEX = BOOKS_DIR / "library-index.json"
MODELS_DIR = Path(__file__).parent.parent / "models"

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument('--topic', help='Topic folder (e.g. theory/anthropocene)')
args = parser.parse_args()

# Setup embeddings ONCE
import os
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(MODELS_DIR)

print("Loading MiniLM model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(f"✅ Model loaded (dim: {model.get_sentence_embedding_dimension()})")

# Setup chunking
Settings.chunk_size = 1024
Settings.chunk_overlap = 200
node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
print(f"✅ Chunking: 1024 chars, 200 overlap\n")

# Load library
with open(LIBRARY_INDEX, 'r') as f:
    library = json.load(f)

# Filter topics
topics = library['topics']
if args.topic:
    topics = [t for t in topics if t['path'] == args.topic]
    if not topics:
        print(f"❌ Topic '{args.topic}' not found")
        exit(1)

print(f"📚 Reindexing {len(topics)} topic(s)...\n")

# Readers
epub_reader = EpubReader()
pdf_reader = PyMuPDFReader()

for i, topic_meta in enumerate(topics, 1):
    topic_id = topic_meta['id']
    topic_folder = topic_meta['path']
    topic_dir = BOOKS_DIR / topic_folder

    # Load topic-index.json
    with open(topic_dir / 'topic-index.json') as f:
        topic_data = json.load(f)

    print(f"[{i}/{len(topics)}] 🔄 {topic_folder} ({len(topic_data['books'])} books)")

    # Load books for this topic
    raw_documents = []

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

            # Add metadata to raw documents
            for doc in docs:
                doc.metadata = {
                    'book_id': book['id'],
                    'book_title': book['title'],
                    'book_author': book.get('author', 'Unknown'),
                    'topic_id': topic_id,
                    'topic_folder': topic_folder,
                    'tags': ','.join(book.get('tags', []))
                }

            raw_documents.extend(docs)

        except Exception as e:
            print(f"  ⚠️  Error loading {book['filename']}: {e}")

    if not raw_documents:
        print(f"  ❌ No documents loaded\n")
        continue

    # Apply chunking to raw documents
    print(f"  ✂️  Chunking {len(raw_documents)} raw docs...")
    nodes = node_parser.get_nodes_from_documents(raw_documents)
    print(f"  📝 Generated {len(nodes)} chunks")

    if not nodes:
        print(f"  ❌ No chunks generated\n")
        continue

    if not nodes:
        print(f"  ❌ No chunks generated\n")
        continue

    # Generate embeddings from nodes
    print(f"  🔢 Generating embeddings...")
    texts = [node.text for node in nodes]
    embeddings_list = model.encode(texts, show_progress_bar=False, batch_size=32)

    # Store chunks with metadata
    chunks_list = []
    for i, node in enumerate(nodes):
        chunks_list.append({
            'chunk_full': node.text,
            'book_id': node.metadata.get('book_id'),
            'book_title': node.metadata.get('book_title'),
            'book_author': node.metadata.get('book_author'),
            'topic_id': node.metadata.get('topic_id'),
            'topic_folder': node.metadata.get('topic_folder'),
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

    print(f"  ✅ {len(nodes)} chunks indexed → {index_file.name}\n")

print("🎉 All topics reindexed!")
