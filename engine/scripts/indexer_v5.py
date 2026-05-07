#!/usr/bin/env python3
"""
Librarian Indexer v5 — Chunk-Level with Source Metadata

Key changes from v4:
- Stores individual chunks (not just book-level embeddings)
- Each chunk includes source metadata (CFI for EPUB, page for PDF)
- Enables precise navigation in reader

Schema v5.1:
{
    "books": [...],       # book metadata only
    "chunks": {           # chunk-level embeddings + source
        "ch_abc123": {
            "chunk_id": "ch_abc123",
            "book_id": "book_xyz",
            "text": "...",
            "source": {
                "type": "epub",
                "spine_index": 3,
                "href": "chapter1.xhtml",
                "paragraphs": [
                    {"idx": 10, "text": "...", "element_id": "para123"}
                ]
            },
            "embedding": [...]
        }
    }
}
"""
import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional
import uuid

from sentence_transformers import SentenceTransformer
import numpy as np

# Import text extraction with new paragraph functions
sys.path.insert(0, str(Path(__file__).parent))
from text_extraction import (
    extract_epub_paragraphs,
    extract_pdf_paragraphs,
    chunk_paragraphs
)

# Paths
LIBRARY_ROOT = Path("/app/books")
MODELS_DIR = Path("/app/engine/models")
INDEX_PATH = LIBRARY_ROOT / ".global-index-v5.1.json"

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
    """Generate stable book ID from content hash."""
    try:
        with open(book_path, 'rb') as f:
            content_sample = f.read(1024 * 1024)  # 1MB
        return hashlib.sha256(content_sample).hexdigest()[:16]
    except Exception:
        rel_path = book_path.relative_to(LIBRARY_ROOT)
        return hashlib.sha256(str(rel_path).encode()).hexdigest()[:16]


def process_book(book_path: Path, existing_books: Dict) -> tuple:
    """
    Process single book: extract paragraphs, chunk, embed.
    
    Returns:
        (book_metadata, chunks_list) or (None, None) if duplicate/unindexable
    """
    book_id = compute_book_id(book_path)
    filetype = book_path.suffix.lstrip('.')
    
    # T017: Check for duplicates
    if book_id in existing_books:
        original_path = existing_books[book_id]['path']
        print(f"   ⚠️  Duplicate: {book_path.name}")
        print(f"      Original: {original_path}")
        print(f"      Deleting duplicate...", end='', flush=True)
        try:
            os.remove(book_path)
            print(" ✓ Deleted")
        except Exception as e:
            print(f" ❌ Failed to delete: {e}")
        return None, None
    
    print(f"   Processing: {book_path.name}...", end='', flush=True)
    
    # T018: Move unindexable to no-indexing/
    NO_INDEXING_DIR = LIBRARY_ROOT / "no-indexing"
    
    def move_to_no_indexing(reason: str):
        """Move book to no-indexing folder."""
        print(f" ⚠️  {reason}")
        print(f"      Moving to no-indexing/...", end='', flush=True)
        try:
            NO_INDEXING_DIR.mkdir(exist_ok=True)
            target = NO_INDEXING_DIR / book_path.name
            import shutil
            shutil.move(str(book_path), str(target))
            print(f" ✓ Moved")
        except Exception as e:
            print(f" ❌ Move failed: {e}")
        return None, None
    
    # Extract paragraphs with structure
    try:
        if filetype == 'epub':
            paragraphs = extract_epub_paragraphs(book_path)
        elif filetype == 'pdf':
            paragraphs = extract_pdf_paragraphs(book_path)
        else:
            return move_to_no_indexing(f"Unsupported filetype: {filetype}")
    except Exception as e:
        return move_to_no_indexing(f"Extraction failed: {e}")
    
    if not paragraphs:
        return move_to_no_indexing("No paragraphs extracted")
    
    # Chunk paragraphs (respecting boundaries)
    chunks = chunk_paragraphs(paragraphs, max_chars=1024)
    
    if not chunks:
        return move_to_no_indexing("No chunks generated")
    
    # Generate embeddings for chunks
    model = get_embed_model()
    chunk_objects = []
    
    for chunk in chunks:
        chunk_id = f"ch_{uuid.uuid4().hex[:12]}"
        text = chunk["text"]
        
        # Generate embedding
        try:
            embedding = model.encode(text, convert_to_numpy=True)
        except Exception as e:
            print(f" ⚠️  Embedding failed: {e}")
            continue
        
        chunk_obj = {
            "chunk_id": chunk_id,
            "book_id": book_id,
            "text": text,
            "source": chunk["source"],
            "paragraphs": chunk["paragraphs"],
            "embedding": embedding.tolist()
        }
        
        chunk_objects.append(chunk_obj)
    
    print(f" ✓ ({len(chunk_objects)} chunks)")
    
    # Book metadata (no embedding, chunks are separate)
    book_meta = {
        "id": book_id,
        "title": book_path.stem,
        "filename": book_path.name,
        "path": str(book_path),
        "filetype": filetype,
        "last_modified": os.path.getmtime(book_path),
        "chunk_count": len(chunk_objects)
    }
    
    return book_meta, chunk_objects


