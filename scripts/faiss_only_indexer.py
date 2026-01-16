#!/usr/bin/env python3
"""
Pure FAISS Binary Indexer

Replaces JSON docstore with binary chunk storage for maximum performance.
No LlamaIndex dependency - direct FAISS + pickle storage.

Performance target: <1s load time (vs 12-30s with JSON)
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict
import time

import faiss
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai
import os

# Load environment
ENV_PATH = Path(__file__).parent.parent / ".env"
if not ENV_PATH.exists():
    ENV_PATH = Path.home() / "Documents/notes/.env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"
FAISS_INDEX_FILE = STORAGE_DIR / "faiss_binary.index"
CHUNKS_FILE = STORAGE_DIR / "chunks_binary.pkl"

# Gemini setup
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env")

genai.configure(api_key=GOOGLE_API_KEY)

# EPUB parsing
try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "ebooklib", "beautifulsoup4"])
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup


def extract_text_from_epub(epub_path: Path) -> str:
    """Extract clean text from EPUB file."""
    book = epub.read_epub(str(epub_path))
    text_parts = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        if text:
            text_parts.append(text)

    return '\n\n'.join(text_parts)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) < 100:  # Skip very small chunks
            continue
        chunks.append(' '.join(chunk_words))

    return chunks


def get_embedding(text: str) -> np.ndarray:
    """Get embedding from Gemini API."""
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return np.array(result['embedding'], dtype=np.float32)


def batch_embed(texts: List[str], batch_size: int = 100) -> np.ndarray:
    """Embed texts in batches to respect API rate limits."""
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}...")

        batch_embeddings = []
        for text in batch:
            emb = get_embedding(text)
            batch_embeddings.append(emb)
            time.sleep(0.1)  # Rate limiting (10 requests/sec)

        all_embeddings.extend(batch_embeddings)

    return np.vstack(all_embeddings)


def main():
    """Build pure FAISS binary index."""
    print("Starting Pure FAISS Binary Indexer...")
    start_time = time.time()

    # Load metadata
    print(f"\n1. Loading metadata from {METADATA_FILE}...")
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    # Collect all books
    all_chunks = []
    all_chunk_metadata = []

    print("\n2. Processing books...")
    for topic in metadata['topics']:
        topic_id = topic['id']
        topic_label = topic['label']

        print(f"\n  Topic: {topic_label}")

        for book in topic['books']:
            book_id = book['id']
            book_title = book['title']
            book_filename = book['filename']

            epub_path = BOOKS_DIR / topic_id / book_filename

            if not epub_path.exists():
                print(f"    ⚠️  {book_title}: File not found")
                continue

            print(f"    📖 {book_title}...")

            # Extract text
            text = extract_text_from_epub(epub_path)

            # Chunk text
            chunks = chunk_text(text, chunk_size=800, overlap=150)
            print(f"       Generated {len(chunks)} chunks")

            # Store chunks with metadata
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_chunk_metadata.append({
                    'book_id': book_id,
                    'book_title': book_title,
                    'topic_id': topic_id,
                    'topic_label': topic_label,
                    'chunk_index': chunk_idx,
                    'text': chunk
                })

    print(f"\n3. Total chunks collected: {len(all_chunks)}")

    # Generate embeddings
    print("\n4. Generating embeddings with Gemini...")
    embeddings = batch_embed(all_chunks)

    # Create FAISS index
    print("\n5. Building FAISS index...")
    dimension = embeddings.shape[1]  # Should be 768
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    print(f"   Index created with {index.ntotal} vectors")

    # Save FAISS index
    print(f"\n6. Saving FAISS index to {FAISS_INDEX_FILE}...")
    STORAGE_DIR.mkdir(exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_FILE))

    # Save chunks as pickle (binary)
    print(f"\n7. Saving chunks to {CHUNKS_FILE}...")
    with open(CHUNKS_FILE, 'wb') as f:
        pickle.dump(all_chunk_metadata, f)

    # Stats
    elapsed = time.time() - start_time
    faiss_size = FAISS_INDEX_FILE.stat().st_size / 1024 / 1024
    chunks_size = CHUNKS_FILE.stat().st_size / 1024 / 1024

    print("\n" + "="*60)
    print("✅ FAISS Binary Index Complete!")
    print("="*60)
    print(f"Total chunks: {len(all_chunks)}")
    print(f"FAISS index: {faiss_size:.2f} MB")
    print(f"Chunks file: {chunks_size:.2f} MB")
    print(f"Total storage: {faiss_size + chunks_size:.2f} MB")
    print(f"Time elapsed: {elapsed:.1f}s")
    print("="*60)


if __name__ == "__main__":
    main()
