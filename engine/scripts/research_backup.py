#!/usr/bin/env python3
"""
CLI wrapper for Librarian partitioned storage.
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
PROJECT_DIR = SCRIPT_DIR.parent.parent  # engine/scripts/ -> engine/ -> project root
BOOKS_DIR = PROJECT_DIR / "books"
MODELS_DIR = SCRIPT_DIR.parent / "models"  # engine/models/
METADATA_FILE = BOOKS_DIR / ".library-index.json"

# Set model cache to local engine/models/ directory
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(MODELS_DIR)

# Load local embedding model (384-dim)
EMBEDDING_MODEL = SentenceTransformer('BAAI/bge-small-en-v1.5')

def load_metadata():
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_topic(topic_id):
    """Load FAISS index + chunks for a topic (v2.0 structure)."""
    # Get topic path from library-index.json
    metadata = load_metadata()
    topic_path = None
    for topic in metadata['topics']:
        if topic['id'] == topic_id:
            topic_path = topic.get('path')  # v2.0 uses 'path' not 'folder_path'
            break
    if not topic_path:
        return None

    topic_dir = BOOKS_DIR / topic_path

    faiss_file = topic_dir / ".faiss.index"
    chunks_file_json = topic_dir / ".chunks.json"
    topic_index_file = topic_dir / ".topic-index.json"

    if not faiss_file.exists() or not chunks_file_json.exists():
        return None

    # Load FAISS index
    index = faiss.read_index(str(faiss_file))

    # Load chunks
    with open(chunks_file_json, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Load topic-index.json for book metadata
    book_metadata = {}
    if topic_index_file.exists():
        with open(topic_index_file, 'r', encoding='utf-8') as f:
            topic_meta = json.load(f)
            for book in topic_meta.get('books', []):
                book_metadata[book['id']] = book

    return {
        'index': index,
        'chunks': chunks,
        'book_metadata': book_metadata,
        'topic_path': topic_path
    }

def get_embedding(text):
    """Get local embedding for text."""
    return EMBEDDING_MODEL.encode(text, convert_to_numpy=True).astype(np.float32)

def query_library(query, topic=None, book=None, k=5):
    """Query the library and return top-k results.

    Args:
        query: Search query string
        topic: Filter by topic ID (optional)
        book: Filter by book filename (optional)
        k: Number of results to return
    """
    metadata = load_metadata()

    # Find topic
    topic_id = None
    if topic:
        for t in metadata['topics']:
            # v2.0: topics only have 'id' and 'path', no 'label'
            if t['id'] == topic or topic.lower() in t['id'].lower():
                topic_id = t['id']
                break

    if not topic_id:
        # Default to first topic with data
        for t in metadata['topics']:
            topic_dir = BOOKS_DIR / t['id']
            if (topic_dir / ".faiss.index").exists():
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

    # Use book metadata from topic-index.json (v2.0)
    book_metadata = topic_data.get('book_metadata', {})
    topic_path = topic_data.get('topic_path', topic_id)

    # Format results with filename and relative path
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(topic_data['chunks']):
            chunk = topic_data['chunks'][idx]
            book_id = chunk.get('book_id')

            # Get book info from topic-index.json (v2.0)
            book_info = book_metadata.get(book_id, {})
            filename = book_info.get('filename', chunk.get('filename', ''))

            # Compute relative path from workspace root to book file
            rel_path = os.path.join('../librarian/books', topic_path, filename) if filename and topic_path else ''

            # Extract page/paragraph (chunks v2.0)
            page = chunk.get('page')  # PDF page number or None
            chapter = chunk.get('chapter')  # EPUB chapter or None
            paragraph = chunk.get('paragraph')  # Paragraph number
            filetype = chunk.get('filetype', 'unknown')

            # Build location string
            location = None
            if filetype == 'pdf' and page:
                if paragraph:
                    location = f"p.{page}, ¶{paragraph}"
                else:
                    location = f"p.{page}"
            elif filetype == 'epub' and chapter:
                if paragraph:
                    location = f"{chapter}, ¶{paragraph}"
                else:
                    location = chapter

            results.append({
                'text': chunk.get('chunk_full', ''),
                'book_title': chunk.get('book_title', ''),
                'topic': topic_id,
                'similarity': float(1 - dist),  # Convert distance to similarity
                'filename': filename,
                'folder_path': topic_path,  # Use topic path from v2.0
                'relative_path': rel_path,
                'location': location,  # NEW: page/paragraph
                'page': page,
                'chapter': chapter,
                'paragraph': paragraph,
                'filetype': filetype
            })

    # Filter by book if specified
    if book:
        results = [r for r in results if r['filename'] == book]

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='Search query')
    parser.add_argument('--topic', help='Filter by topic ID')
    parser.add_argument('--book', help='Filter by book filename (e.g. "Book.pdf")')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results')

    args = parser.parse_args()

    try:
        results = query_library(
            query=args.query,
            topic=args.topic,
            book=args.book,
            k=args.top_k
        )
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
