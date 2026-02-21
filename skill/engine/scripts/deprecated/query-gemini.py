#!/usr/bin/env python3
"""
Query the personal library using LlamaIndex + Gemini.

Usage:
  python3.11 engine/engine/scripts/query.py "what books talk about AI?"
"""

import json
import sys
import time
from pathlib import Path
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Paths
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"


def load_metadata():
    """Load metadata with book/topic information."""
    if not METADATA_FILE.exists():
        return {"topics": {}, "books": {}}

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def query_library(question: str, top_k: int = 5):
    """Query the library index."""
    start = time.time()

    # Load index
    embed_model = GoogleGenAIEmbedding(
        model_name="engine/models/embedding-001",
        api_key=GOOGLE_API_KEY
    )

    storage_context = StorageContext.from_defaults(persist_dir=str(STORAGE_DIR))
    index = load_index_from_storage(storage_context, embed_model=embed_model)

    load_time = time.time() - start
    print(f"⏱️  Index loaded in {load_time*1000:.0f}ms\n")

    # Query - use retriever instead of query_engine to avoid LLM requirement
    query_start = time.time()
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(question)
    query_time = time.time() - query_start

    # Display results
    print("=" * 60)
    print(f"❓ Question: {question}")
    print("=" * 60)

    if not nodes:
        print("\nNo results found.")
    else:
        print(f"\nFound {len(nodes)} relevant passages:\n")
        for i, node in enumerate(nodes, 1):
            book_id = node.metadata.get('book_id', 'unknown')
            topic_id = node.metadata.get('topic_id', 'unknown')
            score = node.score if hasattr(node, 'score') else 0.0

            print(f"\n[{i}] {topic_id}/{book_id} (score: {score:.3f})")
            print("-" * 60)
            text = node.text[:300] + "..." if len(node.text) > 300 else node.text
            print(text)

    print("\n" + "=" * 60)
    print(f"⏱️  Query time: {query_time*1000:.0f}ms")
    print("=" * 60)

    return nodes


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3.11 engine/engine/scripts/query.py \"your question\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    print("\n🔍 Librarian Query")
    print("=" * 60)

    query_library(question)


if __name__ == "__main__":
    main()
