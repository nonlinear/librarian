#!/usr/bin/env python3
"""
Multi-topic research tool - searches across ALL indexed topics when --topic not specified
"""
import sys
import json
from pathlib import Path
from research import query_library, load_metadata, BOOKS_DIR

def search_all_topics(query, k=5, rerank=True, context_window=1, max_per_book=2):
    """Search across all indexed topics and merge results"""
    metadata = load_metadata()
    
    all_results = []
    
    # Find all indexed topics
    indexed_topics = []
    for topic in metadata['topics']:
        topic_dir = BOOKS_DIR / topic['path']  # FIX: use 'path' not 'id'
        if (topic_dir / ".faiss.index").exists():
            indexed_topics.append(topic['id'])
    
    if not indexed_topics:
        return {
            'results': [],
            'metadata': {
                'query': query,
                'error': 'No indexed topics found'
            }
        }
    
    print(f"🔍 Searching across {len(indexed_topics)} topics...", file=sys.stderr)
    
    # Search each topic
    for topic_id in indexed_topics:
        result = query_library(
            query=query,
            topic=topic_id,
            k=k * 2,  # Get more results per topic for better global ranking
            rerank=rerank,
            context_window=context_window,
            max_per_book=None  # Don't limit per-book yet
        )
        
        if 'results' in result and result['results']:
            for item in result['results']:
                item['source_topic'] = topic_id  # Track which topic it came from
                all_results.append(item)
    
    if not all_results:
        return {
            'results': [],
            'metadata': {
                'query': query,
                'topics_searched': indexed_topics,
                'error': 'No results found'
            }
        }
    
    # Sort by similarity globally
    all_results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Apply max_per_book limit
    if max_per_book:
        book_counts = {}
        filtered_results = []
        for item in all_results:
            book_title = item.get('book_title', 'unknown')
            count = book_counts.get(book_title, 0)
            if count < max_per_book:
                filtered_results.append(item)
                book_counts[book_title] = count + 1
        all_results = filtered_results
    
    # Take top-k
    top_results = all_results[:k]
    
    # Book distribution
    book_dist = {}
    for item in top_results:
        book_title = item.get('book_title', 'unknown')
        book_dist[book_title] = book_dist.get(book_title, 0) + 1
    
    return {
        'results': top_results,
        'metadata': {
            'query': query,
            'topics_searched': indexed_topics,
            'total_retrieved': len(all_results),
            'returned': len(top_results),
            'reranked': rerank,
            'context_window': context_window,
            'max_per_book': max_per_book,
            'book_distribution': book_dist
        }
    }

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Multi-topic semantic search')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results')
    parser.add_argument('--no-rerank', action='store_true', help='Disable reranking')
    parser.add_argument('--context-window', type=int, default=1, help='Surrounding chunks')
    parser.add_argument('--max-per-book', type=int, default=2, help='Max per book')
    
    args = parser.parse_args()
    
    result = search_all_topics(
        query=args.query,
        k=args.top_k,
        rerank=not args.no_rerank,
        context_window=args.context_window,
        max_per_book=args.max_per_book
    )
    
    print(json.dumps(result, indent=2))
