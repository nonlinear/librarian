#!/usr/bin/env python3
"""
MCP Server for Literature RAG
Triggered automatically by VS Code Copilot MCP queries. Serves book answers to Copilot.
"""

import os
import sys
import json
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from rag_cost_tracker import RAGCostTracker

# Load environment
load_dotenv(dotenv_path="/Users/nfrota/Documents/notes/.env", override=True)

# Setup paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
BOOKS_DIR = BASE_DIR / "books"

# Initialize models
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

embed_model = GoogleGenAIEmbedding(model_name="engine/models/embedding-001", api_key=api_key)
llm = GoogleGenAI(model="gemini-2.5-pro", api_key=api_key)
Settings.embed_model = embed_model
Settings.llm = llm

# Load index

from llama_index.readers.file import EpubReader

from llama_index.core import VectorStoreIndex

docs = []
errored_epubs = []
for folder in BOOKS_DIR.iterdir():
    if not folder.is_dir() or folder.name.startswith('.'):
        continue
    for item in folder.iterdir():
        if item.suffix == '.epub' and item.is_file():
            reader = EpubReader()
            try:
                docs.extend(reader.load_data(str(item)))
            except Exception as e:
                errored_epubs.append((str(item), str(e)))

if errored_epubs:
    print("[WARNING] The following .epub files could not be loaded:")
    for fname, err in errored_epubs:
        print(f"  {fname}: {err}")

index = VectorStoreIndex(docs)
query_engine = index.as_query_engine()

# Initialize cost tracker
cost_tracker = RAGCostTracker()


def load_folder_topics() -> dict[str, dict[str, Any]]:
    """Load .rag-topics from each folder to determine when to use books"""
    folders = {}

    for folder in BOOKS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue

        topics_file = folder / ".rag-topics"
        if topics_file.exists():
            content = topics_file.read_text()

            # Parse robots.txt style format
            keywords = []
            description = ""
            auto_update = False

            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.startswith('Keywords:'):
                    keyword_str = line.split('Keywords:', 1)[1].strip()
                    keywords = [k.strip().lower() for k in keyword_str.split(',')]

                elif line.startswith('Description:'):
                    description = line.split('Description:', 1)[1].strip()

                elif line.startswith('Auto-update:'):
                    auto_update = 'true' in line.lower()

            folders[folder.name] = {
                "path": str(folder),
                "keywords": [k for k in keywords if k],
                "description": description,
                "auto_update": auto_update,
                "config_file": str(topics_file)
            }

    return folders


def should_query_folder(question: str, folder_info: dict) -> bool:
    """Check if question matches folder's topics"""
    question_lower = question.lower()
    keywords = folder_info.get("keywords", [])

    # Check if any keyword appears in question
    return any(keyword in question_lower for keyword in keywords)


def auto_detect_relevant_folders(question: str) -> list[str]:
    """Auto-detect which folders are relevant to the question"""
    folder_topics = load_folder_topics()
    relevant = []

    for folder_name, folder_info in folder_topics.items():
        if should_query_folder(question, folder_info):
            relevant.append(folder_name)

    return relevant


def list_books() -> dict[str, Any]:
    """List all indexed books organized by folder"""
    folder_topics = load_folder_topics()
    folders_data = {}

    for folder in BOOKS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue

        books = []
        for item in folder.iterdir():
            if item.suffix == '.epub' or (item.is_dir() and item.suffix == '.epub'):
                books.append({
                    "name": item.stem,
                    "path": str(item),
                    "type": "file" if item.is_file() else "directory"
                })

        if books:
            folders_data[folder.name] = {
                "books": books,
                "topics": folder_topics.get(folder.name, {}).get("keywords", [])[:10],  # Show first 10
                "count": len(books)
            }

    return {
        "folders": folders_data,
        "total_folders": len(folders_data),
        "storage_path": str(STORAGE_DIR)
    }


