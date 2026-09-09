#!/usr/bin/env python3
"""
Merge all sub-indexes (.faiss.index) into a single aggregate FAISS index.
Rebuilds metadata.json from individual book metadata files in each category.
Runs INSIDE the librarian Docker container where faiss is available.

The corpus path is provided by the environment/configuration (LIBRARIAN_BOOKS or
resolved config), not hardcoded. Example inside the container:

    docker run --rm -v <your-books-dir>:/app/books -e LIBRARIAN_BOOKS=/app/books \
        librarian-librarian python3 /app/engine/scripts/merge-indexes.py
"""
import os, sys, json, faiss, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/ for config
from config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merge-indexes")

BOOKS_DIR = get_config().corpus_path

def find_sub_indexes():
    """Find all .faiss.index files at any depth."""
    return sorted(BOOKS_DIR.rglob(".faiss.index"))

def collect_metadata():
    """Collect all metadata.json files and merge into one."""
    merged = {}
    for meta_file in BOOKS_DIR.rglob("metadata.json"):
        try:
            data = json.loads(meta_file.read_text())
            # Each metadata.json might contain dict of book_hash -> metadata
            if isinstance(data, dict):
                merged.update(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "book_hash" in item:
                        merged[item["book_hash"]] = item
        except Exception as e:
            logger.warning(f"Error reading {meta_file}: {e}")
    return merged

def main():
    sub_indexes = find_sub_indexes()
    logger.info(f"Found {len(sub_indexes)} sub-indexes")
    
    if not sub_indexes:
        logger.error("No sub-indexes found. Nothing to merge.")
        sys.exit(1)
    
    # Load first index to get dimension
    first = faiss.read_index(str(sub_indexes[0]))
    dim = first.d
    logger.info(f"First index: {first.ntotal} vectors, dim={dim}, type={type(first).__name__}")
    
    # Collect all vectors and IDs
    all_vectors = []
    all_ids = []
    total = 0
    offset = 0
    
    for si in sub_indexes:
        idx = faiss.read_index(str(si))
        if idx.d != dim:
            logger.warning(f"Dimension mismatch: {si.parent.name} has dim={idx.d}, skipping")
            continue
        n = idx.ntotal
        if n == 0:
            continue
        
        # Get vectors
        ids = faiss.IDSelectorArray(range(n))
        vectors = idx.reconstruct_n(0, n)
        
        all_vectors.append(vectors)
        new_ids = list(range(offset, offset + n))
        all_ids.extend(new_ids)
        
        logger.info(f"  {si.parent.name}: {n} vectors → offset {offset}")
        offset += n
        total += n
    
    if total == 0:
        logger.error("No vectors collected. Nothing to merge.")
        sys.exit(1)
    
    # Build aggregate index
    import numpy as np
    all_vectors_np = np.vstack(all_vectors)
    logger.info(f"Total vectors: {total}, shape: {all_vectors_np.shape}")
    
    # Create inner index + IDMap
    inner = faiss.IndexFlatIP(dim)
    index = faiss.IndexIDMap(inner)
    index.add_with_ids(all_vectors_np, np.array(all_ids, dtype=np.int64))
    
    # Write aggregate index
    index_path = BOOKS_DIR / "faiss.index"
    faiss.write_index(index, str(index_path))
    logger.info(f"✅ Aggregate index written: {index_path} ({index.ntotal:,} vectors)")
    
    # Collect and write metadata
    metadata = collect_metadata()
    meta_path = BOOKS_DIR / "metadata.json"
    if metadata:
        meta_path.write_text(json.dumps(metadata, indent=2))
        logger.info(f"✅ Metadata written: {meta_path} ({len(metadata)} books)")
    else:
        logger.warning("⚠️ No metadata collected. Server will start but search will lack book titles.")
    
    # Write index state
    state = {
        "version": 6,
        "vectors_written": total,
        "files": {},
        "metadata": metadata if metadata else {}
    }
    state_path = BOOKS_DIR / "index_state.json"
    state_path.write_text(json.dumps(state, indent=2))
    logger.info(f"✅ Index state written: {state_path}")
    
    logger.info(f"\n🎉 Merge complete! {total:,} vectors from {len(sub_indexes)} sub-indexes.")

if __name__ == "__main__":
    main()
