#!/usr/bin/env python3
"""
Librarian MCP Server v5 — FAISS Production

Clean production MCP server using FAISS vector search.
Zero legacy dependencies, single source of truth.

MCP Tools:
    - search_library: Semantic search via FAISS

Usage:
    python mcp_server.py
"""
import os
import sys
import json
import logging
import signal
import threading
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add engine/scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from faiss_search import get_searcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("librarian-mcp-v5-faiss")

# Initialize MCP server
app = Server("librarian-v5-faiss")

# Paths
FAISS_INDEX = Path("/app/books/faiss.index")
METADATA_JSON = Path("/app/books/metadata.json")

# Lazy-load embedding model & searcher
_model = None
_searcher = None
_searcher_lock = threading.Lock()  # T020: Thread-safe reload


def get_model():
    """Lazy-load embedding model (singleton)."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: BAAI/bge-small-en-v1.5")
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model


def get_search():
    """Lazy-load FAISS searcher (singleton)."""
    global _searcher
    with _searcher_lock:
        if _searcher is None:
            logger.info(f"Loading FAISS index from {FAISS_INDEX}")
            _searcher = get_searcher(
                index_path=str(FAISS_INDEX),
                metadata_path=str(METADATA_JSON)
            )
            stats = _searcher.get_stats()
            logger.info(
                f"FAISS ready: {stats['total_books']} books, "
                f"{stats['total_chunks']:,} chunks, "
                f"{stats['dimensions']} dims"
            )
    return _searcher


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_library",
            description=(
                "Semantic search across 290 books using FAISS vector retrieval. "
                "Returns ranked results with source metadata (book, paragraphs, scores)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (natural language)"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum similarity score (0-1, optional)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_chunk",
            description="Retrieve specific chunk by ID (for follow-up or deep-dive).",
            inputSchema={
                "type": "object",
                "properties": {
                    "chunk_id": {
                        "type": "string",
                        "description": "Chunk identifier (e.g., 'ch_abc123')"
                    }
                },
                "required": ["chunk_id"]
            }
        ),
        Tool(
            name="stats",
            description="Get library statistics (books, chunks, index size).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle MCP tool calls."""
    
    if name == "search_library":
        return await handle_search(arguments)
    
    elif name == "get_chunk":
        return await handle_get_chunk(arguments)
    
    elif name == "stats":
        return await handle_stats(arguments)
    
    raise ValueError(f"Unknown tool: {name}")


async def handle_search(args: dict) -> List[TextContent]:
    """
    Handle search_library tool call.
    
    Args:
        args: {query, k, min_score}
    
    Returns:
        Formatted search results
    """
    query = args.get("query")
    k = args.get("k", 10)
    min_score = args.get("min_score")
    
    logger.info(f"Search: '{query[:60]}...' (k={k}, min_score={min_score})")
    
    # Get model & searcher
    model = get_model()
    searcher = get_search()
    
    # Search
    results = searcher.search_text(
        query_text=query,
        embedding_model=model,
        k=k,
        min_score=min_score
    )
    
    # Format output
    if not results:
        return [TextContent(
            type="text",
            text=f"No results found for: {query}"
        )]
    
    output = f"# Search Results: {query}\n\n"
    output += f"Found {len(results)} relevant chunks:\n\n"
    
    for i, result in enumerate(results, 1):
        score = result["score"]
        book_title = result.get("book_title", "Unknown")
        book_author = result.get("book_author", "Unknown")
        text = result["text"]
        chunk_id = result["chunk_id"]
        
        # Source metadata
        source = result.get("source", {})
        source_type = source.get("type", "unknown")
        
        # EPUB: spine_index + href
        if source_type == "epub":
            spine_idx = source.get("spine_index", "?")
            href = source.get("href", "?")
            location = f"spine {spine_idx}, {href}"
        # PDF: page number
        elif source_type == "pdf":
            page = source.get("page", "?")
            location = f"page {page}"
        else:
            location = "unknown location"
        
        output += f"## {i}. {book_title} [{score:.3f}]\n\n"
        output += f"**Author:** {book_author}  \n"
        output += f"**Location:** {location}  \n"
        output += f"**Chunk ID:** `{chunk_id}`\n\n"
        output += f"> {text[:300]}{'...' if len(text) > 300 else ''}\n\n"
        output += "---\n\n"
    
    return [TextContent(type="text", text=output)]


