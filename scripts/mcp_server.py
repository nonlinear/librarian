#!/usr/bin/env python3
"""
Personal Library MCP Server - Partitioned Lazy Loading

Loads only library-index.json on startup (instant <100ms).
Topic-specific FAISS + chunks loaded on-demand during queries.

MCP Tools:
- query_library: Retrieve relevant chunks from books
- list_topics: Show available topics
- list_books: Show books in a topic
"""

import json
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict
import asyncio

# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
# v2.0: library-index.json, fallback to v1.0 metadata.json for backwards compatibility
METADATA_FILE = BOOKS_DIR / "library-index.json"
if not METADATA_FILE.exists():
    METADATA_FILE = BOOKS_DIR / "metadata.json"  # Fallback to v1.0 schema

# Heavy imports - lazy loaded on first query
_lazy_imports_loaded = False
faiss = None
np = None
SentenceTransformer = None
embedding_model = None

# Global state
metadata: Optional[Dict] = None
_topic_cache: Dict[str, Dict] = {}  # {topic_id: {index, chunks}}


def _ensure_imports():
    """Lazy load heavy dependencies only when needed."""
    global _lazy_imports_loaded, faiss, np, SentenceTransformer, embedding_model
    if _lazy_imports_loaded:
        return

    import pickle
    import numpy
    import faiss as faiss_module
    from sentence_transformers import SentenceTransformer as ST

    # Set globals
    np = numpy
    faiss = faiss_module
    SentenceTransformer = ST

    # Load embedding model
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = 'models'
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    _lazy_imports_loaded = True
    print("✅ Loaded heavy dependencies (local embeddings)", file=sys.stderr, flush=True)


def _rebuild_topic_index(topic_id: str, topic_label: str) -> bool:
    """Rebuild FAISS index for a single topic."""
    try:
        import subprocess

        print(f"🔨 Rebuilding index for topic: {topic_label}", file=sys.stderr, flush=True)

        # Create a minimal script to reindex just this topic
        script_path = Path(__file__).parent / "reindex_topic.py"

        if not script_path.exists():
            print(f"⚠️  reindex_topic.py not found, running full indexer", file=sys.stderr, flush=True)
            # Fallback: run full indexer (slower but works)
            indexer_path = Path(__file__).parent / "indexer.py"
            result = subprocess.run(
                [sys.executable, str(indexer_path)],
                capture_output=True,
                text=True,
                timeout=600  # 10 min max
            )
            return result.returncode == 0

        # Run topic-specific reindexer
        result = subprocess.run(
            [sys.executable, str(script_path), topic_id],
            capture_output=True,
            text=True,
            timeout=120  # 2 min max per topic
        )

        if result.returncode == 0:
            print(f"✅ Rebuilt {topic_label}", file=sys.stderr, flush=True)
            return True
        else:
            print(f"❌ Error: {result.stderr}", file=sys.stderr, flush=True)
            return False

    except Exception as e:
        print(f"❌ Rebuild failed: {e}", file=sys.stderr, flush=True)
        return False


def load_topic(topic_id: str) -> Dict:
    """Lazy load topic-specific FAISS index + chunks."""
    _ensure_imports()

    # Check cache first
    if topic_id in _topic_cache:
        return _topic_cache[topic_id]

    print(f"Loading topic: {topic_id}...", file=sys.stderr, flush=True)

    # Find topic label from metadata
    topic_label = None
    for topic in metadata['topics']:
        if topic['id'] == topic_id:
            topic_label = topic['label']
            break

    if not topic_label:
        print(f"⚠️  Topic {topic_id} not found in metadata", file=sys.stderr, flush=True)
        return None

    # Reconstruct full path from flattened topic_id
    # Get folder path from metadata
    folder_path = topic_data.get('folder_path', topic_label)
    topic_dir = BOOKS_DIR / folder_path
    faiss_file = topic_dir / "faiss.index"
    chunks_file = topic_dir / "chunks.pkl"

    # Auto-rebuild if missing
    if not faiss_file.exists() or not chunks_file.exists():
        print(f"⚠️  Topic {topic_id} indices missing. Auto-rebuilding...", file=sys.stderr, flush=True)
        success = _rebuild_topic_index(topic_id, topic_label)
        if not success:
            print(f"❌ Failed to rebuild {topic_id}", file=sys.stderr, flush=True)
            return None

    # Load FAISS index
    index = faiss.read_index(str(faiss_file))

    # Load chunks
    import pickle
    with open(chunks_file, 'rb') as f:
        chunks = pickle.load(f)

    # Cache
    topic_data = {'index': index, 'chunks': chunks}
    _topic_cache[topic_id] = topic_data

    print(f"✅ Loaded {topic_id}: {index.ntotal} vectors, {len(chunks)} chunks", file=sys.stderr, flush=True)

    return topic_data


