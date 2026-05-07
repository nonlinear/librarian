#!/usr/bin/env python3
"""
Librarian Indexer v4 — Folder-Agnostic

Key changes from v3:
- NO folder/discipline concept required
- Bottom-up: scan all .epub/.pdf recursively
- Folder path becomes optional metadata tag
- Single command: python indexer.py (no args!)

ARCHITECTURAL PRINCIPLES:
1. Identity = content hash (first 1MB)
   - Moving/renaming file preserves book_id
   - Duplicates detected automatically
   - Path is irrelevant to identity

2. Storage path = informational metadata only
   - Does NOT influence search/retrieval
   - Does NOT influence clustering
   - Used only for debugging/UI breadcrumbs

3. Semantic structure = emergent (clustering)
   - No top-down folder taxonomy
   - Content determines relationships
   - FAISS index is cache (rebuildable)

Usage:
    python indexer.py                    # Index all books (default)
    python indexer.py --file path.epub   # Index single file (incremental)
"""
import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional

from sentence_transformers import SentenceTransformer
import numpy as np

# Import text extraction
sys.path.insert(0, str(Path(__file__).parent))
from text_extraction import extract_text, chunk_text

# Paths
LIBRARY_ROOT = Path("/app/books")
MODELS_DIR = Path("/app/engine/models")
INDEX_PATH = LIBRARY_ROOT / ".global-index-v5.json"

# Embedding model
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

# Global embed model (lazy load)
embed_model = None


def get_embed_model():
    """Lazy load embedding model."""
    global embed_model
    if embed_model is None:
        embed_model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=str(MODELS_DIR))
    return embed_model


def compute_book_id(book_path: Path) -> str:
    """
    Generate stable book ID from file content hash.
    
    Content-addressed: moving/renaming file preserves identity.
    Uses first 1MB for performance (99.9% collision-free).
    """
    # Read first 1MB of file for hashing (fast, unique enough)
    try:
        with open(book_path, 'rb') as f:
            content_sample = f.read(1024 * 1024)  # 1MB
        return hashlib.sha256(content_sample).hexdigest()[:16]
    except Exception as e:
        # Fallback: hash path (better than crashing)
        rel_path = book_path.relative_to(LIBRARY_ROOT)
        return hashlib.sha256(str(rel_path).encode()).hexdigest()[:16]


def extract_folder_tags(book_path: Path) -> List[str]:
    """
    Extract folder hierarchy as storage metadata (NOT semantic tags).
    
    This is purely informational — does NOT influence:
    - Search/retrieval
    - Clustering
    - Identity
    
    Used only for:
    - Debugging ("where is this file?")
    - Optional UI breadcrumbs
    """
    rel_path = book_path.relative_to(LIBRARY_ROOT)
    parts = rel_path.parts[:-1]  # exclude filename
    return [p for p in parts if not p.startswith('.')]


def generate_book_embedding(book_path: Path) -> np.ndarray:
    """
    Generate book-level embedding (centroid of chunk embeddings).
    
    Args:
        book_path: Path to book file
    
    Returns:
        Book embedding (384-dim numpy array)
    """
    # 1. Extract text
    try:
        text = extract_text(book_path)
    except Exception as e:
        print(f"   ⚠️  Failed to extract text from {book_path.name}: {e}")
        text = book_path.stem
    
    if not text or len(text) < 100:
        text = book_path.stem
    
    # 2. Chunk text
    chunks = chunk_text(text, size=1024, overlap=200)
    
    if not chunks:
        chunks = [book_path.stem]
    
    # 3. Generate embeddings for each chunk
    model = get_embed_model()
    chunk_embeddings = []
    
    for chunk in chunks:
        if not chunk.strip():
            continue
        emb = model.encode(chunk, convert_to_numpy=True)
        chunk_embeddings.append(emb)
    
    # 4. Book embedding = mean of chunk embeddings
    if not chunk_embeddings:
        return np.zeros(EMBEDDING_DIM)
    
    book_embedding = np.mean(chunk_embeddings, axis=0)
    return book_embedding


def scan_all_books() -> List[Path]:
    """
    Recursively scan LIBRARY_ROOT for all .epub and .pdf files.
    
    Returns:
        List of book paths (sorted)
    """
    books = []
    for ext in ['*.epub', '*.pdf']:
        books.extend(LIBRARY_ROOT.rglob(ext))
    
    # Filter hidden files
    books = [b for b in books if not any(p.startswith('.') for p in b.parts)]
    
    return sorted(books)


