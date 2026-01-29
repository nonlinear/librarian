#!/usr/bin/env python3
"""
CLI wrapper for Librarian partitioned storage.
Called by VS Code extension - returns JSON results.

v1.2.1 Enhancements:
1. BGE Reranking - Cross-encoder reranking for better relevance
2. Context Expansion - Return neighboring chunks for readability
3. Result Deduplication - Group by book, limit per-book
4. Query Enhancement - Query expansion for better recall
5. Metadata Support - Full page/chapter/paragraph display
"""
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder
import os
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent  # engine/scripts/ -> engine/ -> project root
BOOKS_DIR = PROJECT_DIR / "books"
MODELS_DIR = SCRIPT_DIR.parent / "models"  # engine/models/
METADATA_FILE = BOOKS_DIR / ".library-index.json"

# Set model cache to local engine/models/ directory
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(MODELS_DIR)

# Load models
EMBEDDING_MODEL = SentenceTransformer('BAAI/bge-small-en-v1.5')

# BGE Reranker - uses cross-encoder for better relevance
# Will load lazily when needed
RERANKER_MODEL = None

def get_reranker():
    """Lazy load reranker model"""
    global RERANKER_MODEL
    if RERANKER_MODEL is None:
        try:
            # BGE reranker models: bge-reranker-base, bge-reranker-large
            RERANKER_MODEL = CrossEncoder('BAAI/bge-reranker-base', max_length=512)
            print("✓ Loaded BGE reranker", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Reranker unavailable: {e}", file=sys.stderr)
            RERANKER_MODEL = False  # Mark as unavailable
    return RERANKER_MODEL if RERANKER_MODEL is not False else None

# Query expansion synonyms (simple approach)
QUERY_EXPANSIONS = {
    'commons': ['commons', 'shared resources', 'collective action', 'common pool'],
    'governance': ['governance', 'management', 'coordination', 'administration'],
    'knowledge': ['knowledge', 'information', 'data', 'expertise'],
    'community': ['community', 'collective', 'group', 'society'],
    'volunteer': ['volunteer', 'unpaid', 'civic engagement', 'contribution'],
}

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

def expand_query(query: str, expand: bool = False) -> str:
    """
    Expand query with synonyms for better recall.

    Args:
        query: Original query string
        expand: Whether to expand (default: False)

    Returns:
        Expanded query string
    """
    if not expand:
        return query

    words = query.lower().split()
    expanded_terms = []

    for word in words:
        if word in QUERY_EXPANSIONS:
            # Add all synonyms
            expanded_terms.extend(QUERY_EXPANSIONS[word])
        else:
            expanded_terms.append(word)

    # Deduplicate while preserving some order
    seen = set()
    result = []
    for term in expanded_terms:
        if term not in seen:
            seen.add(term)
            result.append(term)

    return ' '.join(result)

def get_context_window(chunks: List[Dict], idx: int, window_size: int = 1) -> Tuple[str, str, str]:
    """
    Get surrounding context for a chunk.

    Args:
        chunks: List of all chunks
        idx: Index of target chunk
        window_size: Number of chunks before/after to include

    Returns:
        (before_text, current_text, after_text)
    """
    before_chunks = []
    after_chunks = []

    current_chunk = chunks[idx]
    current_book_id = current_chunk.get('book_id')

    # Get chunks before (same book only)
    for i in range(max(0, idx - window_size), idx):
        if chunks[i].get('book_id') == current_book_id:
            before_chunks.append(chunks[i].get('chunk_full', ''))

    # Get chunks after (same book only)
    for i in range(idx + 1, min(len(chunks), idx + window_size + 1)):
        if chunks[i].get('book_id') == current_book_id:
            after_chunks.append(chunks[i].get('chunk_full', ''))

    before_text = '\n\n'.join(before_chunks) if before_chunks else ''
    current_text = current_chunk.get('chunk_full', '')
    after_text = '\n\n'.join(after_chunks) if after_chunks else ''

    return before_text, current_text, after_text

def rerank_results(query: str, results: List[Tuple[int, float, Dict]]) -> List[Tuple[int, float, Dict]]:
    """
    Rerank results using BGE cross-encoder.

    Args:
        query: Search query
        results: List of (idx, score, chunk) tuples

    Returns:
        Reranked list of (idx, new_score, chunk) tuples
    """
    reranker = get_reranker()
    if not reranker:
        # Reranker unavailable, return as-is
        return results

    # Prepare pairs for reranking
    pairs = [[query, chunk.get('chunk_full', '')] for _, _, chunk in results]

    # Get reranker scores
    scores = reranker.predict(pairs)

    # Combine with original results
    reranked = []
    for (idx, _, chunk), new_score in zip(results, scores):
        reranked.append((idx, float(new_score), chunk))

    # Sort by new score (descending)
    reranked.sort(key=lambda x: x[1], reverse=True)

    return reranked

def deduplicate_by_book(results: List[Dict], max_per_book: int = 2) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Deduplicate results, keeping max N per book.

    Args:
        results: List of result dictionaries
        max_per_book: Maximum results per book

    Returns:
        (deduplicated_results, book_distribution)
    """
    book_counts = defaultdict(int)
    deduped = []

    for result in results:
        book_title = result.get('book_title', 'Unknown')

        if book_counts[book_title] < max_per_book:
            deduped.append(result)
            book_counts[book_title] += 1

    # Convert to regular dict for JSON serialization
    distribution = dict(book_counts)

    return deduped, distribution

def query_library(
    query: str,
    topic: Optional[str] = None,
    book: Optional[str] = None,
    k: int = 5,
    rerank: bool = True,
    context_window: int = 1,
    max_per_book: int = 2,
    expand_query_flag: bool = False
):
    """Query the library and return top-k results.

    Args:
        query: Search query string
        topic: Filter by topic ID (optional)
        book: Filter by book filename (optional)
        k: Number of results to return
        rerank: Use BGE reranker (default: True)
        context_window: Number of surrounding chunks to include (default: 1)
        max_per_book: Max results per book for deduplication (default: 2)
        expand_query_flag: Expand query with synonyms (default: False)
    """
    metadata = load_metadata()

    # Expand query if requested
    expanded_query = expand_query(query, expand_query_flag)
    if expand_query_flag and expanded_query != query:
        print(f"🔍 Expanded query: {expanded_query}", file=sys.stderr)

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
        return {
            'results': [],
            'metadata': {
                'query': query,
                'expanded_query': expanded_query if expand_query_flag else None,
                'reranked': rerank,
                'context_window': context_window,
                'error': 'No indexed topics found'
            }
        }

    # Load topic data
    topic_data = load_topic(topic_id)
    if not topic_data:
        return {
            'results': [],
            'metadata': {
                'query': query,
                'error': f'Topic {topic_id} not found or not indexed'
            }
        }

    # Get embedding and search
    # Retrieve more candidates if reranking or deduplicating
    if max_per_book is not None and max_per_book < k:
        retrieve_k = k * 3
    elif rerank:
        retrieve_k = k * 2
    else:
        retrieve_k = k

    query_embedding = get_embedding(expanded_query)
    distances, indices = topic_data['index'].search(
        query_embedding.reshape(1, -1),
        retrieve_k
    )

    # Use book metadata from topic-index.json (v2.0)
    book_metadata = topic_data.get('book_metadata', {})
    topic_path = topic_data.get('topic_path', topic_id)
    chunks = topic_data['chunks']

    # Collect initial results
    initial_results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(chunks):
            chunk = chunks[idx]
            similarity = float(1 - dist)  # Convert distance to similarity
            initial_results.append((int(idx), similarity, chunk))

    # Apply reranking if requested
    if rerank:
        initial_results = rerank_results(query, initial_results)
        print(f"✓ Reranked {len(initial_results)} results", file=sys.stderr)

    # Format results with enhanced metadata
    formatted_results = []
    for idx, score, chunk in initial_results:
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

        # Get context window
        before_text, current_text, after_text = get_context_window(chunks, idx, context_window)

        result = {
            'text': current_text,
            'book_title': chunk.get('book_title', ''),
            'topic': topic_id,
            'similarity': score,  # Use reranked score if applicable
            'filename': filename,
            'folder_path': topic_path,  # Use topic path from v2.0
            'relative_path': rel_path,
            'location': location,  # page/paragraph
            'page': page,
            'chapter': chapter,
            'paragraph': paragraph,
            'filetype': filetype
        }

        # Add context if window > 0
        if context_window > 0:
            result['context'] = {
                'before': before_text if before_text else None,
                'after': after_text if after_text else None
            }

        formatted_results.append(result)

    # Filter by book if specified
    if book:
        formatted_results = [r for r in formatted_results if r['filename'] == book]

    # Deduplicate by book
    if max_per_book and max_per_book < k:
        formatted_results, distribution = deduplicate_by_book(formatted_results, max_per_book)
    else:
        # Still track distribution even without deduplication
        distribution = {}
        for r in formatted_results:
            book_title = r.get('book_title', 'Unknown')
            distribution[book_title] = distribution.get(book_title, 0) + 1

    # Trim to requested k
    formatted_results = formatted_results[:k]

    return {
        'results': formatted_results,
        'metadata': {
            'query': query,
            'expanded_query': expanded_query if expand_query_flag else None,
            'topic': topic_id,
            'total_retrieved': len(initial_results),
            'returned': len(formatted_results),
            'reranked': rerank and get_reranker() is not None,
            'context_window': context_window,
            'max_per_book': max_per_book,
            'book_distribution': distribution
        }
    }

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced semantic search with reranking, context, and deduplication'
    )
    parser.add_argument('query', help='Search query')
    parser.add_argument('--topic', help='Filter by topic ID')
    parser.add_argument('--book', help='Filter by book filename (e.g. "Book.pdf")')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--no-rerank', action='store_true', help='Disable BGE reranking')
    parser.add_argument('--context-window', type=int, default=1,
                       help='Number of surrounding chunks (default: 1, 0=disable)')
    parser.add_argument('--max-per-book', type=int, default=2,
                       help='Max results per book (default: 2, 0=unlimited)')
    parser.add_argument('--expand-query', action='store_true',
                       help='Expand query with synonyms')

    args = parser.parse_args()

    try:
        result = query_library(
            query=args.query,
            topic=args.topic,
            book=args.book,
            k=args.top_k,
            rerank=not args.no_rerank,
            context_window=args.context_window,
            max_per_book=args.max_per_book if args.max_per_book > 0 else None,
            expand_query_flag=args.expand_query
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        import traceback
        print(json.dumps({
            'results': [],
            'metadata': {'error': str(e), 'traceback': traceback.format_exc()}
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
