#!/usr/bin/env python3
"""
Personal Library MCP Server

A Model Context Protocol server that provides RAG retrieval from indexed books.
The server is LLM-agnostic - it only returns chunks, the LLM (Claude/GPT/etc) generates responses.

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

import faiss
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
ENV_PATH = Path(__file__).parent.parent / ".env"
if not ENV_PATH.exists():
    # Fallback to notes directory
    ENV_PATH = Path.home() / "Documents/notes/.env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

# Paths
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"
INDEX_FILE = STORAGE_DIR / "faiss.index"
DOCSTORE_FILE = STORAGE_DIR / "docstore.json"

# Gemini API setup
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in .env", file=sys.stderr)
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Global state (loaded once on startup)
faiss_index: Optional[faiss.Index] = None
docstore: Optional[Dict] = None
metadata: Optional[Dict] = None


def load_resources():
    """Load FAISS index, docstore, and metadata (Gemini embeddings = no model loading)."""
    global faiss_index, docstore, metadata

    if faiss_index is None:
        print("Loading FAISS index...", file=sys.stderr, flush=True)
        faiss_index = faiss.read_index(str(INDEX_FILE))

    if docstore is None:
        print("Loading docstore...", file=sys.stderr, flush=True)
        try:
            import orjson
            with open(DOCSTORE_FILE, 'rb') as f:
                docstore = {int(k): v for k, v in orjson.loads(f.read()).items()}
        except ImportError:
            import json as json_lib
            with open(DOCSTORE_FILE, 'r', encoding='utf-8') as f:
                docstore = {int(k): v for k, v in json_lib.load(f).items()}

    if metadata is None:
        print("Loading metadata...", file=sys.stderr, flush=True)
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    print(f"✅ Resources loaded ({faiss_index.ntotal:,} vectors)", file=sys.stderr, flush=True)


def find_book_id(query: str) -> Optional[str]:
    """Find book ID by partial title match."""
    query_lower = query.lower()
    for topic in metadata['topics']:
        for book in topic['books']:
            if query_lower in book['title'].lower() or query_lower == book['id']:
                return book['id']
    return None


def find_topic_id(query: str) -> Optional[str]:
    """Find topic ID by partial label match."""
    query_lower = query.lower()
    for topic in metadata['topics']:
        if query_lower in topic['label'].lower() or query_lower == topic['id']:
            return topic['id']
    return None


def filter_indices(book_id: Optional[str] = None, topic_id: Optional[str] = None) -> List[int]:
    """Get valid docstore indices for book/topic filter."""
    if not book_id and not topic_id:
        return list(docstore.keys())

    valid = []
    for idx, doc in docstore.items():
        if book_id and doc['book_id'] == book_id:
            valid.append(idx)
        elif topic_id and doc['topic_id'] == topic_id:
            valid.append(idx)

    return valid


def query_library(
    question: str,
    book_context: Optional[str] = None,
    top_k: int = 5
) -> Dict:
    """
    Query the library and return relevant chunks.

    Args:
        question: User's question
        book_context: Optional book title/ID or topic label/ID to filter
        top_k: Number of chunks to return

    Returns:
        Dict with results and metadata
    """
    load_resources()

    # Parse context (book or topic)
    book_id = None
    topic_id = None

    if book_context:
        book_id = find_book_id(book_context)
        if not book_id:
            topic_id = find_topic_id(book_context)

        if not book_id and not topic_id:
            return {
                "error": f"Context not found: {book_context}",
                "suggestion": "Use list_topics or list_books to see available options"
            }

    # Generate query embedding using Gemini
    result = genai.embed_content(
        model="models/embedding-001",
        content=question,
        task_type="retrieval_query"
    )
    query_embedding = np.array([result['embedding']], dtype='float32')

    # Search FAISS
    distances, indices = faiss_index.search(query_embedding, top_k * 10)

    # Filter and collect results
    valid_indices = filter_indices(book_id, topic_id) if (book_id or topic_id) else None
    results = []

    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1 or idx not in docstore:
            continue

        if valid_indices and idx not in valid_indices:
            continue

        doc = docstore[idx]

        results.append({
            "text": doc['chunk_full'],
            "book_title": doc['book_title'],
            "book_author": doc['book_author'],
            "topic": doc['topic_label'],
            "chunk_index": doc['chunk_index'],
            "similarity": float(1 / (1 + dist))
        })

        if len(results) >= top_k:
            break

    return {
        "question": question,
        "context": book_context,
        "results": results,
        "total_chunks": len(results)
    }


def list_topics() -> Dict:
    """List all available topics."""
    load_resources()

    topics = []
    for topic in metadata['topics']:
        topics.append({
            "id": topic['id'],
            "label": topic['label'],
            "description": topic['description'],
            "book_count": len(topic['books'])
        })

    return {"topics": topics}


def list_books(topic_context: Optional[str] = None) -> Dict:
    """List books, optionally filtered by topic."""
    load_resources()

    books = []

    for topic in metadata['topics']:
        if topic_context:
            topic_id = find_topic_id(topic_context)
            if topic['id'] != topic_id:
                continue

        for book in topic['books']:
            books.append({
                "id": book['id'],
                "title": book['title'],
                "author": book['author'],
                "topic": topic['label'],
                "tags": book['tags']
            })

    return {"books": books}


# MCP Protocol Implementation
async def handle_mcp_request(request: Dict) -> Dict:
    """Handle incoming MCP request."""
    method = request.get("method")
    params = request.get("params", {})

    try:
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "query_library",
                        "description": "Search indexed books and return relevant text chunks",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string", "description": "User's question"},
                                "book_context": {"type": "string", "description": "Optional: book title or topic to filter"},
                                "top_k": {"type": "integer", "default": 5, "description": "Number of chunks to return"}
                            },
                            "required": ["question"]
                        }
                    },
                    {
                        "name": "list_topics",
                        "description": "List all available topics/folders",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "list_books",
                        "description": "List books, optionally filtered by topic",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "topic_context": {"type": "string", "description": "Optional: topic to filter"}
                            }
                        }
                    }
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "query_library":
                result = query_library(**arguments)
            elif tool_name == "list_topics":
                result = list_topics()
            elif tool_name == "list_books":
                result = list_books(**arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        else:
            return {"error": f"Unknown method: {method}"}

    except Exception as e:
        return {"error": str(e)}


async def main():
    """MCP stdio server main loop."""
    print("Personal Library MCP Server starting...", file=sys.stderr, flush=True)

    # Pre-load all resources on startup
    load_resources()

    print("Personal Library MCP Server ready", file=sys.stderr, flush=True)

    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            request = json.loads(line.strip())
            response = await handle_mcp_request(request)

            print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