def find_topic_id(query: str) -> Optional[str]:
    """Find topic ID by partial label match."""
    query_lower = query.lower()
    for topic in metadata['topics']:
        if query_lower in topic['label'].lower() or query_lower == topic['id']:
            return topic['id']
    return None


def infer_topic_from_query(query: str, min_confidence: float = 0.6) -> Dict:
    """
    Infer topic from query using tags and colloquial phrasing.
    Returns: {
        'topic_id': str or None,
        'confidence': float (0-1),
        'candidates': list of (topic_id, score) tuples,
        'reasoning': str
    }
    """
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # Strategy 1: Check for exact child-parent colloquial phrases
    # "applied cybersecurity", "cybersecurity history", "history of cybersecurity"
    for topic in metadata['topics']:
        topic_id = topic['id']

        # For subtopics like cybersecurity_applied
        if '_' in topic_id:
            parts = topic_id.split('_')
            parent = parts[0]
            child = parts[1]

            # Check various colloquial patterns
            patterns = [
                f"{child} {parent}",      # "applied cybersecurity"
                f"{parent} {child}",      # "cybersecurity applied"
                f"{child} of {parent}",   # "history of cybersecurity"
                f"{parent} {child}",      # "cybersecurity history"
            ]

            for pattern in patterns:
                if pattern in query_lower:
                    return {
                        'topic_id': topic_id,
                        'confidence': 1.0,
                        'candidates': [(topic_id, 1.0)],
                        'reasoning': f'Matched colloquial phrase: "{pattern}"'
                    }

    # Strategy 2: Score topics by tag overlap + word matching
    scored_topics = []

    for topic in metadata['topics']:
        score = 0.0
        topic_id = topic['id']

        # Get topic tags
        topic_tags = set(topic.get('description', '').lower().split(', '))

        # Score tag overlap (weighted higher)
        tag_matches = query_words & topic_tags
        score += len(tag_matches) * 0.5

        # Score topic ID word matches
        topic_words = set(topic_id.replace('_', ' ').split())
        id_matches = query_words & topic_words
        score += len(id_matches) * 0.3

        # Score label matches
        label_words = set(topic['label'].lower().split())
        label_matches = query_words & label_words
        score += len(label_matches) * 0.2

        if score > 0:
            # Normalize score (rough heuristic)
            normalized_score = min(score / max(len(query_words), 3), 1.0)
            scored_topics.append((topic_id, normalized_score, tag_matches | id_matches | label_matches))

    # Sort by score
    scored_topics.sort(key=lambda x: x[1], reverse=True)

    if not scored_topics:
        return {
            'topic_id': None,
            'confidence': 0.0,
            'candidates': [],
            'reasoning': 'No tag or keyword matches found'
        }

    best_topic, best_score, matches = scored_topics[0]

    # Check if we have high enough confidence
    if best_score >= min_confidence:
        return {
            'topic_id': best_topic,
            'confidence': best_score,
            'candidates': [(t, s) for t, s, _ in scored_topics[:3]],
            'reasoning': f'Tag/keyword matches: {", ".join(sorted(matches))}'
        }
    else:
        return {
            'topic_id': None,
            'confidence': best_score,
            'candidates': [(t, s) for t, s, _ in scored_topics[:3]],
            'reasoning': f'Low confidence ({best_score:.2f}). Top matches: {", ".join(sorted(matches))}'
        }