def process_book(book_path: Path) -> Dict:
    """
    Process a single book: extract metadata + generate embedding.
    
    Args:
        book_path: Path to book file
    
    Returns:
        Book metadata dict with embedding
    """
    book_id = compute_book_id(book_path)
    storage_path_parts = extract_folder_tags(book_path)  # storage detail, not semantic
    
    print(f"   Processing: {book_path.name}...", end='', flush=True)
    
    # Generate embedding
    embedding = generate_book_embedding(book_path)
    
    # Count chunks (for search quality metric)
    try:
        text = extract_text(book_path)
        chunks = chunk_text(text, size=1024, overlap=200)
        chunk_count = len(chunks)
    except:
        chunk_count = 1
    
    print(" ✓")
    
    return {
        "id": book_id,
        "title": book_path.stem,
        "filename": book_path.name,
        "path": str(book_path),
        "filetype": book_path.suffix.lstrip('.'),
        "storage_path": storage_path_parts,  # informational only
        "last_modified": os.path.getmtime(book_path),
        "chunk_count": chunk_count,
        "embedding": embedding.tolist()
    }


def load_existing_index() -> Dict:
    """Load existing index if available."""
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            return json.load(f)
    return {
        "schema_version": "5.0",
        "embedding_model": EMBEDDING_MODEL,
        "last_indexed": 0,
        "total_books": 0,
        "total_chunks": 0,
        "books": []
    }


def save_index(index: Dict):
    """Save index to disk (atomic write)."""
    import tempfile
    import os
    
    # Write to temp file first
    with tempfile.NamedTemporaryFile("w", delete=False, dir=INDEX_PATH.parent) as tmp:
        json.dump(index, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
    
    # Atomic rename (POSIX guarantees atomicity)
    os.replace(tmp.name, INDEX_PATH)


def index_all_books():
    """
    Main indexing logic: scan all books, generate embeddings, save index.
    """
    print("\n🚀 Indexing all books (folder-agnostic)...")
    
    # 1. Scan library
    book_paths = scan_all_books()
    print(f"Found {len(book_paths)} books\n")
    
    if not book_paths:
        print("⚠️  No books found in {LIBRARY_ROOT}")
        return
    
    # 2. Load existing index for incremental updates
    index = load_existing_index()
    existing_books = {b["id"]: b for b in index.get("books", [])}
    
    # 3. Process books (skip unchanged if possible)
    processed_books = []
    total_chunks = 0
    
    for book_path in book_paths:
        book_id = compute_book_id(book_path)
        last_modified = os.path.getmtime(book_path)
        
        # Check if already indexed and unchanged
        if book_id in existing_books:
            existing = existing_books[book_id]
            if existing.get("last_modified") == last_modified:
                print(f"   Skipping: {book_path.name} (unchanged)")
                processed_books.append(existing)
                total_chunks += existing.get("chunk_count", 0)
                continue
        
        # Process book
        book_meta = process_book(book_path)
        processed_books.append(book_meta)
        total_chunks += book_meta["chunk_count"]
    
    # 4. Update index
    index["last_indexed"] = time.time()
    index["total_books"] = len(processed_books)
    index["total_chunks"] = total_chunks
    index["books"] = processed_books
    
    # 5. Save
    save_index(index)
    print(f"\n✅ Indexed {len(processed_books)} books ({total_chunks} chunks)")
    print(f"   Saved: {INDEX_PATH}")


def index_single_file(file_path: str):
    """
    Index a single book file (incremental).
    
    Args:
        file_path: Path to book file
    """
    book_path = Path(file_path)
    
    if not book_path.exists():
        print(f"❌ File not found: {file_path}")
        return 1
    
    if book_path.suffix.lower() not in ['.epub', '.pdf']:
        print(f"❌ Unsupported file type: {book_path.suffix}")
        return 1
    
    print(f"\n🚀 Indexing single file: {book_path.name}")
    
    # Load existing index
    index = load_existing_index()
    existing_books = {b["id"]: b for b in index.get("books", [])}
    
    # Process book
    book_meta = process_book(book_path)
    book_id = book_meta["id"]
    
    # Update or add
    if book_id in existing_books:
        # Replace existing
        index["books"] = [
            book_meta if b["id"] == book_id else b
            for b in index["books"]
        ]
        print(f"   Updated existing book")
    else:
        # Add new
        index["books"].append(book_meta)
        print(f"   Added new book")
    
    # Recalculate totals
    index["last_indexed"] = time.time()
    index["total_books"] = len(index["books"])
    index["total_chunks"] = sum(b.get("chunk_count", 0) for b in index["books"])
    
    # Save
    save_index(index)
    print(f"\n✅ Index updated")
    print(f"   Total books: {index['total_books']}")
    
    return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Librarian Indexer v4 (Folder-Agnostic)")
    parser.add_argument('--file', type=str, help="Index single file (incremental)")
    
    args = parser.parse_args()
    
    if args.file:
        return index_single_file(args.file)
    else:
        # Default: index all
        index_all_books()
        return 0


if __name__ == "__main__":
    sys.exit(main())
