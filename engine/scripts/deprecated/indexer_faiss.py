#!/usr/bin/env python3
"""
Index books into FAISS vector store.

This script:
1. Reads metadata.json for book inventory
2. Loads EPUBs and chunks content
3. Generates embeddings (all-MiniLM-L6-v2)
4. Builds FAISS index (optimized for M3)
5. Persists index + docstore to storage/

Optimizations:
- Small chunks (512 tokens) for low latency
- Batch embedding generation
- IndexFlatL2 for maximum speed on ARM
- Minimal memory footprint
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import hashlib


# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"
INDEX_FILE = STORAGE_DIR / "faiss.index"
DOCSTORE_FILE = STORAGE_DIR / "docstore.json"

# Chunking settings (optimized for latency)
CHUNK_SIZE = 512  # tokens (approx 2048 chars)
CHUNK_OVERLAP = 64  # token overlap

# Embedding settings
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
EMBEDDING_DIM = 384  # MiniLM dimension
BATCH_SIZE = 32  # Batch size for embedding generation


class Timer:
    """Simple timer for performance tracking."""
    def __init__(self, name: str):
        self.name = name
        self.start = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        print(f"   ⏱️  {self.name}: {elapsed:.2f}s")


def load_metadata() -> Dict:
    """Load metadata.json."""
    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"metadata.json not found. Run generate_metadata.py first."
        )

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_text_from_epub(epub_path: Path) -> str:
    """Extract all text from EPUB."""
    try:
        book = epub.read_epub(str(epub_path))
        text_parts = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            if text:
                text_parts.append(text)

        return '\n\n'.join(text_parts)

    except Exception as e:
        print(f"   ⚠️  Error reading EPUB: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.

    Simple character-based chunking (not token-aware, but fast).
    Approximation: 1 token ≈ 4 chars.
    """
    char_chunk_size = chunk_size * 4
    char_overlap = overlap * 4

    chunks = []
    start = 0

    while start < len(text):
        end = start + char_chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += (char_chunk_size - char_overlap)

    return chunks


def generate_chunk_id(book_id: str, chunk_index: int, chunk_text: str) -> str:
    """Generate unique ID for chunk."""
    # Hash-based ID for deduplication
    text_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
    return f"{book_id}::{chunk_index:04d}::{text_hash}"


def index_books(metadata: Dict, model: SentenceTransformer) -> Tuple[faiss.Index, Dict]:
    """
    Index all books into FAISS.

    Returns:
        - FAISS index
        - Docstore (chunk_id -> metadata)
    """
    print(f"\n📊 Starting indexing...")
    print(f"   Embedding model: {EMBEDDING_MODEL}")
    print(f"   Chunk size: {CHUNK_SIZE} tokens (~{CHUNK_SIZE * 4} chars)")
    print(f"   Batch size: {BATCH_SIZE}")
    print()

    # Initialize FAISS index (IndexFlatL2 = exact search, fastest on M3)
    index = faiss.IndexFlatL2(EMBEDDING_DIM)

    # Docstore: maps FAISS index position to chunk metadata
    docstore = {}
    current_idx = 0

    total_books = sum(len(topic['books']) for topic in metadata['topics'])
    processed = 0

    for topic in metadata['topics']:
        topic_id = topic['id']
        topic_label = topic['label']

        for book in topic['books']:
            processed += 1
            book_id = book['id']
            book_title = book['title']
            book_author = book['author']
            filename = book['filename']

            print(f"📚 [{processed}/{total_books}] {topic_label}/{book_title}")

            # Load EPUB
            epub_path = BOOKS_DIR / topic_label / filename

            if not epub_path.exists():
                print(f"   ⚠️  File not found: {epub_path}")
                continue

            with Timer("Extract text"):
                text = extract_text_from_epub(epub_path)

            if not text:
                print(f"   ⚠️  No text extracted")
                continue

            # Chunk text
            with Timer("Chunk text"):
                chunks = chunk_text(text)

            print(f"   📄 Generated {len(chunks)} chunks")

            if not chunks:
                continue

            # Generate embeddings (batched for speed)
            with Timer("Generate embeddings"):
                embeddings = model.encode(
                    chunks,
                    batch_size=BATCH_SIZE,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )

            # Add to FAISS index
            index.add(embeddings.astype('float32'))

            # Store chunk metadata
            for i, chunk in enumerate(chunks):
                chunk_id = generate_chunk_id(book_id, i, chunk)

                docstore[current_idx] = {
                    'chunk_id': chunk_id,
                    'book_id': book_id,
                    'book_title': book_title,
                    'book_author': book_author,
                    'topic_id': topic_id,
                    'topic_label': topic_label,
                    'chunk_index': i,
                    'chunk_text': chunk[:500] + '...' if len(chunk) > 500 else chunk,  # Preview only
                    'chunk_full': chunk  # Full text for retrieval
                }

                current_idx += 1

            print(f"   ✅ Indexed {len(chunks)} chunks (total: {current_idx})")
            print()

    return index, docstore


def save_index(index: faiss.Index, docstore: Dict):
    """Persist FAISS index and docstore."""
    print(f"💾 Saving index to {STORAGE_DIR}/")

    # Save FAISS index (binary format)
    faiss.write_index(index, str(INDEX_FILE))
    print(f"   ✅ FAISS index: {INDEX_FILE.name} ({INDEX_FILE.stat().st_size / 1024 / 1024:.2f} MB)")

    # Save docstore (JSON)
    # Convert int keys to strings for JSON compatibility
    docstore_json = {str(k): v for k, v in docstore.items()}

    with open(DOCSTORE_FILE, 'w', encoding='utf-8') as f:
        json.dump(docstore_json, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Docstore: {DOCSTORE_FILE.name} ({DOCSTORE_FILE.stat().st_size / 1024 / 1024:.2f} MB)")


def main():
    """Main indexing workflow."""
    print("🔨 Librarian MCP - Indexer")
    print("=" * 50)

    # Load metadata
    print(f"\n📖 Loading metadata from {METADATA_FILE}")
    metadata = load_metadata()

    total_books = sum(len(topic['books']) for topic in metadata['topics'])
    print(f"   Topics: {len(metadata['topics'])}")
    print(f"   Books: {total_books}")

    # Load embedding model
    print(f"\n🤖 Loading embedding model: {EMBEDDING_MODEL}")
    with Timer("Model load"):
        model = SentenceTransformer(EMBEDDING_MODEL)

    # Index all books
    start_time = time.time()
    index, docstore = index_books(metadata, model)

    # Save
    save_index(index, docstore)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n✅ Indexing complete!")
    print(f"   Total vectors: {index.ntotal}")
    print(f"   Total time: {elapsed:.2f}s ({elapsed/total_books:.2f}s per book)")
    print(f"   Storage: {STORAGE_DIR}/")


if __name__ == "__main__":
    main()