def topic_id_to_path(topic_id: str) -> str:
    """Convert flattened topic ID to display path with /."""
    return topic_id.replace('_', '/')


def get_related_topics(topic_id: str, limit: int = 3) -> List[str]:
    """Suggest related topics based on tag overlap."""
    current_topic = None
    for topic in metadata['topics']:
        if topic['id'] == topic_id:
            current_topic = topic
            break

    if not current_topic:
        return []

    # Get tags from current topic description
    current_tags = set(current_topic.get('description', '').lower().split(', '))

    # Score other topics by tag overlap
    scored_topics = []
    for topic in metadata['topics']:
        if topic['id'] == topic_id:
            continue

        topic_tags = set(topic.get('description', '').lower().split(', '))
        overlap = len(current_tags & topic_tags)

        if overlap > 0:
            scored_topics.append((topic['id'], overlap))

    # Sort by overlap and return top N
    scored_topics.sort(key=lambda x: x[1], reverse=True)
    return [topic_id_to_path(t[0]) for t, _ in scored_topics[:limit]]


def find_book_id(query: str) -> Optional[str]:
    """Find book ID by partial title match."""
    query_lower = query.lower()
    for topic in metadata['topics']:
        for book in topic['books']:
            if query_lower in book['title'].lower() or query_lower == book['id']:
                return book['id']
    return None


def get_embedding(text: str):
    """Get query embedding from local model."""
    _ensure_imports()

    embedding = embedding_model.encode(text, convert_to_numpy=True).astype(np.float32)
    return embedding



def query_library(query: str, topic: Optional[str] = None, book: Optional[str] = None, k: int = 5) -> List[Dict]:
    """
    Query the library with optional topic/book filtering.

    Args:
        query: Natural language query
        topic: Optional topic ID or label
        book: Optional book ID or title
        k: Number of results to return

    Returns:
        List of {text, book_title, topic, score} chunks
    """
    # 1. Determine topic
    topic_id = None
    if topic:
        topic_id = find_topic_id(topic)
        if not topic_id:
            return [{"error": f"Topic not found: {topic}"}]

    # If book specified, find its topic
    if book and not topic_id:
        book_id = find_book_id(book)
        if book_id:
            for t in metadata['topics']:
                for b in t['books']:
                    if b['id'] == book_id:
                        topic_id = t['id']
                        break

    # If still no topic, try to infer from query
    if not topic_id:
        # Simple heuristic: check if query mentions a topic
        query_lower = query.lower()
        for t in metadata['topics']:
            if t['id'] in query_lower or t['label'].lower() in query_lower:
                topic_id = t['id']
                break

        # Default to first topic if still unclear
        if not topic_id and metadata['topics']:
            topic_id = metadata['topics'][0]['id']
            print(f"⚠️  No topic specified, defaulting to: {topic_id}", file=sys.stderr, flush=True)

    # 2. Load topic data
    topic_data = load_topic(topic_id)
    if not topic_data:
        return [{"error": f"Topic {topic_id} has no indexed data"}]

    index = topic_data['index']
    chunks = topic_data['chunks']

    # 3. Get query embedding
    query_vec = get_embedding(query)

    # 4. Search FAISS
    distances, indices = index.search(np.array([query_vec]), k)

    # 5. Filter by book if specified
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:  # FAISS returns -1 for missing results
            continue

        chunk = chunks[idx]

        # Filter by book if specified
        if book:
            book_id = find_book_id(book)
            if book_id and chunk['metadata']['book_id'] != book_id:
                continue

        results.append({
            'text': chunk['text'],
            'book_title': chunk['metadata']['book_title'],
            'topic': chunk['metadata']['topic_label'],
            'topic_path': topic_id_to_path(topic_id),
            'score': float(dist)
        })

    # Add related topics suggestion
    response = {
        'results': results,
        'topic_searched': topic_id_to_path(topic_id),
        'related_topics': get_related_topics(topic_id)
    }

    return response


