#!/usr/bin/env python3
"""
Partition Storage by Topic

Reads LlamaIndex storage (vector_store.json, docstore.json) and creates
topic-specific FAISS indices for lazy loading:
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
VECTOR_STORE_FILE = STORAGE_DIR / "default__vector_store.json"
DOCSTORE_FILE = STORAGE_DIR / "docstore.json"
INDEX_STORE_FILE = STORAGE_DIR / "index_store.json"

def main():
    print("="*60)
    print("Partitioning LlamaIndex Storage by Topic")
    print("="*60)

    # 1. Load metadata
    print("\n1. Loading metadata...")
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    topics = [t['id'] for t in metadata['topics']]
    print(f"   Found {len(topics)} topics: {', '.join(topics)}")

    # 2. Load LlamaIndex vector store
    print("\n2. Loading vector store...")
    with open(VECTOR_STORE_FILE, 'r') as f:
        vector_store = json.load(f)

    embeddings_dict = vector_store.get('embedding_dict', {})
    print(f"   Loaded {len(embeddings_dict)} embeddings")

    # 3. Load docstore
    print("\n3. Loading docstore...")
    with open(DOCSTORE_FILE, 'r') as f:
        docstore = json.load(f)

    docs = docstore.get('docstore/data', {})
    print(f"   Loaded {len(docs)} documents")


    # 4. Group by topic
    print("\n4. Grouping documents by topic...")
    topic_data = defaultdict(lambda: {'embeddings': [], 'chunks': []})

    # Build book_id → topic_id mapping from metadata
    book_to_topic = {}
    for topic in metadata['topics']:
        for book in topic['books']:
            book_to_topic[book['id']] = topic['id']

    # Process each document
    for doc_id, doc_data in docs.items():
        # Extract book_id from metadata
        doc_metadata = doc_data.get('__data__', {}).get('metadata', {})
        book_id = doc_metadata.get('book_id')

        if not book_id or book_id not in book_to_topic:
            print(f"   ⚠️  Skipping doc {doc_id}: no topic mapping")
            continue

        topic_id = book_to_topic[book_id]

        # Get embedding for this doc
        if doc_id in embeddings_dict:
            embedding = embeddings_dict[doc_id]
            topic_data[topic_id]['embeddings'].append(embedding)

            # Create chunk object
            chunk = {
                'id': doc_id,
                'text': doc_data.get('__data__', {}).get('text', ''),
                'metadata': doc_metadata
            }
            topic_data[topic_id]['chunks'].append(chunk)

    for topic_id in topics:
        count = len(topic_data[topic_id]['chunks'])
        print(f"   {topic_id}: {count} chunks")

    # 5. Create partitioned storage
    print("\n5. Creating partitioned storage...")

    for topic_id in topics:
        topic_dir = STORAGE_DIR / topic_id
        topic_dir.mkdir(exist_ok=True)

        topic_chunks = topic_data[topic_id]['chunks']
        topic_embeddings = topic_data[topic_id]['embeddings']

        if not topic_chunks:
            print(f"   ⚠️  {topic_id}: No chunks, skipping")
            continue

        # Create FAISS index from embeddings
        embeddings_array = np.array(topic_embeddings, dtype=np.float32)
        dimension = embeddings_array.shape[1]

        topic_index = faiss.IndexFlatL2(dimension)
        topic_index.add(embeddings_array)

        # Save FAISS index
        topic_faiss_file = topic_dir / "faiss.index"
        faiss.write_index(topic_index, str(topic_faiss_file))

        # Save chunks
        topic_chunks_file = topic_dir / "chunks.pkl"
        with open(topic_chunks_file, 'wb') as f:
            pickle.dump(topic_chunks, f)

        # Stats
        faiss_size = topic_faiss_file.stat().st_size / 1024
        chunks_size = topic_chunks_file.stat().st_size / 1024 / 1024

        print(f"   ✅ {topic_id}: {len(topic_chunks)} chunks, {faiss_size:.1f}KB FAISS, {chunks_size:.2f}MB chunks")

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