def scan_all_books() -> List[Path]:
    """Scan LIBRARY_ROOT for all .epub and .pdf files (excluding no-indexing/)."""
    books = []
    for ext in ['*.epub', '*.pdf']:
        books.extend(LIBRARY_ROOT.rglob(ext))
    
    # Filter hidden files and no-indexing folder
    books = [
        b for b in books 
        if not any(p.startswith('.') for p in b.parts)
        and 'no-indexing' not in b.parts
    ]
    
    return sorted(books)


def load_existing_index() -> Dict:
    """Load existing index if available."""
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            return json.load(f)
    return {
        "schema_version": "5.1",
        "embedding_model": EMBEDDING_MODEL,
        "last_indexed": 0,
        "total_books": 0,
        "total_chunks": 0,
        "books": [],
        "chunks": {}
    }


def save_index(index: Dict):
    """Save index to disk (atomic write)."""
    import tempfile
    
    # Write to temp file first
    with tempfile.NamedTemporaryFile("w", delete=False, dir=INDEX_PATH.parent) as tmp:
        json.dump(index, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
    
    # Atomic rename (POSIX guarantees atomicity)
    os.replace(tmp.name, INDEX_PATH)


def index_all_books():
    """Main indexing: scan books, extract chunks with source, embed."""
    print("\n🚀 Indexing all books (with source metadata)...")
    
    # 1. Load existing index to check for duplicates
    existing_index = load_existing_index()
    existing_books = {b["id"]: b for b in existing_index.get("books", [])}
    
    # 2. Scan library
    book_paths = scan_all_books()
    print(f"Found {len(book_paths)} books\n")
    
    if not book_paths:
        print(f"⚠️  No books found in {LIBRARY_ROOT}")
        return
    
    # 3. Process books
    all_books = []
    all_chunks = {}
    
    for book_path in book_paths:
        book_meta, chunks = process_book(book_path, existing_books)
        
        if book_meta:
            all_books.append(book_meta)
            existing_books[book_meta["id"]] = book_meta  # Update for duplicate detection
            
            # Add chunks to global dict
            for chunk in chunks:
                all_chunks[chunk["chunk_id"]] = chunk
    
    # 4. Build index
    index = {
        "schema_version": "5.1",
        "embedding_model": EMBEDDING_MODEL,
        "last_indexed": time.time(),
        "total_books": len(all_books),
        "total_chunks": len(all_chunks),
        "books": all_books,
        "chunks": all_chunks
    }
    
    # 5. Save
    save_index(index)
    
    print(f"\n✅ Index updated")
    print(f"   Total books: {len(all_books)}")
    print(f"   Total chunks: {len(all_chunks)}")


def index_single_file(file_path: str):
    """Index single file (incremental)."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ File not found: {path}")
        return
    
    print(f"\n🚀 Indexing single file: {path.name}")
    
    # Load existing index
    index = load_existing_index()
    existing_chunks = index.get("chunks", {})
    existing_books = {b["id"]: b for b in index.get("books", [])}
    
    # Process book (with duplicate check)
    book_meta, chunks = process_book(path, existing_books)
    
    if not book_meta:
        print("❌ Processing failed")
        return
    
    # Remove old chunks for this book
    book_id = book_meta["id"]
    existing_chunks = {
        cid: chunk for cid, chunk in existing_chunks.items()
        if chunk["book_id"] != book_id
    }
    
    # Add new chunks
    for chunk in chunks:
        existing_chunks[chunk["chunk_id"]] = chunk
    
    # Update book metadata
    existing_books[book_id] = book_meta
    
    # Update index
    index["books"] = list(existing_books.values())
    index["chunks"] = existing_chunks
    index["total_books"] = len(index["books"])
    index["total_chunks"] = len(existing_chunks)
    index["last_indexed"] = time.time()
    
    # Save
    save_index(index)
    
    print(f"\n✅ Index updated")
    print(f"   Total books: {index['total_books']}")
    print(f"   Total chunks: {index['total_chunks']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Librarian Indexer v5 (with source metadata)")
    parser.add_argument("--file", help="Index single file (incremental)")
    
    args = parser.parse_args()
    
    if args.file:
        index_single_file(args.file)
    else:
        index_all_books()