async def handle_mcp_request(request: Dict) -> Dict:
    """Handle MCP protocol request."""
    try:
        method = request.get('method')
        params = request.get('params', {})

        if method == 'initialize':
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "personal-library",
                    "version": "1.0.0"
                }
            }

        elif method == 'notifications/initialized':
            # Client confirms it's ready - no response needed for notifications
            return None

        elif method == 'tools/list':
            return {
                "tools": [
                    {
                        "name": "query_library",
                        "description": "Search personal library for relevant book passages",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language query"},
                                "topic": {"type": "string", "description": "Optional topic filter"},
                                "book": {"type": "string", "description": "Optional book filter"},
                                "k": {"type": "integer", "description": "Number of results", "default": 5}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "list_topics",
                        "description": "List all available topics",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "list_books",
                        "description": "List books in a topic",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string", "description": "Topic ID or label"}
                            },
                            "required": ["topic"]
                        }
                    }
                ]
            }

        elif method == 'tools/call':
            tool_name = params.get('name')
            tool_params = params.get('arguments', {})

            if tool_name == 'query_library':
                results = query_library(**tool_params)
                return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}

            elif tool_name == 'list_topics':
                topics = [{"id": t['id'], "path": topic_id_to_path(t['id']), "label": t['label'], "description": t['description']}
                         for t in metadata['topics']]
                return {"content": [{"type": "text", "text": json.dumps(topics, indent=2)}]}

            elif tool_name == 'list_books':
                topic_id = find_topic_id(tool_params['topic'])
                if not topic_id:
                    return {"error": f"Topic not found: {tool_params['topic']}"}

                for topic in metadata['topics']:
                    if topic['id'] == topic_id:
                        books = [{"id": b['id'], "title": b['title'], "author": b['author']}
                                for b in topic['books']]
                        return {"content": [{"type": "text", "text": json.dumps(books, indent=2)}]}

                return {"error": "Topic not found"}

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        else:
            return {"error": f"Unknown method: {method}"}

    except Exception as e:
        return {"error": str(e)}


async def main():
    """MCP stdio server main loop."""
    global metadata
    import time

    start = time.time()
    print(f"[{time.time()-start:.3f}s] Personal Library MCP Server starting...", file=sys.stderr, flush=True)

    # Load ONLY metadata (19KB - instant)
    t1 = time.time()
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    print(f"[{time.time()-start:.3f}s] Loaded metadata in {time.time()-t1:.3f}s", file=sys.stderr, flush=True)

    print(f"[{time.time()-start:.3f}s] ✅ Ready! Loaded metadata: {len(metadata['topics'])} topics", file=sys.stderr, flush=True)
    print(f"[{time.time()-start:.3f}s] 💡 Topic indices will lazy-load on first query", file=sys.stderr, flush=True)
    print(f"[{time.time()-start:.3f}s] Waiting for stdin...", file=sys.stderr, flush=True)

    while True:
        try:
            print(f"[{time.time()-start:.3f}s] Reading stdin...", file=sys.stderr, flush=True)
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            print(f"[{time.time()-start:.3f}s] Received: {line[:50] if line else 'EOF'}...", file=sys.stderr, flush=True)

            if not line:
                break

            request = json.loads(line.strip())
            request_id = request.get('id')
            print(f"[{time.time()-start:.3f}s] Processing method: {request.get('method')} (id={request_id})", file=sys.stderr, flush=True)

            response = await handle_mcp_request(request)

            # JSON-RPC: Requests (with id) always get responses, notifications don't
            if request_id is not None:
                json_rpc_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": response if response is not None else {}
                }
                print(f"[{time.time()-start:.3f}s] Sending response", file=sys.stderr, flush=True)
                print(json.dumps(json_rpc_response), flush=True)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
