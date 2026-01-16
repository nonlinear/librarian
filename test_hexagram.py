#!/usr/bin/env python3
"""Test query for hexagram 63"""
import sys
import pickle
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# Set model cache
os.environ['SENTENCE_TRANSFORMERS_HOME'] = 'models'

# Load new index directly
oracles_dir = Path("storage/oracles")
index = faiss.read_index(str(oracles_dir / "faiss.index"))
print(f"✅ FAISS index dimension: {index.d}")
print(f"✅ Total vectors: {index.ntotal}")

# Load chunks
with open(oracles_dir / "chunks.pkl", 'rb') as f:
    chunks = pickle.load(f)
print(f"✅ Total chunks: {len(chunks)}")

# Test search
model = SentenceTransformer('all-MiniLM-L6-v2')
query_emb = model.encode("hexagram 63 after completion judgment", convert_to_numpy=True).astype(np.float32).reshape(1, -1)
print(f"✅ Query embedding dimension: {query_emb.shape[1]}")

distances, indices = index.search(query_emb, 5)
print(f"\n📖 Top 5 results for hexagram 63:\n")
for i, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
    chunk = chunks[idx]
    print(f"{i}️⃣ [{chunk['book_title']}] (similarity: {1-dist:.3f})")
    print(f"{chunk['text'][:600]}...\n")
