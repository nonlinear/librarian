#!/usr/bin/env python3
"""
Librarian MCP Server - Thin wrapper around research.py

Single source of truth: research.py contains all query logic.
This file only handles MCP protocol (JSON-RPC over stdio).
"""

import json
import os
import sys
import traceback
from pathlib import Path

# Suppress progress bars and model loading output
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
import warnings
warnings.filterwarnings('ignore')

# Import research.py (single source of truth)
sys.path.insert(0, str(Path(__file__).parent))

try:
    import research
except Exception as e:
    print(f"ERROR: Failed to import research.py: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(2)

# Global metadata cache
metadata = None


def handle_request(request: dict) -> dict:
    """Handle MCP JSON-RPC request."""
    global metadata

    method = request.get('method')
    params = request.get('params', {})

    # Lazy load metadata
    if metadata is None:
        metadata = research.load_metadata()
        print(f"✅ Loaded: {len(metadata['topics'])} topics", file=sys.stderr, flush=True)

    # MCP Protocol methods
    if method == 'initialize':
        return {
            "protocolVersion": "0.1.0",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "librarian", "version": "2.0.0"}
        }

    elif method == 'tools/list':
        return {
            "tools": [
                {
                    "name": "query_library",
                    "description": "Search personal library for relevant passages",
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
                    "description": "List all available topics",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "list_books",
                    "description": "List books in a topic",
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
        args = params.get('arguments', {})

        if tool_name == 'query_library':
            # Delegate to research.py (single source of truth)
            results = research.query_library(
                query=args['query'],
                topic=args.get('topic'),
                book=args.get('book'),
                k=args.get('k', 5)
            )
            return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}

        elif tool_name == 'list_topics':
            topics = [{"id": t["id"], "path": t["path"]} for t in metadata["topics"]]
            return {"content": [{"type": "text", "text": json.dumps(topics, indent=2)}]}

        elif tool_name == 'list_books':
            topic_id = args['topic']

            # Find topic
            topic = next((t for t in metadata['topics'] if t['id'] == topic_id), None)
            if not topic:
                return {"content": [{"type": "text", "text": f"Topic '{topic_id}' not found"}]}

            # Load topic index
            topic_data = research.load_topic(topic['path'])
            if not topic_data:
                return {"content": [{"type": "text", "text": f"Failed to load topic '{topic_id}'"}]}

            books = [{"title": b["title"], "path": b["path"]} for b in topic_data.get("books", [])]
            return {"content": [{"type": "text", "text": json.dumps(books, indent=2)}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

    return {}


def main():
    """Main loop: read JSON-RPC from stdin, write to stdout."""
    try:
        print("Librarian MCP Server starting (delegates to research.py)...", file=sys.stderr, flush=True)

        # Force load metadata early to catch import/load errors
        global metadata
        metadata = research.load_metadata()
        print(f"✅ Loaded: {len(metadata['topics'])} topics", file=sys.stderr, flush=True)

        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                request_id = request.get('id')

                result = handle_request(request)

                # JSON-RPC response (only if request had id)
                if request_id is not None:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result if result else {}
                    }
                    print(json.dumps(response), flush=True)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"ERROR processing request: {e}", file=sys.stderr, flush=True)
                traceback.print_exc(file=sys.stderr)
                if request_id is not None:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32603, "message": str(e)}
                    }
                    print(json.dumps(error_response), flush=True)

    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
