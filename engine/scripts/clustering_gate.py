#!/usr/bin/env python3
"""
Clustering Gate — Entropy-Based Adaptive Clustering

Decides whether to cluster based on dataset semantic diversity.

Logic:
- Low entropy (high avg similarity) → Single cluster (no fake structure)
- Medium entropy → Clustering allowed
- High entropy → Stronger clustering encouraged

Key insight: Clustering is not always the right abstraction.
Only create structure when data supports structure.
"""
import numpy as np
from typing import Dict, List
from pathlib import Path


def compute_pairwise_similarities(embeddings: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Compute pairwise cosine similarities for all embeddings.
    
    Args:
        embeddings: Dict of {book_id: embedding_vector}
    
    Returns:
        Similarity matrix (n x n)
    """
    book_ids = list(embeddings.keys())
    n = len(book_ids)
    
    sim_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i, n):
            emb_i = embeddings[book_ids[i]]
            emb_j = embeddings[book_ids[j]]
            
            sim = np.dot(emb_i, emb_j) / (np.linalg.norm(emb_i) * np.linalg.norm(emb_j))
            sim_matrix[i, j] = sim
            sim_matrix[j, i] = sim  # Symmetric
    
    return sim_matrix


def compute_dataset_entropy(embeddings: Dict[str, np.ndarray]) -> Dict:
    """
    Compute semantic diversity (entropy) of dataset.
    
    High avg similarity = low entropy = no meaningful clustering possible.
    
    Args:
        embeddings: Dict of {book_id: embedding_vector}
    
    Returns:
        Entropy analysis dict
    """
    if len(embeddings) < 3:
        return {
            "entropy": "undefined",
            "avg_similarity": None,
            "std_similarity": None,
            "reason": "Too few books (need >= 3)"
        }
    
    # Compute pairwise similarities
    sim_matrix = compute_pairwise_similarities(embeddings)
    
    # Extract upper triangle (exclude diagonal)
    n = len(embeddings)
    upper_triangle = []
    for i in range(n):
        for j in range(i + 1, n):
            upper_triangle.append(sim_matrix[i, j])
    
    avg_similarity = np.mean(upper_triangle)
    std_similarity = np.std(upper_triangle)
    
    # Entropy levels (thresholds tuned empirically)
    if avg_similarity > 0.85:
        entropy = "low"
        cluster_recommendation = "single_cluster"
        reason = "High avg similarity (low diversity) — clustering would create arbitrary boundaries"
    elif avg_similarity > 0.70:
        entropy = "medium"
        cluster_recommendation = "clustering_allowed"
        reason = "Moderate diversity — clustering may reveal structure"
    else:
        entropy = "high"
        cluster_recommendation = "clustering_encouraged"
        reason = "High diversity — clustering likely to find meaningful structure"
    
    return {
        "entropy": entropy,
        "avg_similarity": avg_similarity,
        "std_similarity": std_similarity,
        "cluster_recommendation": cluster_recommendation,
        "reason": reason,
        "pairwise_similarities": upper_triangle
    }


def should_cluster(embeddings: Dict[str, np.ndarray], min_books: int = 3) -> Dict:
    """
    Clustering gate: Decide whether to cluster based on entropy.
    
    Args:
        embeddings: Book embeddings
        min_books: Minimum books required for clustering
    
    Returns:
        Decision dict with recommendation
    """
    n_books = len(embeddings)
    
    # Too few books?
    if n_books < min_books:
        return {
            "should_cluster": False,
            "reason": f"Too few books ({n_books} < {min_books})",
            "recommendation": "single_cluster",
            "entropy_analysis": None
        }
    
    # Compute entropy
    entropy_analysis = compute_dataset_entropy(embeddings)
    
    if entropy_analysis["entropy"] == "undefined":
        return {
            "should_cluster": False,
            "reason": entropy_analysis["reason"],
            "recommendation": "single_cluster",
            "entropy_analysis": None
        }
    
    # Clustering gate decision
    should_cluster_flag = entropy_analysis["cluster_recommendation"] != "single_cluster"
    
    return {
        "should_cluster": should_cluster_flag,
        "reason": entropy_analysis["reason"],
        "recommendation": entropy_analysis["cluster_recommendation"],
        "entropy_analysis": entropy_analysis
    }


def clustering_gate_report(embeddings: Dict[str, np.ndarray]) -> str:
    """
    Generate human-readable clustering gate report.
    
    Args:
        embeddings: Book embeddings
    
    Returns:
        Report string
    """
    decision = should_cluster(embeddings)
    
    lines = []
    lines.append("=" * 70)
    lines.append("🚪 CLUSTERING GATE")
    lines.append("=" * 70)
    
    if decision["should_cluster"]:
        lines.append("✅ GATE OPEN: Clustering recommended")
    else:
        lines.append("🚫 GATE CLOSED: Clustering not recommended")
    
    lines.append(f"\nReason: {decision['reason']}")
    lines.append(f"Recommendation: {decision['recommendation']}")
    
    if decision.get("entropy_analysis"):
        ent = decision["entropy_analysis"]
        lines.append(f"\nEntropy Level: {ent['entropy'].upper()}")
        lines.append(f"Avg Similarity: {ent['avg_similarity']:.2%}")
        lines.append(f"Std Similarity: {ent['std_similarity']:.2%}")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


# Test
if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python clustering_gate.py <discipline_id>")
        sys.exit(1)
    
    discipline_id = sys.argv[1]
    library_root = Path(__file__).parent.parent.parent / "books"
    discipline_path = library_root / discipline_id
    
    index_path = discipline_path / ".discipline-index.json"
    
    if not index_path.exists():
        print(f"❌ Index not found: {index_path}")
        sys.exit(1)
    
    with open(index_path, 'r') as f:
        index = json.load(f)
    
    embeddings = {k: np.array(v) for k, v in index.get("embeddings", {}).items()}
    
    # Run clustering gate
    decision = should_cluster(embeddings)
    
    # Print report
    print(clustering_gate_report(embeddings))
    
    # Exit code
    sys.exit(0 if decision["should_cluster"] else 1)
