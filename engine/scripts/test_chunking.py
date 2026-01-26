#!/usr/bin/env python3
"""
Test chunking on a single topic to diagnose the low chunk count issue
"""
import time
from pathlib import Path
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import EpubReader

# Setup
MODELS_DIR = Path(__file__).parent.parent / "models"
TEST_TOPIC = "cybersecurity/applied"
BOOKS_DIR = Path(__file__).parent.parent / "books" / TEST_TOPIC

embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder=str(MODELS_DIR)
)
Settings.embed_model = embed_model
Settings.chunk_size = 1024
Settings.chunk_overlap = 200

print(f"🔬 Testing chunking on: {TEST_TOPIC}")
print("=" * 60)

# Load books
reader = EpubReader()
all_documents = []
book_stats = []

epub_files = list(BOOKS_DIR.glob("*.epub"))
print(f"\nFound {len(epub_files)} EPUB files")

start_time = time.time()

for epub_path in epub_files:
    print(f"\n📖 {epub_path.name}")
    try:
        docs = reader.load_data(str(epub_path))
        filesize = epub_path.stat().st_size

        # Each "doc" is the full book text
        for doc in docs:
            text_size = len(doc.text)
            expected_chunks = text_size // 1024  # rough estimate

            print(f"   Filesize: {filesize:,} bytes")
            print(f"   Text extracted: {text_size:,} chars")
            print(f"   Expected chunks: ~{expected_chunks}")

            book_stats.append({
                'filename': epub_path.name,
                'filesize': filesize,
                'text_size': text_size,
                'expected_chunks': expected_chunks
            })

        all_documents.extend(docs)

    except Exception as e:
        print(f"   ❌ Error: {e}")

load_time = time.time() - start_time
print(f"\n⏱️  Loading time: {load_time:.2f}s ({len(all_documents)} documents)")

# Build index
print("\n🔨 Building index...")
index_start = time.time()
index = VectorStoreIndex.from_documents(all_documents, show_progress=True)
index_time = time.time() - index_start

# Count actual chunks created
actual_chunks = len(index.docstore.docs)

print(f"\n📊 RESULTS:")
print("=" * 60)
print(f"Books loaded: {len(epub_files)}")
print(f"Documents: {len(all_documents)}")
print(f"Actual chunks created: {actual_chunks}")

total_expected = sum(s['expected_chunks'] for s in book_stats)
print(f"Expected chunks: {total_expected}")
print(f"Efficiency: {(actual_chunks / total_expected * 100):.1f}%")

print(f"\n⏱️  Performance:")
print(f"  Load time: {load_time:.2f}s")
print(f"  Index time: {index_time:.2f}s")
print(f"  Total: {load_time + index_time:.2f}s")
print(f"  Chunks/second: {actual_chunks / index_time:.1f}")

print(f"\n📋 Per-book breakdown:")
for stat in book_stats:
    print(f"  {stat['filename']}: {stat['expected_chunks']} chunks expected")
