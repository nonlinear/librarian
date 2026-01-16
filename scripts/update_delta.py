#!/usr/bin/env python3
"""
Delta Update Script

Compares metadata.json against books/ folder structure.
Only reindexes what changed (added/removed books).

If no discrepancy: does nothing.
If delta exists: updates DB + metadata.json incrementally.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Set, Tuple
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


def get_books_from_filesystem() -> Dict[str, Dict]:
    """Get actual books from books/ folder structure."""
    books_map = {}

    for topic_dir in BOOKS_DIR.iterdir():
        if not topic_dir.is_dir() or topic_dir.name.startswith('.'):
            continue

        topic_id = topic_dir.name

        for book_file in topic_dir.glob("*.epub"):
            book_key = f"{topic_id}/{book_file.name}"
            books_map[book_key] = {
                'topic_id': topic_id,
                'filename': book_file.name,
                'path': book_file
            }

    return books_map


def get_books_from_metadata() -> Dict[str, Dict]:
    """Get books from metadata.json."""
    if not METADATA_FILE.exists():
        return {}

    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    books_map = {}
    for topic in metadata['topics']:
        for book in topic['books']:
            book_key = f"{topic['id']}/{book['filename']}"
            books_map[book_key] = {
                'topic_id': topic['id'],
                'book_id': book['id'],
                'title': book['title'],
                'filename': book['filename']
            }

    return books_map


def compare_books(fs_books: Dict, meta_books: Dict) -> Tuple[Set[str], Set[str]]:
    """Compare filesystem books vs metadata books."""
    fs_keys = set(fs_books.keys())
    meta_keys = set(meta_books.keys())

    added = fs_keys - meta_keys  # In filesystem but not in metadata
    removed = meta_keys - fs_keys  # In metadata but not in filesystem

    return added, removed


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


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
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


def generate_book_id(filename: str) -> str:
    """Generate book_id from filename."""
    return filename.replace('.epub', '').replace(' ', '_').replace('-', '_').lower()


def extract_book_title(filename: str) -> str:
    """Extract clean title from filename."""
    return filename.replace('.epub', '').strip()


def main():
    """Run delta update."""
    print("="*60)
    print("Delta Update Script - RAG Incremental Indexing")
    print("="*60)

    # 1. Get current state
    print("\n1. Scanning filesystem...")
    fs_books = get_books_from_filesystem()
    print(f"   Found {len(fs_books)} books in books/")

    print("\n2. Reading metadata.json...")
    meta_books = get_books_from_metadata()
    print(f"   Found {len(meta_books)} books in metadata")

    # 2. Compare
    print("\n3. Comparing...")
    added, removed = compare_books(fs_books, meta_books)

    if not added and not removed:
        print("\n✅ No changes detected. Database is up to date.")
        print("   Exiting without modification.")
        return

    print(f"\n   📊 Delta detected:")
    print(f"      Added: {len(added)} books")
    print(f"      Removed: {len(removed)} books")

    # Show details
    if added:
        print(f"\n   ➕ Added books:")
        for book_key in sorted(added):
            print(f"      - {book_key}")

    if removed:
        print(f"\n   ➖ Removed books:")
        for book_key in sorted(removed):
            print(f"      - {book_key}")

    # 3. Load existing index (if exists)
    if FAISS_INDEX_FILE.exists() and CHUNKS_FILE.exists():
        print(f"\n4. Loading existing index...")
        index = faiss.read_index(str(FAISS_INDEX_FILE))
        with open(CHUNKS_FILE, 'rb') as f:
            chunks_metadata = pickle.load(f)
        print(f"   Loaded {len(chunks_metadata)} existing chunks")
    else:
        print(f"\n4. No existing index - creating new one...")
        index = None
        chunks_metadata = []

    # 4. Handle removals
    if removed and chunks_metadata:
        print(f"\n5. Removing chunks from deleted books...")
        removed_book_ids = set()
        for book_key in removed:
            book_id = meta_books[book_key]['book_id']
            removed_book_ids.add(book_id)

        # Filter out removed chunks
        kept_chunks = [c for c in chunks_metadata if c['book_id'] not in removed_book_ids]
        removed_count = len(chunks_metadata) - len(kept_chunks)
        chunks_metadata = kept_chunks

        print(f"   Removed {removed_count} chunks")

        # Rebuild FAISS index (no way to remove from FAISS directly)
        if chunks_metadata:
            print(f"   Rebuilding FAISS index...")
            embeddings = []
            for chunk in chunks_metadata:
                emb = get_embedding(chunk['text'])
                embeddings.append(emb)
                time.sleep(0.1)

            embeddings_array = np.vstack(embeddings)
            dimension = embeddings_array.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_array)
        else:
            index = None

    # 5. Handle additions
    if added:
        print(f"\n6. Adding new books...")
        new_chunks = []

        for book_key in sorted(added):
            book_info = fs_books[book_key]
            topic_id = book_info['topic_id']
            filename = book_info['filename']
            book_path = book_info['path']

            book_id = generate_book_id(filename)
            book_title = extract_book_title(filename)

            print(f"\n   📖 {book_title}")
            print(f"      Extracting text...")
            text = extract_text_from_epub(book_path)

            print(f"      Chunking...")
            chunks = chunk_text(text)
            print(f"      Generated {len(chunks)} chunks")

            print(f"      Embedding...")
            for chunk_idx, chunk in enumerate(chunks):
                emb = get_embedding(chunk)

                # Add to index
                if index is None:
                    dimension = len(emb)
                    index = faiss.IndexFlatL2(dimension)

                index.add(np.array([emb]))

                # Store metadata
                chunks_metadata.append({
                    'book_id': book_id,
                    'book_title': book_title,
                    'topic_id': topic_id,
                    'chunk_index': chunk_idx,
                    'text': chunk
                })

                time.sleep(0.1)  # Rate limiting

        print(f"\n   ✅ Added {len(new_chunks)} new chunks")

    # 6. Update metadata.json
    print(f"\n7. Updating metadata.json...")

    # Load or create metadata
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {'topics': []}

    # Remove deleted books
    for topic in metadata['topics']:
        topic['books'] = [
            b for b in topic['books']
            if f"{topic['id']}/{b['filename']}" not in removed
        ]

    # Add new books
    for book_key in added:
        book_info = fs_books[book_key]
        topic_id = book_info['topic_id']
        filename = book_info['filename']

        # Find or create topic
        topic = None
        for t in metadata['topics']:
            if t['id'] == topic_id:
                topic = t
                break

        if topic is None:
            topic = {
                'id': topic_id,
                'label': topic_id.replace('_', ' ').title(),
                'description': '',
                'books': []
            }
            metadata['topics'].append(topic)

        # Add book
        book_id = generate_book_id(filename)
        book_title = extract_book_title(filename)

        topic['books'].append({
            'id': book_id,
            'title': book_title,
            'author': None,
            'year': None,
            'tags': [],
            'filename': filename
        })

    # Save metadata
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"   ✅ metadata.json updated")

    # 7. Save index
    print(f"\n8. Saving updated index...")
    STORAGE_DIR.mkdir(exist_ok=True)

    if index:
        faiss.write_index(index, str(FAISS_INDEX_FILE))
        print(f"   ✅ FAISS index saved ({index.ntotal} vectors)")

    with open(CHUNKS_FILE, 'wb') as f:
        pickle.dump(chunks_metadata, f)
    print(f"   ✅ Chunks saved ({len(chunks_metadata)} chunks)")

    # Stats
    print("\n" + "="*60)
    print("✅ Delta Update Complete!")
    print("="*60)
    print(f"Total chunks: {len(chunks_metadata)}")
    if index:
        faiss_size = FAISS_INDEX_FILE.stat().st_size / 1024 / 1024
        chunks_size = CHUNKS_FILE.stat().st_size / 1024 / 1024
        print(f"FAISS index: {faiss_size:.2f} MB")
        print(f"Chunks file: {chunks_size:.2f} MB")
    print("="*60)


if __name__ == "__main__":
    main()
