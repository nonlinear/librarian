#!/usr/bin/env python3
"""
Librarian MCP Server v3 — Cluster-Aware Search

Replaces v2 topic-based MCP with cluster selection logic.

MCP Tools:
    - research_query: Cluster-aware semantic search

Usage:
    python mcp_server.py
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from threading import Thread, Lock

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add engine/scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from cluster_selection import cluster_aware_search
from search import search_library
from query_logger import log_query

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("librarian-mcp-v3")

# Initialize MCP server
app = Server("librarian-v3")

# Library root
LIBRARY_ROOT = Path(__file__).parent.parent.parent / "books"
INDEX_PATH = LIBRARY_ROOT / ".global-index-v5.json"


# ============================================================
# Hot-Reload System (v4)
# ============================================================

class IndexReloader:
    """
    Hot-reload index when file changes (mtime-based).
    
    Background thread polls mtime every 2s.
    On change: reload index atomically.
    
    Zero downtime, always fresh index.
    """
    
    def __init__(self):
        self.index = None
        self.lock = Lock()
        self.last_mtime = 0
        self.load_index()
        
        # Start background reload thread
        self.thread = Thread(target=self.watch_loop, daemon=True)
        self.thread.start()
        logger.info("[IndexReloader] Hot-reload enabled (mtime-based, 2s poll)")
    
    def load_index(self):
        """Load index from disk (thread-safe)."""
        with self.lock:
            try:
                with open(INDEX_PATH) as f:
                    self.index = json.load(f)
                self.last_mtime = INDEX_PATH.stat().st_mtime
                total_books = self.index.get('total_books', 0)
                total_chunks = self.index.get('total_chunks', 0)
                logger.info(f"[IndexReloader] Loaded index: {total_books} books, {total_chunks} chunks")
            except Exception as e:
                logger.error(f"[IndexReloader] Failed to load index: {e}")
                self.index = {"books": [], "total_books": 0, "total_chunks": 0}
                self.last_mtime = 0
    
    def get_index(self):
        """Get current index (thread-safe)."""
        with self.lock:
            return self.index
    
    def watch_loop(self):
        """Background thread polling for mtime changes."""
        while True:
            time.sleep(2)  # Poll every 2 seconds
            
            try:
                current_mtime = INDEX_PATH.stat().st_mtime
                if current_mtime > self.last_mtime:
                    logger.info("[IndexReloader] Index file changed, reloading...")
                    old_count = self.index.get('total_books', 0) if self.index else 0
                    self.load_index()
                    new_count = self.index.get('total_books', 0)
                    delta = new_count - old_count
                    if delta != 0:
                        logger.info(f"[IndexReloader] Book count delta: {delta:+d} (now {new_count})")
            except FileNotFoundError:
                pass  # Index not created yet
            except Exception as e:
                logger.error(f"[IndexReloader] Watch error: {e}")


# Global index reloader
index_reloader = IndexReloader()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="research_query",
            description=(
                "Search library using cluster-aware semantic search. "
                "Automatically selects relevant clusters based on query + conversation context. "
                "Returns top-K results with citations (book, page, CFI)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Research query (natural language)"
                    },
                    "discipline": {
                        "type": "string",
                        "description": "Discipline ID (e.g., 'management_knowledge', 'design_theory'). Optional: inferred if not provided."
                    },
                    "history": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Recent conversation messages (last 3-5) for context-aware cluster selection"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    },
                    "rerank": {
                        "type": "boolean",
                        "description": "Enable reranking (default: true)",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle MCP tool calls."""
    
    if name == "research_query":
        return await handle_research_query(arguments)
    
    raise ValueError(f"Unknown tool: {name}")


