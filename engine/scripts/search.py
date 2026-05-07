#!/usr/bin/env python3
"""
Librarian Search v3 — Cluster-Filtered FAISS Search

Replaces v2 topic-based search with cluster-aware filtering.

Usage:
    from search import search_library
    
    results = search_library(
        query="What is clustering?",
        discipline="management_knowledge",
        clusters=["cluster-0", "cluster-1"],
        k=5
    )
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

from sentence_transformers import SentenceTransformer
import faiss

# Paths
LIBRARY_ROOT = Path(__file__).parent.parent.parent / "books"
MODELS_DIR = Path(__file__).parent.parent / "models"

# Embedding model (same as indexer)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Global embed model (lazy load)
embed_model = None


def get_embed_model():
    """Lazy load embedding model."""
    global embed_model
    if embed_model is None:
        embed_model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=str(MODELS_DIR))
    return embed_model


def load_discipline_index(discipline: str) -> Dict:
    """
    Load .discipline-index.json for a discipline.
    
    Args:
        discipline: Discipline ID (e.g., "management_knowledge")
    
    Returns:
        Discipline index dict
    """
    discipline_path = LIBRARY_ROOT / discipline
    index_path = discipline_path / ".discipline-index.json"
    
    if not index_path.exists():
        raise FileNotFoundError(f"Discipline index not found: {index_path}")
    
    with open(index_path, 'r') as f:
        return json.load(f)


def load_topic_chunks(topic_path: Path) -> tuple:
    """
    Load chunks and FAISS index for a topic.
    
    Args:
        topic_path: Path to topic directory (e.g., /app/books/design/interaction)
    
    Returns:
        Tuple of (chunks_list, faiss_index) or (None, None) if not found
    """
    chunks_file = topic_path / ".chunks.json"
    faiss_file = topic_path / ".faiss.index"
    
    if not chunks_file.exists() or not faiss_file.exists():
        return None, None
    
    try:
        with open(chunks_file, 'r') as f:
            chunks = json.load(f)
        faiss_index = faiss.read_index(str(faiss_file))
        return chunks, faiss_index
    except Exception as e:
        print(f"Warning: Failed to load chunks for {topic_path}: {e}")
        return None, None


def search_chunks_in_topic(
    query_emb: np.ndarray,
    topic_path: Path,
    book_ids_filter: Optional[set] = None,
    k: int = 3
) -> List[Dict]:
    """
    Search for best chunks within a topic, optionally filtering by book_ids.
    
    Args:
        query_emb: Query embedding vector
        topic_path: Path to topic directory
        book_ids_filter: Set of book_ids to filter (None = all)
        k: Number of chunks to return
    
    Returns:
        List of chunk results with text, metadata, and scores
    """
    chunks, faiss_index = load_topic_chunks(topic_path)
    
    if chunks is None or faiss_index is None:
        return []
    
    # Search FAISS for top chunks
    search_k = k * 5 if book_ids_filter else k
    query_reshaped = query_emb.reshape(1, -1).astype('float32')
    distances, indices = faiss_index.search(query_reshaped, min(search_k, len(chunks)))
    
    # Collect results
    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1 or idx >= len(chunks):
            continue
        
        chunk = chunks[idx]
        
        # Filter by book_id if specified
        if book_ids_filter and chunk["book_id"] not in book_ids_filter:
            continue
        
        distance = distances[0][i]
        similarity = 1 / (1 + distance)
        
        # Build result
        result = {
            "book_title": chunk.get("book_title", "Unknown"),
            "book_author": chunk.get("book_author", "Unknown"),
            "book_id": chunk["book_id"],
            "similarity": float(similarity),
            "text": chunk.get("chunk_full", ""),
            "page": chunk.get("page"),
            "chapter": chunk.get("chapter"),
            "paragraph": chunk.get("paragraph"),
            "cfi": None  # TODO: generate CFI from chapter + paragraph
        }
        
        results.append(result)
        
        if len(results) >= k:
            break
    
    return results


def search_library(
    query: str,
    discipline: str,
    clusters: Optional[List[str]] = None,
    k: int = 5,
    rerank: bool = True
) -> List[Dict]:
    """
    Search library with optional cluster filtering.
    
    Strategy: 
    1. Book-level search (fast, using discipline index)
    2. Chunk-level search (precise, using topic FAISS indices)
    
    Args:
        query: Search query (natural language)
        discipline: Discipline ID (e.g., "management_knowledge")
        clusters: List of cluster IDs to search (None = search all)
        k: Number of results to return
        rerank: Enable reranking (TODO: implement)
    
    Returns:
        List of result dicts with book_title, similarity, text, page, cfi, etc.
    """
    # 1. Load discipline index
    index = load_discipline_index(discipline)
    
    books = index.get("books", [])
    embeddings = index.get("embeddings", {})
    clusters_metadata = index.get("clusters", [])
    
    if not books:
        return []
    
    # 2. Build cluster → book_ids mapping (for post-filtering)
    cluster_to_books = {}
    if clusters:
        for cluster_meta in clusters_metadata:
            if cluster_meta["id"] in clusters:
                cluster_to_books[cluster_meta["id"]] = set(cluster_meta["book_ids"])
        
        # Flatten to allowed book_ids
        allowed_book_ids = set()
        for book_ids in cluster_to_books.values():
            allowed_book_ids.update(book_ids)
    else:
        # No cluster filtering: all books allowed
        allowed_book_ids = None
    
    # 3. Generate query embedding
    model = get_embed_model()
    query_emb = model.encode(query, convert_to_numpy=True)
    
    # 4. Build FAISS index ONCE (all books in discipline)
    # TODO: Cache this index (rebuild only when discipline changes)
    book_ids = [b["id"] for b in books]
    book_embeddings = np.array([embeddings[bid] for bid in book_ids]).astype('float32')
    
    dimension = book_embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(book_embeddings)
    
    # 5. Book-level search (find relevant books)
    search_k = min(10, len(books))  # Top 10 books for chunk search
    query_emb_reshaped = query_emb.reshape(1, -1).astype('float32')
    distances, indices = faiss_index.search(query_emb_reshaped, search_k)
    
    # 6. Collect relevant book_ids (with cluster filtering)
    relevant_book_ids = set()
    for idx in indices[0]:
        if idx == -1:
            continue
        
        book = books[idx]
        book_id = book["id"]
        
        # Filter by cluster
        if allowed_book_ids and book_id not in allowed_book_ids:
            continue
        
        relevant_book_ids.add(book_id)
    
    if not relevant_book_ids:
        return []
    
    # 7. Chunk-level search across all topics in discipline
    # Scan for topic directories and search chunks
    all_chunk_results = []
    discipline_path = LIBRARY_ROOT / discipline
    
    # Recursively scan for topic directories (containing .chunks.json)
    def find_topic_dirs(base_path: Path) -> List[Path]:
        topic_dirs = []
        for item in base_path.iterdir():
            if item.name.startswith('.'):
                continue
            if item.is_dir():
                # Check if this is a topic directory (has .chunks.json)
                if (item / ".chunks.json").exists():
                    topic_dirs.append(item)
                else:
                    # Recurse into subdirectories
                    topic_dirs.extend(find_topic_dirs(item))
        return topic_dirs
    
    topic_dirs = find_topic_dirs(discipline_path)
    
    # Search chunks in each topic directory
    for topic_path in topic_dirs:
        chunk_results = search_chunks_in_topic(
            query_emb=query_emb,
            topic_path=topic_path,
            book_ids_filter=relevant_book_ids,
            k=k * 2  # Get more chunks, will deduplicate/sort later
        )
        
        all_chunk_results.extend(chunk_results)
    
    # 8. Sort by similarity and return top k
    all_chunk_results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Fallback: If no chunks found from relevant books, return book-level results
    if len(all_chunk_results) == 0:
        print("Warning: No chunks found for relevant books. Returning book-level results.")
        # Return book-level results as fallback
        fallback_results = []
        for idx in indices[0][:k]:
            if idx == -1:
                continue
            
            book = books[idx]
            book_id = book["id"]
            
            # Filter by cluster
            if allowed_book_ids and book_id not in allowed_book_ids:
                continue
            
            distance = distances[0][indices[0].tolist().index(idx)]
            similarity = 1 / (1 + distance)
            
            fallback_results.append({
                "book_title": book["title"],
                "book_author": book.get("author", "Unknown"),
                "book_id": book_id,
                "similarity": float(similarity),
                "text": f"[Book-level match: {book['title']}. Chunks not indexed for this book yet.]",
                "page": None,
                "chapter": None,
                "paragraph": None,
                "cfi": None
            })
            
            if len(fallback_results) >= k:
                break
        
        return fallback_results
    
    return all_chunk_results[:k]


# Test/demo
if __name__ == "__main__":
    # Example search
    results = search_library(
        query="what are design tokens",
        discipline="design",
        clusters=None,  # Global search
        k=3
    )
    
    print("\n🔍 Search Results:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['book_title']}")
        print(f"   Similarity: {r['similarity']:.3f}")
        print(f"   {r['text'][:100]}...\n")
