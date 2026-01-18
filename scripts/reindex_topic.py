#!/usr/bin/env python3
"""
Reindex a single topic (for auto-recovery when indices are missing)
Usage: python3.11 scripts/reindex_topic.py <topic_id>
"""

import sys
import json
from pathlib import Path
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import EpubReader, PyMuPDFReader

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
METADATA_FILE = BOOKS_DIR / "metadata.json"
MODELS_DIR = Path(__file__).parent.parent / "models"

# Setup embeddings
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder=str(MODELS_DIR)
)
Settings.embed_model = embed_model

def reindex_topic(topic_id: str):
    """Reindex a single topic."""

    # Load metadata
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    # Find topic
    topic_data = None
    for topic in metadata['topics']:
        if topic['id'] == topic_id:
            topic_data = topic
            break

    if not topic_data:
        print(f"❌ Topic {topic_id} not found in metadata")
        return False

    topic_label = topic_data['label']
    topic_dir = BOOKS_DIR / topic_label

    print(f"📚 Reindexing topic: {topic_label}")

    # Load books for this topic
    documents = []
    epub_reader = EpubReader()
    pdf_reader = PyMuPDFReader()

    for book in topic_data['books']:
        book_path = topic_dir / book['filename']

        if not book_path.exists():
            print(f"  ⚠️  Skipping {book['filename']} (not found)")
            continue

        print(f"  Loading: {book['title']}")

        try:
            # Detect file type and use appropriate reader
            file_ext = book_path.suffix.lower()

            if file_ext == '.epub':
                docs = epub_reader.load_data(str(book_path))
            elif file_ext == '.pdf':
                docs = pdf_reader.load_data(str(book_path))
            else:
                print(f"    ⚠️  Unsupported format: {file_ext}")
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
            print(f"    ✓ {len(docs)} chunks")

        except Exception as e:
            print(f"    ⚠️  Error: {e}")

    if not documents:
        print(f"❌ No documents loaded for {topic_label}")
        return False

    print(f"\n  Building index for {len(documents)} chunks...")

    # Build index
    index = VectorStoreIndex.from_documents(documents)

    # Extract embeddings and chunks
    embeddings = []
    chunks = []

    for doc in documents:
        # Get embedding
        embedding = embed_model.get_text_embedding(doc.text)
        embeddings.append(embedding)

        # Store chunk info
        chunks.append({
            'text': doc.text,
            'metadata': doc.metadata
        })

    # Create FAISS index
    embeddings_array = np.array(embeddings, dtype=np.float32)
    dimension = embeddings_array.shape[1]

    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings_array)

    # Save files
    faiss_file = topic_dir / "faiss.index"
    chunks_file = topic_dir / "chunks.pkl"

    faiss.write_index(faiss_index, str(faiss_file))

    with open(chunks_file, 'wb') as f:
        pickle.dump(chunks, f)

    print(f"\n✅ Rebuilt {topic_label}")
    print(f"   FAISS: {faiss_file}")
    print(f"   Chunks: {chunks_file}")
    print(f"   Total: {len(chunks)} chunks")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3.11 scripts/reindex_topic.py <topic_id>")
        sys.exit(1)

    topic_id = sys.argv[1]
    success = reindex_topic(topic_id)

    sys.exit(0 if success else 1)
