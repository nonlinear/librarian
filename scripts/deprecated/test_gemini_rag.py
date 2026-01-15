#!/usr/bin/env python3
"""
Test script for RAG with embeddings.
Triggered by CLI: python3 scripts/test_gemini_rag.py (indexes a test EPUB and runs a query)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.readers.file import EpubReader

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from rag_cost_tracker import RAGCostTracker

# Load environment variables
load_dotenv()

# Initialize cost tracker
cost_tracker = RAGCostTracker()

# Choose embedding model (OpenAI or Gemini)
USE_OPENAI = os.getenv("OPENAI_API_KEY") is not None
USE_GEMINI = os.getenv("GOOGLE_API_KEY") is not None

if USE_OPENAI:
    from llama_index.embeddings.openai import OpenAIEmbedding
    print("\n🔧 Using OpenAI embeddings (paid)")
    embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    model_name = "openai_embedding"
elif USE_GEMINI:
    from llama_index.embeddings.gemini import GeminiEmbedding
    from llama_index.llms.gemini import Gemini
    print("\n🔧 Using Gemini embeddings and LLM (free tier)")
    api_key = os.getenv("GOOGLE_API_KEY")
    embed_model = GeminiEmbedding(
        model_name="models/embedding-001",
        api_key=api_key
    )
    llm = Gemini(model_name="models/gemini-pro", api_key=api_key)
    Settings.llm = llm
    model_name = "gemini_embedding"
else:
    raise ValueError("No API key found. Set OPENAI_API_KEY or GOOGLE_API_KEY in .env")

# Setup paths
BASE_DIR = Path(__file__).parent.parent
BOOKS_DIR = BASE_DIR / "literature" / "books"
STORAGE_DIR = BASE_DIR / "storage"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

print("\n📚 AI Literature - RAG Test with Cost Tracking")
print("=" * 50)
print(f"Books folder: {BOOKS_DIR}")
print(f"Storage folder: {STORAGE_DIR}")

Settings.embed_model = embed_model

# Load documents
print(f"\n📖 Loading EPUB files from {BOOKS_DIR}...")
documents = []
book_names = []

# Find EPUBs (both files and directories)
epub_files = list(BOOKS_DIR.glob("*.epub"))
epub_dirs = [d for d in BOOKS_DIR.iterdir() if d.is_dir() and d.suffix == '.epub']

if not epub_files and not epub_dirs:
    print("❌ No EPUB files found!")
    exit(1)

# Load EPUB files
for epub_file in epub_files:
    if epub_file.is_file():
        book_name = epub_file.stem
        book_names.append(book_name)
        print(f"   Loading: {book_name}")
        reader = SimpleDirectoryReader(
            input_files=[str(epub_file)],
            file_extractor={".epub": EpubReader()}
        )
        docs = reader.load_data()
        documents.extend(docs)
        print(f"   ✓ Loaded {len(docs)} chunks")

# Load EPUB directories (unzipped)
for epub_dir in epub_dirs:
    book_name = epub_dir.stem
    book_names.append(book_name)
    print(f"   Loading: {book_name}")
    reader = SimpleDirectoryReader(
        input_dir=str(epub_dir),
        required_exts=[".html", ".xhtml"],
        recursive=True
    )
    docs = reader.load_data()
    documents.extend(docs)
    print(f"   ✓ Loaded {len(docs)} chunks")

print(f"✓ Total: {len(documents)} document chunks")

# Estimate token count for cost tracking (rough estimate: ~0.75 tokens per char)
total_chars = sum(len(doc.text) for doc in documents)
estimated_tokens = int(total_chars * 0.75)
print(f"📊 Estimated tokens: ~{estimated_tokens:,}")

# Create index
print("\n🔨 Creating vector index (this may take a minute)...")
index = VectorStoreIndex.from_documents(documents)
print("✓ Index created successfully")

# Log embedding costs for each book
print("\n💰 Logging embedding costs...")
tokens_per_book = estimated_tokens // len(book_names)
for book_name in book_names:
    cost = cost_tracker.log_embedding(book_name, tokens_per_book, model_name)
    print(f"   {book_name}: ${cost:.4f}")

# Persist index
print(f"\n💾 Saving index to {STORAGE_DIR}...")
index.storage_context.persist(persist_dir=str(STORAGE_DIR))
print("✓ Index saved")

# Test query
print("\n🔍 Testing query...")
query_engine = index.as_query_engine()
test_query = "What is this book about?"
response = query_engine.query(test_query)

# Log query cost
query_tokens = len(test_query) * 0.75  # Rough estimate
if book_names:
    query_cost = cost_tracker.log_query(book_names[0], int(query_tokens), model_name.replace("embedding", "query"))
    print(f"💰 Query cost: ${query_cost:.6f}")

print(f"\n📝 Response:\n{response}\n")

# Show cost report
cost_tracker.print_report()

print("\n" + "=" * 50)
print("✅ Test completed successfully!")
print(f"\n💡 Next steps:")
print("   1. Try different queries")
print("   2. Add more books to literature/books/")
print("   3. Create REST API endpoint")
print("   4. View costs: python3 code/rag_cost_tracker.py")
