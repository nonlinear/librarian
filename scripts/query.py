#!/usr/bin/env python3
"""
Query the indexed book library.

Usage:
  python3.11 scripts/query.py "your question here"
  python3.11 scripts/query.py --book "book_id" "your question"
  python3.11 scripts/query.py --topic "topic_id" "your question"
"""

import json
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# Paths
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"
INDEX_FILE = STORAGE_DIR / "faiss.index"
DOCSTORE_FILE = STORAGE_DIR / "docstore.json"

# Model
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# Query settings
TOP_K = 5  # Number of chunks to retrieve


class Timer:
    """Context manager for timing operations."""
    def __init__(self, name: str, silent: bool = False):
        self.name = name
        self.silent = silent
        self.elapsed = 0

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed = time.time() - self.start
        if not self.silent:
            print(f"⏱️  {self.name}: {self.elapsed*1000:.1f}ms")


def load_index_and_metadata():
    """Load FAISS index, docstore, and metadata."""
    print("📚 Loading index...")

    with Timer("Load FAISS index"):
        index = faiss.read_index(str(INDEX_FILE))

    with Timer("Load docstore"):
        with open(DOCSTORE_FILE, 'r', encoding='utf-8') as f:
            docstore = json.load(f)
        # Convert string keys back to int
        docstore = {int(k): v for k, v in docstore.items()}

    with Timer("Load metadata"):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    print(f"   Vectors: {index.ntotal:,}")
    print(f"   Books: {sum(len(t['books']) for t in metadata['topics'])}")
    print()

    return index, docstore, metadata


def load_embedding_model():
    """Load the embedding model."""
    print(f"🤖 Loading embedding model: {EMBEDDING_MODEL}")
    with Timer("Model load"):
        model = SentenceTransformer(EMBEDDING_MODEL)
    print()
    return model


def filter_by_book_or_topic(
    docstore: Dict,
    book_id: Optional[str] = None,
    topic_id: Optional[str] = None
) -> List[int]:
    """
    Get list of valid indices filtered by book or topic.

    Returns list of docstore indices that match the filter.
    """
    if not book_id and not topic_id:
        return list(docstore.keys())

    valid_indices = []
    for idx, doc in docstore.items():
        if book_id and doc['book_id'] == book_id:
            valid_indices.append(idx)
        elif topic_id and doc['topic_id'] == topic_id:
            valid_indices.append(idx)

    return valid_indices


def query(
    question: str,
    model: SentenceTransformer,
    index: faiss.Index,
    docstore: Dict,
    metadata: Dict,
    book_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    top_k: int = TOP_K
) -> List[Dict]:
    """
    Query the index and return top results.

    Returns list of result dicts with chunk text and metadata.
    """
    # Generate query embedding
    with Timer("Generate query embedding", silent=True) as t_embed:
        query_embedding = model.encode([question], convert_to_numpy=True)

    # Search FAISS
    with Timer("FAISS search", silent=True) as t_search:
        distances, indices = index.search(query_embedding.astype('float32'), top_k * 10)

    # Filter results if needed
    results = []
    valid_indices = filter_by_book_or_topic(docstore, book_id, topic_id) if (book_id or topic_id) else None

    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:  # FAISS returns -1 for empty results
            continue

        # Apply filter
        if valid_indices is not None and idx not in valid_indices:
            continue

        if idx not in docstore:
            continue

        doc = docstore[idx]

        results.append({
            'distance': float(dist),
            'similarity': 1 / (1 + dist),  # Convert L2 distance to similarity
            'chunk_text': doc['chunk_full'],
            'book_title': doc['book_title'],
            'book_author': doc['book_author'],
            'topic_label': doc['topic_label'],
            'chunk_index': doc['chunk_index']
        })

        if len(results) >= top_k:
            break

    # Print timing
    print(f"⏱️  Query latency: {(t_embed.elapsed + t_search.elapsed)*1000:.1f}ms")
    print(f"   └─ Embedding: {t_embed.elapsed*1000:.1f}ms")
    print(f"   └─ Search: {t_search.elapsed*1000:.1f}ms")
    print()

    return results


def display_results(results: List[Dict]):
    """Pretty print query results."""
    if not results:
        print("❌ No results found")
        return

    print(f"📖 Top {len(results)} results:")
    print("=" * 80)
    print()

    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['book_title']} — {result['book_author']}")
        print(f"    Topic: {result['topic_label']} | Chunk #{result['chunk_index']}")
        print(f"    Similarity: {result['similarity']:.3f}")
        print()
        # Show preview (first 400 chars)
        preview = result['chunk_text'][:400]
        if len(result['chunk_text']) > 400:
            preview += "..."
        print(f"    {preview}")
        print()
        print("-" * 80)
        print()


def find_book_id(metadata: Dict, query: str) -> Optional[str]:
    """Find book ID by partial title match."""
    query_lower = query.lower()
    for topic in metadata['topics']:
        for book in topic['books']:
            if query_lower in book['title'].lower() or query_lower in book['id']:
                return book['id']
    return None


def find_topic_id(metadata: Dict, query: str) -> Optional[str]:
    """Find topic ID by partial label match."""
    query_lower = query.lower()
    for topic in metadata['topics']:
        if query_lower in topic['label'].lower() or query_lower in topic['id']:
            return topic['id']
    return None


def main():
    parser = argparse.ArgumentParser(description='Query the book library')
    parser.add_argument('question', help='Your question')
    parser.add_argument('--book', help='Filter by book (title or ID)')
    parser.add_argument('--topic', help='Filter by topic (label or ID)')
    parser.add_argument('--top-k', type=int, default=TOP_K, help='Number of results')

    args = parser.parse_args()

    print("🔍 Personal Library MCP - Query")
    print("=" * 80)
    print()

    # Load everything
    index, docstore, metadata = load_index_and_metadata()
    model = load_embedding_model()

    # Resolve book/topic filters
    book_id = None
    topic_id = None

    if args.book:
        book_id = find_book_id(metadata, args.book)
        if book_id:
            print(f"🔎 Filtering by book: {book_id}")
        else:
            print(f"⚠️  Book not found: {args.book}")
            return

    if args.topic:
        topic_id = find_topic_id(metadata, args.topic)
        if topic_id:
            print(f"🔎 Filtering by topic: {topic_id}")
        else:
            print(f"⚠️  Topic not found: {args.topic}")
            return

    # Query
    print(f"❓ Question: {args.question}")
    print()

    results = query(
        args.question,
        model,
        index,
        docstore,
        metadata,
        book_id=book_id,
        topic_id=topic_id,
        top_k=args.top_k
    )

    # Display
    display_results(results)


if __name__ == "__main__":
    main()
