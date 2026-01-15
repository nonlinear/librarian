#!/usr/bin/env python3
"""
Query indexed books using RAG.
Triggered by CLI: python3 query_book.py "Book Name" "Your question"
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import StorageContext, load_index_from_storage, Settings

# MCP server check and auto-start
import psutil
import subprocess

def is_mcp_server_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if (
                proc.info['name'] in ['python3.11', 'python3'] and
                any('literature_mcp_server.py' in str(arg) for arg in proc.info['cmdline'])
            ):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def start_mcp_server():
    subprocess.Popen([
        '/opt/homebrew/bin/python3.11',
        '/Users/nfrota/Documents/literature/scripts/literature_mcp_server.py'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Ensure MCP server is running before query
if not is_mcp_server_running():
    print("[INFO] MCP server not running. Starting MCP server...")
    start_mcp_server()
    import time; time.sleep(2)  # Wait briefly to ensure server starts

# Load environment variables
load_dotenv()

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))
from rag_cost_tracker import RAGCostTracker

# Setup paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"

def setup_models():
    """Setup embedding and LLM models"""
    USE_GEMINI = os.getenv("GOOGLE_API_KEY") is not None

    if USE_GEMINI:
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
        from llama_index.llms.google_genai import GoogleGenAI

        api_key = os.getenv("GOOGLE_API_KEY")
        embed_model = GoogleGenAIEmbedding(
            model_name="models/embedding-001",
            api_key=api_key,
        )
        llm = GoogleGenAI(model="models/gemini-2.5-flash", api_key=api_key)
        Settings.embed_model = embed_model
        Settings.llm = llm
        return "gemini"
    else:
        raise ValueError("GOOGLE_API_KEY not found in .env")

def query_books(book_name: str, question: str):
    """Query the indexed books"""

    # Setup models
    model_type = setup_models()

    # Load index from storage
    print(f"📚 Loading index from {STORAGE_DIR}...")
    storage_context = StorageContext.from_defaults(persist_dir=str(STORAGE_DIR))
    index = load_index_from_storage(storage_context)
    print("✓ Index loaded\n")

    # Create query engine
    query_engine = index.as_query_engine()

    # Execute query
    print(f"🔍 Querying: {book_name}")
    print(f"❓ Question: {question}\n")
    print("=" * 80)

    response = query_engine.query(question)

    print(f"📝 Answer:\n\n{response}\n")

    # Extract and display sources
    if hasattr(response, 'source_nodes') and response.source_nodes:
        print("\n📚 Sources:")
        print("-" * 80)
        seen_sources = set()
        for i, node in enumerate(response.source_nodes[:3], 1):  # Top 3
            metadata = node.node.metadata if hasattr(node.node, 'metadata') else {}
            file_name = metadata.get('file_name', 'Unknown')
            file_path = metadata.get('file_path', '')
            score = node.score if hasattr(node, 'score') else 0.0

            # Get book info
            if file_path:
                book_path = Path(file_path)
                source_book = book_path.stem
            else:
                source_book = file_name

            if source_book not in seen_sources:
                print(f"   {i}. {source_book} (relevance: {score:.2f})")
                # Show snippet
                text_snippet = node.node.text[:150].replace('\n', ' ')
                print(f"      \"{text_snippet}...\"")
                seen_sources.add(source_book)

    print("=" * 80)

    # Track costs
    cost_tracker = RAGCostTracker()
    query_tokens = int(len(question) * 0.75)
    cost = cost_tracker.log_query(book_name, query_tokens, f"{model_type}_query")

    print(f"\n💰 Query cost: ${cost:.6f}")

    return response

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 query_book.py 'Book Name' 'Your question'")
        print("Example: python3 query_book.py 'Seeing Like a State' 'What is legibility?'")
        sys.exit(1)

    book_name = sys.argv[1]
    question = sys.argv[2]

    try:
        query_books(book_name, question)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
