#!/usr/bin/env python3
"""
CLI wrapper for Personal Library partitioned storage.
Called by VS Code extension - returns JSON results.
"""
import sys
import json
import argparse
import pickle
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os

# Paths
SCRIPT_DIR = Path(__file__).parent
STORAGE_DIR = SCRIPT_DIR.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"

# Load local embedding model (384-dim)
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

def load_metadata():
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_topic(topic_id):
    """Load FAISS index + chunks for a topic."""
    topic_dir = STORAGE_DIR / topic_id
    faiss_file = topic_dir / "faiss.index"
    chunks_file = topic_dir / "chunks.pkl"

    if not faiss_file.exists() or not chunks_file.exists():
        return None

    index = faiss.read_index(str(faiss_file))
    with open(chunks_file, 'rb') as f:
        chunks = pickle.load(f)

    return {'index': index, 'chunks': chunks}

def get_embedding(text):
    """Get local embedding for text."""
    return EMBEDDING_MODEL.encode(text, convert_to_numpy=True).astype(np.float32)

def query_library(query, topic=None, k=5):
    """Query the library."""
    metadata = load_metadata()

    # Find topic
    topic_id = None
    if topic:
        for t in metadata['topics']:
            if t['id'] == topic or topic.lower() in t['label'].lower():
                topic_id = t['id']
                break

    if not topic_id:
        # Default to first topic with data
        for t in metadata['topics']:
            topic_dir = STORAGE_DIR / t['id']
            if (topic_dir / "faiss.index").exists():
                topic_id = t['id']
                break

    if not topic_id:
        return []

    # Load topic data
    topic_data = load_topic(topic_id)
    if not topic_data:
        return []

    # Get embedding and search
    query_embedding = get_embedding(query)
    distances, indices = topic_data['index'].search(
        query_embedding.reshape(1, -1),
        k
    )

    # Format results
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(topic_data['chunks']):
            chunk = topic_data['chunks'][idx]
            results.append({
                'text': chunk['text'],
                'book_title': chunk.get('book_title', ''),
                'topic': topic_id,
                'similarity': float(1 - dist)  # Convert distance to similarity
            })

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='Search query')
    parser.add_argument('--topic', help='Topic filter')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results')

    args = parser.parse_args()

    try:
        results = query_library(
            query=args.query,
            topic=args.topic,
            k=args.top_k
        )
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
