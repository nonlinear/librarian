#!/usr/bin/env python3
"""
Partition Storage by Topic

Splits monolithic FAISS index + chunks into topic-specific files:
  storage/ai/faiss.index + chunks.pkl
  storage/activism/faiss.index + chunks.pkl
  etc.

Enables lazy loading: only load relevant topic per query.
"""

import json
import pickle
from pathlib import Path
from collections import defaultdict

import faiss
import numpy as np

# Paths
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"
FAISS_INDEX_FILE = STORAGE_DIR / "faiss.index"
CHUNKS_FILE = STORAGE_DIR / "chunks_binary.pkl"

def main():
    print("="*60)
    print("Partitioning Storage by Topic")
    print("="*60)

    # 1. Load metadata
    print("\n1. Loading metadata...")
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    topics = [t['id'] for t in metadata['topics']]
    print(f"   Found {len(topics)} topics: {', '.join(topics)}")

    # 2. Load FAISS index
    print("\n2. Loading FAISS index...")
    index = faiss.read_index(str(FAISS_INDEX_FILE))
    print(f"   Loaded {index.ntotal} vectors")

    # 3. Load chunks
    print("\n3. Loading chunks...")
    with open(CHUNKS_FILE, 'rb') as f:
        chunks = pickle.load(f)
    print(f"   Loaded {len(chunks)} chunks")

    # 4. Group by topic
    print("\n4. Grouping by topic...")
    topic_chunks = defaultdict(list)
    topic_indices = defaultdict(list)

    for idx, chunk in enumerate(chunks):
        topic_id = chunk['metadata']['topic_id']
        topic_chunks[topic_id].append(chunk)
        topic_indices[topic_id].append(idx)

    for topic_id in topics:
        count = len(topic_chunks[topic_id])
        print(f"   {topic_id}: {count} chunks")

    # 5. Create partitioned storage
    print("\n5. Creating partitioned storage...")

    # Get all vectors from FAISS
    all_vectors = []
    for i in range(index.ntotal):
        vector = index.reconstruct(int(i))
        all_vectors.append(vector)

    for topic_id in topics:
        topic_dir = STORAGE_DIR / topic_id
        topic_dir.mkdir(exist_ok=True)

        # Get topic chunks and vectors
        topic_chunk_list = topic_chunks[topic_id]
        topic_idx_list = topic_indices[topic_id]

        if not topic_chunk_list:
            print(f"   ⚠️  {topic_id}: No chunks, skipping")
            continue

        # Create topic FAISS index
        topic_vectors = [all_vectors[i] for i in topic_idx_list]
        topic_vectors_array = np.vstack(topic_vectors)

        dimension = topic_vectors_array.shape[1]
        topic_index = faiss.IndexFlatL2(dimension)
        topic_index.add(topic_vectors_array)

        # Save topic FAISS index
        topic_faiss_file = topic_dir / "faiss.index"
        faiss.write_index(topic_index, str(topic_faiss_file))

        # Save topic chunks
        topic_chunks_file = topic_dir / "chunks.pkl"
        with open(topic_chunks_file, 'wb') as f:
            pickle.dump(topic_chunk_list, f)

        # Stats
        faiss_size = topic_faiss_file.stat().st_size / 1024
        chunks_size = topic_chunks_file.stat().st_size / 1024 / 1024

        print(f"   ✅ {topic_id}: {len(topic_chunk_list)} chunks, {faiss_size:.1f}KB FAISS, {chunks_size:.2f}MB chunks")

    # 6. Summary
    print("\n" + "="*60)
    print("✅ Partitioning Complete!")
    print("="*60)
    print(f"Created {len(topics)} topic-specific storage directories")
    print("\nStructure:")
    print("  storage/")
    print("    metadata.json (19KB - always loaded)")
    for topic_id in topics:
        topic_dir = STORAGE_DIR / topic_id
        if topic_dir.exists():
            print(f"    {topic_id}/")
            print(f"      faiss.index (lazy loaded)")
            print(f"      chunks.pkl (lazy loaded)")
    print("\n💡 MCP startup = instant (only metadata.json)")
    print("💡 Query loads only 1 topic (~2-4MB)")
    print("="*60)


if __name__ == "__main__":
    main()