async def handle_research_query(args: dict) -> List[TextContent]:
    """
    Handle research_query tool call.
    
    Args:
        args: Tool arguments (query, discipline, history, k, rerank)
    
    Returns:
        List of TextContent (formatted results)
    """
    query = args.get("query")
    discipline = args.get("discipline")
    history = args.get("history", [])
    k = args.get("k", 5)
    rerank = args.get("rerank", True)
    
    logger.info(f"Research query: {query[:60]}... (discipline: {discipline}, k: {k})")
    
    # 1. Infer discipline if not provided
    if not discipline:
        discipline = infer_discipline(query, history)
        logger.info(f"Inferred discipline: {discipline}")
    
    # 2. Cluster selection (with context)
    cluster_result = cluster_aware_search(
        query=query,
        discipline=discipline,
        history=history,
        top_k=3,
        threshold=0.25
    )
    
    selected_clusters = cluster_result.get("selected_clusters", [])
    fallback = cluster_result.get("fallback")
    
    if fallback:
        logger.info(f"Fallback: {fallback} ({cluster_result.get('reason')})")
    else:
        logger.info(f"Selected {len(selected_clusters)} clusters: {selected_clusters}")
    
    # 3. Search with cluster filtering
    results = search_library(
        query=query,
        discipline=discipline,
        clusters=selected_clusters if not fallback else None,
        k=k,
        rerank=rerank
    )
    
    # 4. Log query (for analysis later)
    log_query(
        query=query,
        discipline=discipline,
        selected_clusters=selected_clusters,
        results=results,
        fallback=fallback,
        history=history,
        cluster_scores=cluster_result.get("metadata", [])  # FAILURE 4: log cluster scores
    )
    
    # 5. Format results WITH ATTRIBUTION
    if not results or len(results) == 0:
        return [TextContent(
            type="text",
            text=f"No results found for: {query}"
        )]
    
    # Get attribution
    attribution = cluster_result.get("attribution")
    
    # Format output with DCA
    output = ""
    
    # DYNAMIC CLUSTER ATTRIBUTION HEADER
    if attribution:
        primary = attribution["primary_cluster"]
        output += f"# 📚 Cluster: {primary['name']}\n\n"
        
        output += "**Why this cluster:**\n"
        for reason in attribution["reasons"]:
            output += f"- {reason}\n"
        output += "\n"
        
        # Multi-cluster attribution (if applicable)
        if attribution.get("secondary_clusters"):
            output += "**Additional clusters:**\n"
            for sec in attribution["secondary_clusters"]:
                output += f"- {sec['name']} (weight: {sec['weight']:.0%})\n"
            output += "\n"
    elif not fallback:
        output += f"**Clusters searched:** {', '.join(selected_clusters)}\n\n"
    else:
        output += f"**Search mode:** Global (no clusters matched)\n\n"
    
    # RESULTS SECTION
    output += f"---\n\n"
    output += f"# Research Results: {query}\n\n"
    output += f"**Found {len(results)} results:**\n\n"
    
    for i, result in enumerate(results, 1):
        book_title = result.get("book_title", "Unknown")
        similarity = result.get("similarity", 0)
        text = result.get("text", "")
        
        # Citation metadata
        page = result.get("page")
        chapter = result.get("chapter", "")
        cfi = result.get("cfi", "")
        
        output += f"## {i}. {book_title}\n"
        output += f"**Relevance:** {similarity:.1%}\n"
        
        if cfi:
            output += f"**Location:** {cfi}\n"
        elif page:
            output += f"**Page:** {page}\n"
        elif chapter:
            output += f"**Chapter:** {chapter}\n"
        
        output += f"\n{text[:500]}...\n\n"
        output += "---\n\n"
    
    return [TextContent(type="text", text=output)]


def infer_discipline(query: str, history: List[str] = None) -> str:
    """
    Infer discipline from query + conversation context.
    
    TODO: Use LLM to infer discipline from query/history.
    For now, returns default discipline.
    
    Args:
        query: User query
        history: Conversation history
    
    Returns:
        Discipline ID (e.g., "management_knowledge")
    """
    # Placeholder: return first available discipline
    # Real implementation: LLM inference or keyword matching
    
    for item in LIBRARY_ROOT.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            index_path = item / ".discipline-index.json"
            if index_path.exists():
                return item.name
    
    # Fallback: return hardcoded default
    return "management_knowledge"


async def main():
    """Run MCP server."""
    logger.info("Starting Librarian MCP Server v3...")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
