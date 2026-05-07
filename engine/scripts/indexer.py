#!/usr/bin/env python3
"""
Librarian Indexer v3 — Clustering-Based

Replaces v2 topic-based indexing with:
- Flat book structure (no topic folders required)
- Book-level embeddings (centroid of chunks)
- HDBSCAN clustering (auto-discovery)
- Discipline as optional metadata (not folder-based)

Usage:
    python indexer.py --all              # Index all books
    python indexer.py --discipline name  # Index one discipline
    python indexer.py --book path        # Index one book
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

from sentence_transformers import SentenceTransformer
import numpy as np

# Import text extraction
sys.path.insert(0, str(Path(__file__).parent))
from text_extraction import extract_text, chunk_text

# Paths
LIBRARY_ROOT = Path(__file__).parent.parent.parent / "books"
MODELS_DIR = Path(__file__).parent.parent / "models"

# Embedding model (same as v2 for compatibility)
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



def generate_book_embedding(book_path: Path) -> np.ndarray:
    """
    Generate book-level embedding (centroid of chunk embeddings).
    
    Args:
        book_path: Path to book file
    
    Returns:
        Book embedding (384-dim numpy array)
    """
    # 1. Extract text (REAL IMPLEMENTATION)
    try:
        text = extract_text(book_path)
    except Exception as e:
        print(f"   ⚠️  Failed to extract text from {book_path.name}: {e}")
        # Fallback: use filename as proxy
        text = book_path.stem
    
    if not text or len(text) < 100:
        # Fallback for empty/tiny books: use filename
        text = book_path.stem
    
    # 2. Chunk text
    chunks = chunk_text(text, size=1024, overlap=200)
    
    if not chunks:
        # Fallback: embed filename
        chunks = [book_path.stem]
    
    # 3. Generate embeddings for each chunk
    model = get_embed_model()
    chunk_embeddings = []
    
    for chunk in chunks:
        if not chunk.strip():
            continue  # Skip empty chunks
        emb = model.encode(chunk, convert_to_numpy=True)
        chunk_embeddings.append(emb)
    
    # 4. Book embedding = mean of chunk embeddings
    if not chunk_embeddings:
        # Fallback: zero vector
        return np.zeros(EMBEDDING_DIM)
    
    book_embedding = np.mean(chunk_embeddings, axis=0)
    return book_embedding


def scan_books(discipline_path: Path) -> List[Dict]:
    """
    Scan discipline folder for books (.epub, .pdf).
    
    Args:
        discipline_path: Path to discipline folder
    
    Returns:
        List of book metadata dicts
    """
    books = []
    
    for ext in ['*.epub', '*.pdf']:
        for book_path in discipline_path.rglob(ext):
            # Skip hidden files
            if book_path.name.startswith('.'):
                continue
            
            book_id = book_path.stem.lower().replace(' ', '_')
            
            books.append({
                'id': book_id,
                'title': book_path.stem,
                'filename': book_path.name,
                'path': str(book_path),
                'filetype': book_path.suffix.lstrip('.'),
                'last_modified': os.path.getmtime(book_path)
            })
    
    return books


def index_discipline(discipline_id: str, discipline_path: Path):
    """
    Index all books in a discipline.
    
    Args:
        discipline_id: Discipline ID (e.g., "management_knowledge")
        discipline_path: Path to discipline folder
    """
    print(f"\n📚 Indexing discipline: {discipline_id}")
    print(f"   Path: {discipline_path}")
    
    # 1. Scan books
    books = scan_books(discipline_path)
    print(f"   Found {len(books)} books")
    
    if not books:
        print("   ⚠️  No books found, skipping")
        return
    
    # 2. Generate embeddings for each book
    embeddings = {}
    
    for book in books:
        print(f"   Processing: {book['title']}...", end='', flush=True)
        
        book_path = Path(book['path'])
        embedding = generate_book_embedding(book_path)
        embeddings[book['id']] = embedding.tolist()
        
        print(" ✓")
    
    # 3. Save discipline index (no clustering yet, just embeddings)
    index_path = discipline_path / ".discipline-index.json"
    
    import time
    discipline_index = {
        "schema_version": "3.0",
        "discipline_id": discipline_id,
        "discipline_label": discipline_id.replace('_', ' ').title(),
        "last_indexed": time.time(),
        "embedding_model": EMBEDDING_MODEL,
        "books": books,
        "embeddings": embeddings,
        "clusters": []  # Populated by cluster.py later
    }
    
    with open(index_path, 'w') as f:
        json.dump(discipline_index, f, indent=2)
    
    print(f"   ✅ Saved: {index_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Librarian Indexer v3")
    parser.add_argument('--all', action='store_true', help="Index all disciplines")
    parser.add_argument('--discipline', type=str, help="Index one discipline (path)")
    
    args = parser.parse_args()
    
    if args.all:
        print("\n🚀 Indexing all disciplines...")
        
        # Find all discipline folders (any folder with books)
        disciplines = []
        for item in LIBRARY_ROOT.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if has books
                has_books = any(
                    f.suffix in ['.epub', '.pdf']
                    for f in item.rglob('*')
                    if f.is_file()
                )
                if has_books:
                    disciplines.append((item.name, item))
        
        print(f"Found {len(disciplines)} disciplines")
        
        for discipline_id, discipline_path in disciplines:
            index_discipline(discipline_id, discipline_path)
    
    elif args.discipline:
        discipline_path = LIBRARY_ROOT / args.discipline
        
        if not discipline_path.exists():
            print(f"❌ Discipline not found: {discipline_path}")
            return 1
        
        index_discipline(args.discipline, discipline_path)
    
    else:
        print("❌ Use --all or --discipline <name>")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
