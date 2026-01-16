#!/usr/bin/env python3
"""
Convert JSON docstore to binary pickle format.

Simply converts existing docstore.json → chunks_binary.pkl
WITHOUT reindexing or re-embedding. Instant conversion.
"""

import json
import pickle
from pathlib import Path

# Paths
STORAGE_DIR = Path(__file__).parent.parent / "storage"
DOCSTORE_JSON = STORAGE_DIR / "docstore.json"
CHUNKS_BINARY = STORAGE_DIR / "chunks_binary.pkl"

def main():
    print("Converting JSON docstore to binary pickle...")

    # Read JSON
    print(f"\n1. Reading {DOCSTORE_JSON}...")
    with open(DOCSTORE_JSON, 'r') as f:
        docstore = json.load(f)

    print(f"   Loaded {len(docstore)} chunks")

    # Convert to list format
    print("\n2. Converting format...")
    chunks_list = []
    for idx, chunk_data in docstore.items():
        chunks_list.append(chunk_data)

    # Save as pickle
    print(f"\n3. Saving to {CHUNKS_BINARY}...")
    with open(CHUNKS_BINARY, 'wb') as f:
        pickle.dump(chunks_list, f)

    # Stats
    json_size = DOCSTORE_JSON.stat().st_size / 1024 / 1024
    pickle_size = CHUNKS_BINARY.stat().st_size / 1024 / 1024

    print("\n" + "="*60)
    print("✅ Conversion Complete!")
    print("="*60)
    print(f"Chunks: {len(chunks_list)}")
    print(f"JSON size: {json_size:.2f} MB")
    print(f"Pickle size: {pickle_size:.2f} MB")
    print(f"Reduction: {((json_size - pickle_size) / json_size * 100):.1f}%")
    print("="*60)
    print("\nYou can now use chunks_binary.pkl with FAISS!")
    print("Existing faiss.index still works - no need to reindex.")


if __name__ == "__main__":
    main()