def query_literature(question: str, book_context: str = None, auto_detect: bool = True) -> dict[str, Any]:
    """
    Query indexed literature with optional book context

    Args:
        question: The question to ask
        book_context: Optional book name to provide context
        auto_detect: Auto-detect relevant folders based on keywords
    """
    # Auto-detect relevant folders if enabled
    relevant_folders = []
    if auto_detect and not book_context:
        relevant_folders = auto_detect_relevant_folders(question)

    # Add book context to question if provided
    context_info = ""
    if book_context:
        context_info = f" [Context: {book_context}]"
        enhanced_question = f"In the context of '{book_context}': {question}"
    elif relevant_folders:
        context_info = f" [Auto-detected: {', '.join(relevant_folders)}]"
        enhanced_question = f"Using knowledge from {', '.join(relevant_folders)}: {question}"
    else:
        enhanced_question = question

    # Query the index
    response = query_engine.query(enhanced_question)

    # Extract sources from response
    sources = []
    if hasattr(response, 'source_nodes') and response.source_nodes:
        seen_sources = set()
        for node in response.source_nodes:
            # Extract metadata from node
            metadata = node.node.metadata if hasattr(node.node, 'metadata') else {}
            file_name = metadata.get('file_name', 'Unknown')
            file_path = metadata.get('file_path', '')

            # Extract book name from path
            if file_path:
                book_path = Path(file_path)
                # Get folder name (e.g., "urbanism") and book name
                folder = book_path.parent.parent.name if 'books' in str(book_path) else 'Unknown'
                book_name = book_path.stem if book_path.suffix == '.epub' else file_name
            else:
                folder = 'Unknown'
                book_name = file_name

            # Create citation key
            citation_key = f"{folder}/{book_name}"

            if citation_key not in seen_sources:
                sources.append({
                    "book": book_name,
                    "folder": folder,
                    "citation": f"[{book_name}](/Users/nfrota/Documents/literature/books/{folder}/{book_name}.epub)",
                    "score": node.score if hasattr(node, 'score') else 0.0,
                    "snippet": node.text[:150] if hasattr(node, 'text') else "",
                })
                seen_sources.add(citation_key)

    # Format sources for display
    sources_text = ""
    if sources:
        sources_text = "\n\n**Sources:**\n"
        for src in sources[:3]:  # Top 3 sources
            sources_text += f"- {src['citation']}\n  🔍 Search: \"{src.get('snippet', '')[:100]}...\"\n"

    # Track costs
    query_tokens = int(len(enhanced_question) * 0.75)
    cost = cost_tracker.log_query(
        book_context or relevant_folders[0] if relevant_folders else "general_query",
        query_tokens,
        "gemini_query"
    )

    return {
        "question": question,
        "book_context": book_context,
        "auto_detected_folders": relevant_folders if not book_context else [],
        "answer": str(response) + sources_text,
        "sources": sources,
        "cost": f"${cost:.6f}",
        "source_nodes": len(response.source_nodes) if hasattr(response, 'source_nodes') else 0,
        "context_used": context_info
    }


def get_costs() -> dict[str, Any]:
    """Get cost statistics"""
    costs = cost_tracker.costs

    total_embedding = sum(
        book["embedding_cost"]
        for book in costs.get("books", {}).values()
    )

    total_queries = sum(
        len(book.get("queries", []))
        for book in costs.get("books", {}).values()
    )

    total_query_cost = sum(
        q["cost"]
        for book in costs.get("books", {}).values()
        for q in book.get("queries", [])
    )

    return {
        "total_embedding_cost": f"${total_embedding:.4f}",
        "total_queries": total_queries,
        "total_query_cost": f"${total_query_cost:.4f}",
        "total_cost": f"${total_embedding + total_query_cost:.4f}",
        "books": list(costs.get("books", {}).keys())
    }


def handle_request(method: str, params: dict[str, Any]) -> dict[str, Any]:
    """Handle MCP requests"""
    if method == "setLogLevel":
        return {"result": "Log level not implemented"}

    if method == "initialize":
        return {"result": "MCP server initialized"}

    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "query_literature",
                    "description": "Query indexed literature/books using RAG. Searches through embedded book content to answer questions.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to ask about the literature"
                            }
                        }
                    }
                },
                {
                    "name": "list_books",
                    "description": "List all indexed books in the literature database",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_literature_costs",
                    "description": "Get cost statistics for literature RAG usage",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "query_literature":
            result = query_literature(
                arguments["question"],
                arguments.get("book_context")
            )
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        if tool_name == "list_books":
            result = list_books()
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        if tool_name == "get_literature_costs":
            result = get_costs()
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        raise ValueError(f"Unknown tool: {tool_name}")

    raise ValueError(f"Unknown method: {method}")
