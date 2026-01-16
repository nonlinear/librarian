#!/usr/bin/env python3
"""
Personal Library MCP Server - Partitioned Lazy Loading

Loads only metadata.json on startup (instant <100ms).
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
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"

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


def load_topic(topic_id: str) -> Dict:
    """Lazy load topic-specific FAISS index + chunks."""
    _ensure_imports()

    # Check cache first
    if topic_id in _topic_cache:
        return _topic_cache[topic_id]

    print(f"Loading topic: {topic_id}...", file=sys.stderr, flush=True)

    topic_dir = STORAGE_DIR / topic_id
    faiss_file = topic_dir / "faiss.index"
    chunks_file = topic_dir / "chunks.pkl"

    if not faiss_file.exists() or not chunks_file.exists():
        print(f"⚠️  Topic {topic_id} not indexed yet", file=sys.stderr, flush=True)
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
            'score': float(dist)
        })

    return results


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
                topics = [{"id": t['id'], "label": t['label'], "description": t['description']}
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
            print(f"[{time.time()-start:.3f}s] Processing method: {request.get('method')}", file=sys.stderr, flush=True)

            response = await handle_mcp_request(request)

            # Only send response if not None (notifications don't get responses)
            if response is not None:
                print(f"[{time.time()-start:.3f}s] Sending response", file=sys.stderr, flush=True)
                print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
