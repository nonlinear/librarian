#!/usr/bin/env python3
"""
Query Logger v3 — Logs all queries for analysis

Logs every query with:
- Query text
- Selected clusters
- Results (books, similarity scores)
- Timestamp

Output: query-log.jsonl (append-only)
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Log path
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "query-log.jsonl"


def log_query(
    query: str,
    discipline: str,
    selected_clusters: List[str],
    results: List[Dict],
    fallback: str = None,
    history: List[str] = None,
    cluster_scores: List[Dict] = None
):
    """
    Log a query to query-log.jsonl.
    
    Args:
        query: User query
        discipline: Discipline ID
        selected_clusters: List of cluster IDs selected
        results: List of result dicts
        fallback: Fallback reason (if any)
        history: Conversation history (optional)
        cluster_scores: Scored clusters (for debugging)
    """
    # Create logs dir if needed
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Detect cluster vs chunk mismatch
    # If cluster score high but result similarity low → retrieval problem
    cluster_chunk_mismatch = False
    if cluster_scores and results:
        top_cluster_score = cluster_scores[0].get("score", 0) if cluster_scores else 0
        top_result_score = results[0].get("similarity", 0) if results else 0
        
        # Red flag: cluster good, chunk bad
        if top_cluster_score > 0.6 and top_result_score < 0.4:
            cluster_chunk_mismatch = True
    
    # Build log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "discipline": discipline,
        "selected_clusters": selected_clusters,
        "fallback": fallback,
        "history": history[-3:] if history else [],
        "results_count": len(results),
        "cluster_chunk_mismatch": cluster_chunk_mismatch,  # FAILURE 4 detection
        "top_cluster_scores": [
            {"id": c["cluster_id"], "score": c["score"]}
            for c in (cluster_scores or [])[:3]
        ],
        "results": [
            {
                "book_title": r.get("book_title"),
                "book_id": r.get("book_id"),
                "similarity": r.get("similarity"),
                "page": r.get("page"),
                "cfi": r.get("cfi")
            }
            for r in results[:5]  # Log top-5 only
        ]
    }
    
    # Append to log file (JSONL format)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")


def get_recent_queries(n: int = 10) -> List[Dict]:
    """
    Get last N queries from log.
    
    Args:
        n: Number of queries to return
    
    Returns:
        List of log entry dicts
    """
    if not LOG_FILE.exists():
        return []
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    # Return last N
    recent = []
    for line in lines[-n:]:
        try:
            recent.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    
    return recent


# Example usage
if __name__ == "__main__":
    # Test logging
    log_query(
        query="What is clustering?",
        discipline="management_knowledge",
        selected_clusters=["cluster-abc123", "cluster-def456"],
        results=[
            {"book_title": "Book A", "book_id": "book_a", "similarity": 0.85},
            {"book_title": "Book B", "book_id": "book_b", "similarity": 0.72}
        ],
        fallback=None,
        history=["Previous message 1", "Previous message 2"]
    )
    
    print("✅ Logged query to", LOG_FILE)
    
    # Read recent
    recent = get_recent_queries(5)
    print(f"\n📊 Last {len(recent)} queries:\n")
    for entry in recent:
        print(f"  • {entry['query'][:60]}... ({entry['results_count']} results)")
