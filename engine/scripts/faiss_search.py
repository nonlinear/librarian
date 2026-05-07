#!/usr/bin/env python3
"""
FAISS Search Layer - Production
Abstraction layer for semantic retrieval over FAISS index
"""
import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FAISSSearch:
    """
    Production-grade FAISS search interface
    
    Responsibilities:
    - Load FAISS index + metadata
    - Normalize query embeddings
    - Return ranked chunks with scores
    - Handle edge cases (empty index, invalid queries)
    """
    
    def __init__(self, index_path: str, metadata_path: str):
        """
        Initialize FAISS searcher
        
        Args:
            index_path: Path to faiss.index file
            metadata_path: Path to metadata.json file
        """
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        
        # Load index
        logger.info(f"Loading FAISS index from {self.index_path}")
        self.index = faiss.read_index(str(self.index_path))
        
        # Load metadata
        logger.info(f"Loading metadata from {self.metadata_path}")
        with open(self.metadata_path) as f:
            data = json.load(f)
            self.chunks = data["chunks"]
            self.books = {b["id"]: b for b in data.get("books", [])}
        
        logger.info(f"✅ FAISS loaded: {self.index.ntotal:,} vectors, {len(self.chunks):,} chunks")
        
        # Validate consistency
        if self.index.ntotal != len(self.chunks):
            raise ValueError(
                f"Index/metadata mismatch: {self.index.ntotal} vectors != {len(self.chunks)} chunks"
            )
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for top-k similar chunks
        
        Args:
            query_embedding: 384-dim embedding vector
            k: Number of results to return
            min_score: Optional score threshold (0-1)
        
        Returns:
            List of chunks with metadata + scores
            [
                {
                    "chunk_id": "ch_...",
                    "book_id": "book_...",
                    "text": "...",
                    "source": {...},
                    "paragraphs": [...],
                    "score": 0.85,
                    "book_title": "..."
                },
                ...
            ]
        """
        # Validate input
        if len(query_embedding) != self.index.d:
            raise ValueError(f"Query dimension {len(query_embedding)} != index dimension {self.index.d}")
        
        # Normalize query (FAISS IndexFlatIP expects normalized vectors)
        q = np.array(query_embedding, dtype="float32").reshape(1, -1)
        faiss.normalize_L2(q)
        
        # Search
        scores, ids = self.index.search(q, k)
        
        # Build results
        results = []
        for score, idx in zip(scores[0], ids[0]):
            # FAISS returns -1 for missing results
            if idx < 0 or idx >= len(self.chunks):
                continue
            
            # Apply score threshold
            if min_score is not None and score < min_score:
                continue
            
            # Get chunk metadata
            chunk = self.chunks[idx]
            
            # Handle both book_id and book_hash (mixed metadata from bootstrap)
            book_key = chunk.get("book_id") or chunk.get("book_hash")
            
            # Enrich with book title
            book = self.books.get(book_key, {})
            
            results.append({
                **chunk,
                "score": float(score),
                "book_title": book.get("title", "Unknown"),
                "book_author": book.get("author", "Unknown")
            })
        
        return results
    
    def search_text(
        self,
        query_text: str,
        embedding_model,
        k: int = 10,
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Convenience wrapper: text → embedding → search
        
        Args:
            query_text: Natural language query
            embedding_model: Model with .encode() method
            k: Number of results
            min_score: Optional threshold
        
        Returns:
            Search results
        """
        # Generate embedding
        embedding = embedding_model.encode(query_text).tolist()
        
        # Search
        return self.search(embedding, k=k, min_score=min_score)
    
    def get_stats(self) -> Dict:
        """
        Return index statistics
        
        Returns:
            {
                "total_vectors": int,
                "total_chunks": int,
                "total_books": int,
                "dimensions": int,
                "index_type": str
            }
        """
        return {
            "total_vectors": self.index.ntotal,
            "total_chunks": len(self.chunks),
            "total_books": len(self.books),
            "dimensions": self.index.d,
            "index_type": type(self.index).__name__
        }
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """
        Retrieve specific chunk by ID
        
        Args:
            chunk_id: Chunk identifier
        
        Returns:
            Chunk metadata or None
        """
        for chunk in self.chunks:
            if chunk["chunk_id"] == chunk_id:
                return chunk
        return None


# Singleton loader (lazy initialization)
_searcher: Optional[FAISSSearch] = None

def get_searcher(
    index_path: str = "/app/books/faiss.index",
    metadata_path: str = "/app/books/metadata.json"
) -> FAISSSearch:
    """
    Get or create singleton FAISS searcher
    
    Args:
        index_path: Path to FAISS index
        metadata_path: Path to metadata JSON
    
    Returns:
        FAISSSearch instance (cached)
    """
    global _searcher
    
    if _searcher is None:
        _searcher = FAISSSearch(index_path, metadata_path)
    
    return _searcher


# Example usage
if __name__ == "__main__":
    import sys
    
    # Test load
    searcher = get_searcher()
    
    # Print stats
    stats = searcher.get_stats()
    print("\n📊 FAISS Search Layer Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value:,}" if isinstance(value, int) else f"   {key}: {value}")
    
    # Test search (requires embedding model)
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
        query = sys.argv[1] if len(sys.argv) > 1 else "quantum mechanics"
        print(f"\n🔍 Test Query: '{query}'")
        
        results = searcher.search_text(query, model, k=5)
        
        print(f"\n✅ Top {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result['score']:.3f}] {result['book_title']}")
            print(f"   {result['text'][:150]}...")
    
    except ImportError:
        print("\n⚠️  sentence-transformers not available (test search skipped)")
    except Exception as e:
        print(f"\n❌ Search test failed: {e}")
