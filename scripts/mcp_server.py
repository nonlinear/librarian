#!/usr/bin/env python3
"""
Personal Library MCP Server (LlamaIndex version)

Simplified architecture using LlamaIndex built-in vector store.
Fast startup with Gemini embeddings.
"""

import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict
import asyncio
from dotenv import load_dotenv

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Load environment
ENV_PATH = Path(__file__).parent.parent / ".env"
if not ENV_PATH.exists():
    ENV_PATH = Path.home() / "Documents/notes/.env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Paths
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"

# Setup Gemini embeddings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY not found in .env", file=sys.stderr)
    sys.exit(1)

embed_model = GoogleGenAIEmbedding(
    model_name="models/embedding-001",
    api_key=GOOGLE_API_KEY
)
Settings.embed_model = embed_model

# Global state
index = None
metadata = None


def load_resources():
    """Load LlamaIndex and metadata."""
    global index, metadata

    if index is None:
        print("Loading vector index...", file=sys.stderr, flush=True)
        storage_context = StorageContext.from_defaults(persist_dir=str(STORAGE_DIR))
        index = load_index_from_storage(storage_context)

    if metadata is None:
        print("Loading metadata...", file=sys.stderr, flush=True)
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)

    print("✅ Resources loaded", file=sys.stderr, flush=True)


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


def query_library(
    question: str,
    book_context: Optional[str] = None,
    top_k: int = 5
) -> Dict:
    """Query the library and return relevant chunks."""
    load_resources()

    # Parse context
    book_id = None
    topic_id = None

    if book_context:
        book_id = find_book_id(book_context)
        if not book_id:
            topic_id = find_topic_id(book_context)

        if not book_id and not topic_id:
            return {
                "error": f"Context not found: {book_context}",
                "suggestion": "Use list_topics or list_books"
            }

    # Build filter string if needed
    filter_metadata = {}
    if book_id:
        filter_metadata['book_id'] = book_id
    elif topic_id:
        filter_metadata['topic_id'] = topic_id

    # Query index
    retriever = index.as_retriever(
        similarity_top_k=top_k,
        filters=filter_metadata if filter_metadata else None
    )

    nodes = retriever.retrieve(question)

    # Format results
    results = []
    for node in nodes:
        results.append({
            "text": node.text,
            "book_title": node.metadata.get('book_title', 'Unknown'),
            "book_author": node.metadata.get('book_author', 'Unknown'),
            "topic": node.metadata.get('topic_label', 'Unknown'),
            "score": node.score
        })

    return {"results": results}


def list_topics() -> Dict:
    """List all topics."""
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
            if topic_id and topic['id'] != topic_id:
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

    # Pre-load resources
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
