#!/usr/bin/env python3
"""
Librarian MCP Server - Thin wrapper around research.py

Delegates all queries to research.py (single source of truth).
Provides MCP protocol interface (stdin/stdout) for VS Code integration.

MCP Tools:
- query_library: Retrieve relevant chunks from books (calls research.py)
- list_topics: Show available topics
- list_books: Show books in a topic
"""

import json
import sys
import asyncio
from pathlib import Path

# Add parent dir to path to import research
sys.path.insert(0, str(Path(__file__).parent))
import research

# Metadata cache (loaded once at startup)
metadata = None


async def handle_mcp_request(request: dict) -> dict:
    """Handle MCP JSON-RPC requests."""
    global metadata

    method = request.get('method')
    params = request.get('params', {})

    try:
        # Initialize metadata on first use
        if metadata is None:
            metadata = research.load_metadata()

        if method == 'initialize':
            return {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "librarian",
                    "version": "2.0.0"
                }
            }

        elif method == 'tools/list':
            return {
                "tools": [
                    {
                        "name": "query_library",
                        "description": "Search your personal library for relevant book passages",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "topic": {"type": "string", "description": "Optional topic filter"},
                                "book": {"type": "string", "description": "Optional book filter"},
                                "k": {"type": "integer", "description": "Number of results", "default": 5}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "list_topics",
                        "description": "List all available topics in the library",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "list_books",
                        "description": "List books in a specific topic",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string", "description": "Topic ID"}
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
                # Delegate to research.py
                results = research.query_library(
                    query=tool_params['query'],
                    topic=tool_params.get('topic'),
                    book=tool_params.get('book'),
                    k=tool_params.get('k', 5)
                )
                return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}

            elif tool_name == 'list_topics':
                topics = [{"id": t['id'], "path": t.get('path', t['id'])}
                         for t in metadata['topics']]
                return {"content": [{"type": "text", "text": json.dumps(topics, indent=2)}]}

            elif tool_name == 'list_books':
                topic_id = tool_params.get('topic')
                if not topic_id:
                    return {"error": "Topic parameter required"}

                # Find topic path
                topic_path = None
                for topic in metadata['topics']:
                    if topic['id'] == topic_id:
                        topic_path = topic.get('path')
                        break

                if not topic_path:
                    return {"error": f"Topic not found: {topic_id}"}

                # Load topic-index.json
                books_dir = Path(metadata.get('library_path', research.BOOKS_DIR))
                topic_index_file = books_dir / topic_path / ".topic-index.json"

                if not topic_index_file.exists():
                    return {"error": f"Topic index not found for: {topic_id}"}

                with open(topic_index_file, 'r', encoding='utf-8') as f:
                    topic_meta = json.load(f)
                    books = [{"id": b['id'], "title": b['title'], "author": b.get('author', 'Unknown')}
                            for b in topic_meta.get('books', [])]
                    return {"content": [{"type": "text", "text": json.dumps(books, indent=2)}]}

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        else:
            return {"error": f"Unknown method: {method}"}

    except Exception as e:
        return {"error": str(e)}


async def main():
    """MCP stdio server main loop."""
    global metadata

    print("Librarian MCP Server starting (delegating to research.py)...", file=sys.stderr, flush=True)

    # Load metadata once at startup
    metadata = research.load_metadata()
    print(f"✅ Loaded metadata: {len(metadata['topics'])} topics", file=sys.stderr, flush=True)
    print("Waiting for stdin...", file=sys.stderr, flush=True)

    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

            if not line:
                break

            request = json.loads(line.strip())
            request_id = request.get('id')

            response = await handle_mcp_request(request)

            # JSON-RPC: Requests (with id) always get responses
            if request_id is not None:
                json_rpc_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": response if response is not None else {}
                }
                print(json.dumps(json_rpc_response), flush=True)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
