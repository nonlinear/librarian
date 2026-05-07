#!/usr/bin/env python3
"""
Librarian Indexer v6 — Production Incremental Architecture

Three-layer design:
1. Discovery Layer: scan filesystem, compute hashes
2. State Layer: index_state.json (source of truth)
3. Storage Layer: FAISS (append-only embedding log)

Key properties:
- Identity = content hash (not path)
- Path = metadata only (can move freely)
- O(Δ) processing (only new books)
- FAISS append-only (no rebuild)
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
import tempfile

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
INDEX_STATE_PATH = LIBRARY_ROOT / ".index_state.json"
NO_INDEXING_DIR = LIBRARY_ROOT / "no-indexing"

# Embedding model
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

embed_model = None


def get_embed_model():
    """Lazy load embedding model."""
    global embed_model
    if embed_model is None:
        embed_model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=str(MODELS_DIR))
    return embed_model


# ============================================================================
# LAYER 1: DISCOVERY (filesystem → file entries)
# ============================================================================

def compute_book_hash(file_path: Path) -> str:
    """Content-based identity (stable across moves)."""
    try:
        with open(file_path, 'rb') as f:
            content_sample = f.read(1024 * 1024)  # 1MB sample
        return hashlib.sha256(content_sample).hexdigest()[:16]
    except Exception as e:
        # Fallback to path-based hash (better than crash)
        return hashlib.sha256(str(file_path).encode()).hexdigest()[:16]


def get_file_fingerprint(file_path: Path) -> tuple:
    """Fast fingerprint for change detection (size, mtime)."""
    stat = file_path.stat()
    return (stat.st_size, int(stat.st_mtime))


def scan_filesystem(state: Dict) -> Dict[str, Dict]:
    """
    Scan library with fingerprint-based caching.
    
    Fast path: if (size, mtime) unchanged → reuse cached hash
    Slow path: if changed or new → compute hash
    
    Returns:
        {
            "hash_abc123": {
                "path": "/app/books/AI/book.epub",
                "size": 12345,
                "mtime": 1234567890,
                "filetype": "epub"
            },
            ...
        }
    """
    discovered = {}
    file_cache = state.get("file_cache", {})
    updated_cache = {}
    
    # Stats for reporting
    stats = {"total": 0, "cached": 0, "hashed": 0}
    
    for ext in ['*.epub', '*.pdf']:
        for file_path in LIBRARY_ROOT.rglob(ext):
            # Skip hidden files and no-indexing folder
            if any(p.startswith('.') for p in file_path.parts):
                continue
            if 'no-indexing' in file_path.parts:
                continue
            
            stats["total"] += 1
            path_str = str(file_path)
            
            # Get current fingerprint
            fingerprint = get_file_fingerprint(file_path)
            
            # Check cache (fast path)
            cached = file_cache.get(path_str)
            if cached and cached["fingerprint"] == fingerprint:
                # File unchanged → reuse hash
                book_hash = cached["hash"]
                stats["cached"] += 1
            else:
                # File changed or new → compute hash (slow path)
                book_hash = compute_book_hash(file_path)
                stats["hashed"] += 1
            
            # Update file cache
            updated_cache[path_str] = {
                "fingerprint": fingerprint,
                "hash": book_hash
            }
            
            # Add to discovered
            discovered[book_hash] = {
                "path": path_str,
                "size": fingerprint[0],
                "mtime": fingerprint[1],
                "filetype": file_path.suffix.lstrip('.')
            }
    
    # Update state with new cache
    state["file_cache"] = updated_cache
    
    print(f"   {stats['total']} files: {stats['cached']} cached, {stats['hashed']} hashed")
    
    return discovered


# ============================================================================
# LAYER 2: STATE MANAGEMENT (index state = source of truth)
# ============================================================================

def load_index_state() -> Dict:
    """
    Load index state (what is currently indexed).
    
    Returns:
        {
            "file_cache": {  # NEW: fingerprint cache
                "/app/books/a.epub": {
                    "fingerprint": [12345, 1710000000],
                    "hash": "abc123"
                }
            },
            "books": {
                "hash_abc123": {
                    "path": "/app/books/AI/book.epub",
                    "indexed_at": 1234567890.0,
                    "chunk_range": [0, 500],
                    "chunk_count": 500
                }
            },
            "total_chunks": 167767,
            "total_books": 290,
            "last_updated": 1234567890.0
        }
    """
    if not INDEX_STATE_PATH.exists():
        return {
            "file_cache": {},
            "books": {},
            "total_chunks": 0,
            "total_books": 0,
            "last_updated": 0
        }
    
    with open(INDEX_STATE_PATH) as f:
        state = json.load(f)
        # Ensure file_cache exists (migration from old format)
        if "file_cache" not in state:
            state["file_cache"] = {}
        return state


def save_index_state(state: Dict):
    """Atomically save index state."""
    temp = tempfile.NamedTemporaryFile("w", delete=False, dir=LIBRARY_ROOT)
    json.dump(state, temp, indent=2)
    temp.flush()
    os.fsync(temp.fileno())
    temp.close()
    os.replace(temp.name, INDEX_STATE_PATH)


def compute_diff(current_fs: Dict, index_state: Dict) -> Dict:
    """
    Compute what changed since last index.
    
    Returns:
        {
            "new": ["hash_abc", "hash_def"],      # New books to index
            "moved": {"hash_xyz": "new/path"},    # Path changed (metadata update only)
            "deleted": ["hash_old"]                # No longer on disk
        }
    """
    current_hashes = set(current_fs.keys())
    indexed_hashes = set(index_state["books"].keys())
    
    diff = {
        "new": list(current_hashes - indexed_hashes),
        "moved": {},
        "deleted": list(indexed_hashes - current_hashes)
    }
    
    # Check for moved files (same hash, different path)
    for book_hash in (current_hashes & indexed_hashes):
        old_path = index_state["books"][book_hash]["path"]
        new_path = current_fs[book_hash]["path"]
        if old_path != new_path:
            diff["moved"][book_hash] = new_path
    
    return diff


# ============================================================================
# LAYER 3: PROCESSING (extract → embed → append to FAISS)
# ============================================================================

def move_to_no_indexing(book_path: Path, reason: str):
    """Move unindexable book to quarantine."""
    print(f"   ⚠️  {reason}")
    print(f"      Moving to no-indexing/...", end='', flush=True)
    try:
        NO_INDEXING_DIR.mkdir(exist_ok=True)
        target = NO_INDEXING_DIR / book_path.name
        shutil.move(str(book_path), str(target))
        print(f" ✓ Moved")
    except Exception as e:
        print(f" ❌ {e}")


def process_book(book_hash: str, file_entry: Dict) -> Optional[Dict]:
    """
    Extract paragraphs, chunk, embed for ONE book.
    
    Returns:
        {
            "book_hash": "abc123",
            "chunks": [
                {
                    "chunk_id": "ch_...",
                    "text": "...",
                    "source": {...},
                    "embedding": [...]
                }
            ]
        }
        or None if failed
    """
    file_path = Path(file_entry["path"])
    filetype = file_entry["filetype"]
    
    print(f"   Processing: {file_path.name}...", end='', flush=True)
    
    # Extract paragraphs
    try:
        if filetype == 'epub':
            paragraphs = extract_epub_paragraphs(file_path)
        elif filetype == 'pdf':
            paragraphs = extract_pdf_paragraphs(file_path)
        else:
            move_to_no_indexing(file_path, f"Unsupported: {filetype}")
            return None
    except Exception as e:
        move_to_no_indexing(file_path, f"Extraction failed: {e}")
        return None
    
    if not paragraphs:
        move_to_no_indexing(file_path, "No paragraphs")
        return None
    
    # Chunk
    chunks = chunk_paragraphs(paragraphs, max_chars=1024)
    if not chunks:
        move_to_no_indexing(file_path, "No chunks")
        return None
    
    # Embed
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
        
        chunk_objects.append({
            "chunk_id": chunk_id,
            "book_hash": book_hash,
            "text": text,
            "source": chunk["source"],
            "paragraphs": chunk["paragraphs"],
            "embedding": embedding.tolist()
        })
    
    print(f" ✓ {len(chunk_objects)} chunks")
    
    return {
        "book_hash": book_hash,
        "chunks": chunk_objects
    }


# ============================================================================
# FAISS OPERATIONS (append-only)
# ============================================================================

def append_to_faiss(new_chunks: List[Dict], state: Dict) -> faiss.Index:
    """
    Append new embeddings to FAISS index (or create if missing).
    
    Returns:
        Updated FAISS index
    """
    # Load existing index or create new
    if FAISS_INDEX_PATH.exists():
        print(f"   Loading existing FAISS index...")
        index = faiss.read_index(str(FAISS_INDEX_PATH))
        print(f"   Current size: {index.ntotal:,} vectors")
    else:
        print(f"   Creating new FAISS index...")
        index = faiss.IndexFlatIP(EMBEDDING_DIM)
    
    if not new_chunks:
        return index
    
    # Prepare embeddings
    embeddings = np.array([c["embedding"] for c in new_chunks], dtype="float32")
    faiss.normalize_L2(embeddings)
    
    # Append to index
    start_offset = index.ntotal
    index.add(embeddings)
    
    print(f"   ✓ Appended {len(new_chunks)} vectors ({start_offset:,} → {index.ntotal:,})")
    
    return index


def save_faiss_and_metadata(index: faiss.Index, all_chunks: List[Dict], state: Dict):
    """Save FAISS index + metadata atomically."""
    print(f"\n   Saving FAISS index...")
    
    # 1. FAISS index
    temp_index = tempfile.NamedTemporaryFile(delete=False, dir=LIBRARY_ROOT)
    faiss.write_index(index, temp_index.name)
    os.replace(temp_index.name, FAISS_INDEX_PATH)
    
    # 2. Metadata (chunks without embeddings + book info)
    books_meta = []
    for book_hash, book_info in state["books"].items():
        books_meta.append({
            "id": book_hash,
            "title": Path(book_info["path"]).stem,
            "filename": Path(book_info["path"]).name,
            "path": book_info["path"],
            "chunk_count": book_info["chunk_count"]
        })
    
    metadata = {
        "books": books_meta,
        "chunks": [
            {k: v for k, v in c.items() if k != "embedding"}
            for c in all_chunks
        ]
    }
    
    temp_meta = tempfile.NamedTemporaryFile("w", delete=False, dir=LIBRARY_ROOT)
    json.dump(metadata, temp_meta, indent=2)
    temp_meta.flush()
    os.fsync(temp_meta.fileno())
    temp_meta.close()
    os.replace(temp_meta.name, METADATA_PATH)
    
    faiss_size = FAISS_INDEX_PATH.stat().st_size / 1024 / 1024
    meta_size = METADATA_PATH.stat().st_size / 1024 / 1024
    
    print(f"   ✓ FAISS: {faiss_size:.1f} MB")
    print(f"   ✓ Metadata: {meta_size:.1f} MB")


# ============================================================================
# MAIN INCREMENTAL INDEXER
# ============================================================================

def index_incremental():
    """
    Incremental indexer: O(Δ new books), not O(N total books).
    """
    print("\n🚀 Incremental indexer (folder-agnostic, content-addressed)")
    
    # 1. Load index state FIRST (needed for fingerprint cache)
    print("\n📊 Loading index state...")
    state = load_index_state()
    print(f"   Indexed: {state['total_books']} books, {state['total_chunks']:,} chunks")
    
    # 2. Discover current filesystem state (with fingerprint caching)
    print("\n📁 Scanning filesystem...")
    current_fs = scan_filesystem(state)  # Pass state for cache access
    print(f"   Found {len(current_fs)} books on disk")
    
    # 3. Compute diff
    print("\n🔍 Computing diff...")
    diff = compute_diff(current_fs, state)
    
    print(f"   New books: {len(diff['new'])}")
    print(f"   Moved: {len(diff['moved'])}")
    print(f"   Deleted: {len(diff['deleted'])}")
    
    # 4. Handle moved files (metadata update only)
    if diff["moved"]:
        print(f"\n📦 Updating paths for {len(diff['moved'])} moved books...")
        for book_hash, new_path in diff["moved"].items():
            state["books"][book_hash]["path"] = new_path
        save_index_state(state)
    
    # 5. Handle deleted files
    if diff["deleted"]:
        print(f"\n🗑️  Removing {len(diff['deleted'])} deleted books from index...")
        for book_hash in diff["deleted"]:
            del state["books"][book_hash]
        # Note: FAISS vectors stay (append-only), but metadata removed
        # Full rebuild needed to reclaim space (rare operation)
    
    # 6. Process NEW books only
    if not diff["new"]:
        print("\n✅ No new books to index")
        if diff["moved"] or diff["deleted"]:
            save_index_state(state)
        return
    
    print(f"\n🆕 Processing {len(diff['new'])} new books...")
    
    new_chunks_all = []
    chunk_offset = state["total_chunks"]
    processed_count = 0
    
    for book_hash in diff["new"]:
        file_entry = current_fs[book_hash]
        result = process_book(book_hash, file_entry)
        
        if result:
            chunks = result["chunks"]
            chunk_count = len(chunks)
            
            # Update state
            state["books"][book_hash] = {
                "path": file_entry["path"],
                "indexed_at": time.time(),
                "chunk_range": [chunk_offset, chunk_offset + chunk_count],
                "chunk_count": chunk_count
            }
            
            chunk_offset += chunk_count
            new_chunks_all.extend(chunks)
            processed_count += 1
            
            # CHECKPOINT: Save every 10 books (resumable on crash)
            if processed_count % 10 == 0:
                print(f"   ✅ Checkpoint: {processed_count}/{len(diff['new'])} books processed")
                save_index_state(state)
    
    if not new_chunks_all:
        print("\n⚠️  No valid chunks from new books")
        return
    
    # 7. Append to FAISS
    print(f"\n➕ Appending {len(new_chunks_all)} new chunks to FAISS...")
    
    # Load all existing chunks (needed for metadata.json)
    if METADATA_PATH.exists():
        with open(METADATA_PATH) as f:
            existing_meta = json.load(f)
            all_chunks = existing_meta.get("chunks", [])
    else:
        all_chunks = []
    
    # Add new chunks
    all_chunks.extend(new_chunks_all)
    
    # Append to FAISS
    index = append_to_faiss(new_chunks_all, state)
    
    # 8. Save everything
    state["total_chunks"] = len(all_chunks)
    state["total_books"] = len(state["books"])
    state["last_updated"] = time.time()
    
    save_faiss_and_metadata(index, all_chunks, state)
    save_index_state(state)
    
    print(f"\n✅ Index updated")
    print(f"   Total books: {state['total_books']}")
    print(f"   Total chunks: {state['total_chunks']:,}")


if __name__ == "__main__":
    index_incremental()
