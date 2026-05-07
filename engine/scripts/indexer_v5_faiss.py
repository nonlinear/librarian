#!/usr/bin/env python3
"""
Librarian Indexer v5.1 — FAISS-Based (No OOM)

Optimized indexer that uses FAISS + metadata.json for duplicate detection.
Avoids loading 2.3GB legacy JSON into memory.
"""
import os
import sys
import json
import hashlib
import time
import shutil
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Set
import uuid

from sentence_transformers import SentenceTransformer

# Import text extraction
sys.path.insert(0, str(Path(__file__).parent))
from text_extraction import (
    extract_epub_paragraphs,
    extract_pdf_paragraphs,
    chunk_paragraphs
)

# Paths
LIBRARY_ROOT = Path("/app/books")
MODELS_DIR = Path("/app/engine/models")
FAISS_INDEX_PATH = LIBRARY_ROOT / "faiss.index"
METADATA_PATH = LIBRARY_ROOT / "metadata.json"
NO_INDEXING_DIR = LIBRARY_ROOT / "no-indexing"

# Embedding model
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

# Global model (lazy load)
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


def load_existing_book_ids() -> Set[str]:
    """
    Load existing book IDs from metadata.json.
    Much smaller than loading full index (433MB vs 2.3GB).
    """
    if not METADATA_PATH.exists():
        return set()
    
    try:
        with open(METADATA_PATH) as f:
            metadata = json.load(f)
        
        book_ids = set()
        
        # Extract book IDs from chunks
        for chunk in metadata.get("chunks", []):
            book_ids.add(chunk["book_id"])
        
        print(f"   Loaded {len(book_ids)} existing book IDs from metadata")
        return book_ids
    
    except Exception as e:
        print(f"⚠️  Failed to load metadata: {e}")
        return set()


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


def move_to_no_indexing(book_path: Path, reason: str):
    """Move unindexable book to quarantine folder."""
    print(f" ⚠️  {reason}")
    print(f"      Moving to no-indexing/...", end='', flush=True)
    try:
        NO_INDEXING_DIR.mkdir(exist_ok=True)
        target = NO_INDEXING_DIR / book_path.name
        shutil.move(str(book_path), str(target))
        print(f" ✓ Moved")
    except Exception as e:
        print(f" ❌ Move failed: {e}")


def process_book(book_path: Path, existing_book_ids: Set[str]) -> Optional[Dict]:
    """
    Process single book: extract paragraphs, chunk, embed.
    
    Returns:
        {
            "book": {...},      # Book metadata
            "chunks": [...]     # List of chunk objects
        }
        or None if duplicate/unindexable
    """
    book_id = compute_book_id(book_path)
    filetype = book_path.suffix.lstrip('.')
    
    # T017: Check for duplicates
    if book_id in existing_book_ids:
        print(f"   ⚠️  Duplicate: {book_path.name}")
        print(f"      Deleting duplicate...", end='', flush=True)
        try:
            os.remove(book_path)
            print(" ✓ Deleted")
        except Exception as e:
            print(f" ❌ Failed to delete: {e}")
        return None
    
    print(f"   Processing: {book_path.name}...", end='', flush=True)
    
    # Extract paragraphs
    try:
        if filetype == 'epub':
            paragraphs = extract_epub_paragraphs(book_path)
        elif filetype == 'pdf':
            paragraphs = extract_pdf_paragraphs(book_path)
        else:
            move_to_no_indexing(book_path, f"Unsupported filetype: {filetype}")
            return None
    except Exception as e:
        move_to_no_indexing(book_path, f"Extraction failed: {e}")
        return None
    
    if not paragraphs:
        move_to_no_indexing(book_path, "No paragraphs extracted")
        return None
    
    # Chunk paragraphs
    chunks = chunk_paragraphs(paragraphs, max_chars=1024)
    
    if not chunks:
        move_to_no_indexing(book_path, "No chunks generated")
        return None
    
    # Generate embeddings
    model = get_embed_model()
    chunk_objects = []
    
    for chunk in chunks:
        chunk_id = f"ch_{uuid.uuid4().hex[:12]}"
        text = chunk["text"]
        
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
    
    # Book metadata
    book_meta = {
        "id": book_id,
        "title": book_path.stem,
        "filename": book_path.name,
        "path": str(book_path),
        "filetype": filetype,
        "last_modified": os.path.getmtime(book_path),
        "chunk_count": len(chunk_objects)
    }
    
    return {
        "book": book_meta,
        "chunks": chunk_objects
    }


def build_faiss_index(all_chunks: List[Dict]) -> faiss.Index:
    """Build FAISS index from chunks."""
    print(f"\n   Building FAISS index ({len(all_chunks):,} chunks)...")
    
    # Create index
    index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner product (cosine similarity)
    
    # Prepare embeddings
    embeddings = np.array([c["embedding"] for c in all_chunks], dtype="float32")
    
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Add to index
    index.add(embeddings)
    
    print(f"   ✓ FAISS index built: {index.ntotal:,} vectors")
    
    return index


def save_faiss_index(index: faiss.Index, chunks: List[Dict], books: List[Dict]):
    """Save FAISS index + metadata atomically."""
    import tempfile
    
    print(f"\n   Saving FAISS index...")
    
    # 1. Save FAISS index
    temp_index = tempfile.NamedTemporaryFile(delete=False, dir=LIBRARY_ROOT)
    faiss.write_index(index, temp_index.name)
    os.replace(temp_index.name, FAISS_INDEX_PATH)
    
    # 2. Save metadata (without embeddings)
    metadata = {
        "books": books,
        "chunks": [
            {k: v for k, v in c.items() if k != "embedding"}
            for c in chunks
        ]
    }
    
    temp_meta = tempfile.NamedTemporaryFile("w", delete=False, dir=LIBRARY_ROOT)
    json.dump(metadata, temp_meta, indent=2)
    temp_meta.flush()
    os.fsync(temp_meta.fileno())
    temp_meta.close()
    os.replace(temp_meta.name, METADATA_PATH)
    
    # Get sizes
    faiss_size = FAISS_INDEX_PATH.stat().st_size / 1024 / 1024
    meta_size = METADATA_PATH.stat().st_size / 1024 / 1024
    
    print(f"   ✓ FAISS index: {faiss_size:.1f} MB")
    print(f"   ✓ Metadata: {meta_size:.1f} MB")


def index_all_books():
    """Main indexing: scan books, extract chunks, build FAISS."""
    print("\n🚀 Indexing all books (FAISS-based, no OOM)...")
    
    # 1. Load existing book IDs (not full chunks)
    existing_book_ids = load_existing_book_ids()
    
    # 2. Scan library
    book_paths = scan_all_books()
    print(f"Found {len(book_paths)} books\n")
    
    if not book_paths:
        print(f"⚠️  No books found in {LIBRARY_ROOT}")
        return
    
    # 3. Process books
    all_books = []
    all_chunks = []
    
    for book_path in book_paths:
        result = process_book(book_path, existing_book_ids)
        
        if result:
            all_books.append(result["book"])
            all_chunks.extend(result["chunks"])
            existing_book_ids.add(result["book"]["id"])  # Update for next iteration
    
    # 4. Build FAISS index
    if not all_chunks:
        print("\n⚠️  No chunks to index")
        return
    
    index = build_faiss_index(all_chunks)
    
    # 5. Save
    save_faiss_index(index, all_chunks, all_books)
    
    print(f"\n✅ Index updated")
    print(f"   Total books: {len(all_books)}")
    print(f"   Total chunks: {len(all_chunks):,}")


if __name__ == "__main__":
    index_all_books()
