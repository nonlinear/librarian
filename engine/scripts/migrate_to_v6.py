#!/usr/bin/env python3
"""
Migrate existing index to v6 format with file cache.

One-time migration: metadata.json → .index_state.json
"""
import json
import os
from pathlib import Path

LIBRARY_ROOT = Path("/app/books")
METADATA_PATH = LIBRARY_ROOT / "metadata.json"
INDEX_STATE_PATH = LIBRARY_ROOT / ".index_state.json"

print("🔄 Migrating to v6 index state...")

# Load existing metadata
with open(METADATA_PATH) as f:
    metadata = json.load(f)

books = metadata.get("books", [])
chunks = metadata.get("chunks", [])

print(f"Found {len(books)} books, {len(chunks):,} chunks")

# Build index state
state = {
    "file_cache": {},  # Will be populated on next scan
    "books": {},
    "total_chunks": len(chunks),
    "total_books": len(books),
    "last_updated": 0
}

# Group chunks by book
chunk_offset = 0
for book in books:
    book_id = book["id"]
    book_chunks = [c for c in chunks if c.get("book_id") == book_id or c.get("book_hash") == book_id]
    chunk_count = len(book_chunks)
    
    state["books"][book_id] = {
        "path": book["path"],
        "indexed_at": 0,
        "chunk_range": [chunk_offset, chunk_offset + chunk_count],
        "chunk_count": chunk_count
    }
    
    chunk_offset += chunk_count
    
    # Add to file cache (size/mtime will be updated on next scan)
    if os.path.exists(book["path"]):
        stat = os.stat(book["path"])
        state["file_cache"][book["path"]] = {
            "fingerprint": [stat.st_size, int(stat.st_mtime)],
            "hash": book_id
        }

# Save
with open(INDEX_STATE_PATH, "w") as f:
    json.dump(state, f, indent=2)

print(f"✅ Created {INDEX_STATE_PATH}")
print(f"   {len(state['books'])} books")
print(f"   {len(state['file_cache'])} file cache entries")