async def handle_get_chunk(args: dict) -> List[TextContent]:
    """
    Handle get_chunk tool call.
    
    Args:
        args: {chunk_id}
    
    Returns:
        Full chunk content
    """
    chunk_id = args.get("chunk_id")
    
    logger.info(f"Get chunk: {chunk_id}")
    
    searcher = get_search()
    chunk = searcher.get_chunk_by_id(chunk_id)
    
    if not chunk:
        return [TextContent(
            type="text",
            text=f"Chunk not found: {chunk_id}"
        )]
    
    # Format output
    output = f"# Chunk: {chunk_id}\n\n"
    output += f"**Book:** {chunk.get('book_title', 'Unknown')}  \n"
    output += f"**Text:**\n\n{chunk['text']}\n\n"
    
    # Source metadata
    source = chunk.get("source", {})
    output += f"**Source:** {json.dumps(source, indent=2)}\n\n"
    
    # Paragraphs
    paragraphs = chunk.get("paragraphs", [])
    if paragraphs:
        output += f"**Paragraphs:** {len(paragraphs)}\n"
        for p in paragraphs[:3]:  # Show first 3
            output += f"- idx={p.get('idx')}, element_id={p.get('element_id')}\n"
    
    return [TextContent(type="text", text=output)]


async def handle_stats(args: dict) -> List[TextContent]:
    """
    Handle stats tool call.
    
    Returns:
        Library statistics
    """
    logger.info("Get stats")
    
    searcher = get_search()
    stats = searcher.get_stats()
    
    output = "# Library Statistics\n\n"
    output += f"**Books:** {stats['total_books']:,}  \n"
    output += f"**Chunks:** {stats['total_chunks']:,}  \n"
    output += f"**Vectors:** {stats['total_vectors']:,}  \n"
    output += f"**Dimensions:** {stats['dimensions']}  \n"
    output += f"**Index Type:** {stats['index_type']}\n\n"
    
    # File sizes
    faiss_size = FAISS_INDEX.stat().st_size / 1024 / 1024
    meta_size = METADATA_JSON.stat().st_size / 1024 / 1024
    
    output += f"**Storage:**  \n"
    output += f"- FAISS index: {faiss_size:.1f} MB  \n"
    output += f"- Metadata: {meta_size:.1f} MB  \n"
    output += f"- Total: {faiss_size + meta_size:.1f} MB\n"
    
    return [TextContent(type="text", text=output)]


async def main():
    """Run MCP server."""
    logger.info("Starting Librarian MCP v5 (FAISS-only)")
    
    # T020: Setup signal handler for hot-reload
    def reload_handler(signum, frame):
        """Handle SIGHUP = reload FAISS index."""
        logger.info("SIGHUP received, reloading FAISS index...")
        global _searcher
        with _searcher_lock:
            old_searcher = _searcher
            _searcher = None  # Clear cache
            try:
                # Reload from disk
                _searcher = get_searcher(
                    index_path=str(FAISS_INDEX),
                    metadata_path=str(METADATA_JSON)
                )
                stats = _searcher.get_stats()
                logger.info(
                    f"✅ FAISS reloaded: {stats['total_chunks']:,} chunks"
                )
                # Free old searcher
                del old_searcher
            except Exception as e:
                logger.error(f"❌ Reload failed: {e}")
                # Restore old searcher on failure
                _searcher = old_searcher
    
    signal.signal(signal.SIGHUP, reload_handler)
    logger.info("Hot-reload enabled (send SIGHUP to reload index)")
    
    # Pre-load index (fail fast if missing)
    try:
        get_search()
    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")
        logger.error("Make sure FAISS index exists at /app/books/faiss.index")
        sys.exit(1)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
