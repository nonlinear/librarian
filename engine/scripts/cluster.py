#!/usr/bin/env python3
"""
Librarian Clustering v3 — HDBSCAN

Auto-generates clusters from book embeddings using HDBSCAN.
Runs after indexer.py has generated book-level embeddings.

Usage:
    python cluster.py --all              # Cluster all disciplines
    python cluster.py --discipline name  # Cluster one discipline
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict
import numpy as np

try:
    import hdbscan
    HAS_HDBSCAN = True
except ImportError:
    print("⚠️  hdbscan not installed. Install with: pip install hdbscan")
    HAS_HDBSCAN = False

# Paths
LIBRARY_ROOT = Path(__file__).parent.parent.parent / "books"

# Import clustering gate
sys.path.insert(0, str(Path(__file__).parent))
from clustering_gate import should_cluster, clustering_gate_report


def load_discipline_index(discipline_path: Path) -> Dict:
    """Load .discipline-index.json."""
    index_path = discipline_path / ".discipline-index.json"
    
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found: {index_path}. Run indexer.py first.")
    
    with open(index_path, 'r') as f:
        return json.load(f)


def cluster_books_hdbscan(
    embeddings: Dict[str, List[float]],
    min_cluster_size: int = 3,
    min_samples: int = 2
) -> Dict[str, int]:
    """
    Cluster books using HDBSCAN.
    
    Args:
        embeddings: Dict of book_id → embedding (list of floats)
        min_cluster_size: Minimum cluster size
        min_samples: Minimum samples per cluster
    
    Returns:
        Dict of book_id → cluster_id (int, -1 = noise)
    """
    if not HAS_HDBSCAN:
        raise ImportError("hdbscan not installed")
    
    # Convert embeddings dict → matrix
    book_ids = list(embeddings.keys())
    embedding_matrix = np.array([embeddings[bid] for bid in book_ids])
    
    # Run HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',  # or 'cosine' after normalization
        cluster_selection_method='eom'
    )
    
    cluster_labels = clusterer.fit_predict(embedding_matrix)
    
    # Map book_id → cluster_id
    assignments = {}
    for i, book_id in enumerate(book_ids):
        assignments[book_id] = int(cluster_labels[i])
    
    return assignments


def generate_cluster_metadata(
    cluster_id: int,
    book_ids: List[str],
    books_metadata: List[Dict],
    embeddings: Dict[str, List[float]]
) -> Dict:
    """
    Generate cluster metadata (name, centroid, keywords).
    
    Args:
        cluster_id: Cluster ID (int)
        book_ids: List of book IDs in cluster
        books_metadata: List of all books (from .discipline-index.json)
        embeddings: Dict of book_id → embedding
    
    Returns:
        Cluster metadata dict
    """
    # Centroid = mean of book embeddings in cluster
    cluster_embeddings = [embeddings[bid] for bid in book_ids]
    centroid = np.mean(cluster_embeddings, axis=0).tolist()
    
    # STABLE CLUSTER ID: hash of sorted book IDs
    # This prevents ID drift when HDBSCAN reruns
    import hashlib
    stable_id = hashlib.md5(
        ",".join(sorted(book_ids)).encode()
    ).hexdigest()[:8]
    
    # Name = first 3 book titles (simple for now, LLM naming later)
    book_titles = []
    for book in books_metadata:
        if book['id'] in book_ids:
            book_titles.append(book['title'])
    
    cluster_name = " + ".join(book_titles[:3])
    if len(book_titles) > 3:
        cluster_name += f" (+{len(book_titles)-3} more)"
    
    return {
        "id": f"cluster-{stable_id}",  # Stable hash-based ID
        "hdbscan_label": cluster_id,     # Original HDBSCAN label (for debugging)
        "name": cluster_name,
        "centroid": centroid,
        "book_ids": sorted(book_ids),   # Sorted for determinism
        "size": len(book_ids),
        "keywords": []  # TODO: TF-IDF or LLM-generated
    }


def cluster_discipline(discipline_id: str, discipline_path: Path):
    """
    Cluster books in a discipline.
    
    Uses clustering gate to decide if clustering is appropriate.
    
    Args:
        discipline_id: Discipline ID
        discipline_path: Path to discipline folder
    """
    print(f"\n🧩 Clustering discipline: {discipline_id}")
    
    # 1. Load index
    index = load_discipline_index(discipline_path)
    
    embeddings = index.get('embeddings', {})
    books = index.get('books', [])
    
    if not embeddings:
        print("   ⚠️  No embeddings found. Run indexer.py first.")
        return
    
    print(f"   Books: {len(embeddings)}")
    
    # 2. Clustering gate (entropy check)
    embeddings_np = {k: np.array(v) for k, v in embeddings.items()}
    gate_decision = should_cluster(embeddings_np)
    
    print(f"\n{clustering_gate_report(embeddings_np)}\n")
    
    # 3. Cluster based on gate decision
    if not gate_decision["should_cluster"]:
        print("   🚫 CLUSTERING BLOCKED (low entropy)")
        print("   ➡️  Using single cluster mode\n")
        # Single cluster (all books together)
        assignments = {bid: 0 for bid in embeddings.keys()}
    else:
        print("   ✅ CLUSTERING ALLOWED (sufficient entropy)\n")
        # Adjust min_cluster_size for dataset size
        min_size = max(2, len(embeddings) // 3)
        if len(embeddings) <= 5:
            min_size = 2
        
        assignments = cluster_books_hdbscan(
            embeddings,
            min_cluster_size=min_size,
            min_samples=1  # Relaxed for small datasets
        )
    
    # 3. Group by cluster
    clusters_dict = {}
    for book_id, cluster_id in assignments.items():
        if cluster_id not in clusters_dict:
            clusters_dict[cluster_id] = []
        clusters_dict[cluster_id].append(book_id)
    
    print(f"   Clusters found: {len(clusters_dict)}")
    
    # 4. Generate cluster metadata
    clusters = []
    for cluster_id, book_ids in clusters_dict.items():
        if cluster_id == -1:
            # Noise (unclustered books)
            print(f"   • Noise: {len(book_ids)} books (unclustered)")
            continue
        
        meta = generate_cluster_metadata(cluster_id, book_ids, books, embeddings)
        clusters.append(meta)
        print(f"   • {meta['name'][:60]}... ({meta['size']} books)")
    
    # 5. Update discipline index
    import time
    index['clusters'] = clusters
    index['last_clustered'] = time.time()
    
    index_path = discipline_path / ".discipline-index.json"
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"   ✅ Updated: {index_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Librarian Clustering v3")
    parser.add_argument('--all', action='store_true', help="Cluster all disciplines")
    parser.add_argument('--discipline', type=str, help="Cluster one discipline")
    
    args = parser.parse_args()
    
    if not HAS_HDBSCAN:
        print("❌ hdbscan not installed")
        print("   Install with: pip install hdbscan")
        return 1
    
    if args.all:
        print("\n🚀 Clustering all disciplines...")
        
        # Find all disciplines with .discipline-index.json
        disciplines = []
        for item in LIBRARY_ROOT.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                index_path = item / ".discipline-index.json"
                if index_path.exists():
                    disciplines.append((item.name, item))
        
        print(f"Found {len(disciplines)} disciplines with indexes")
        
        for discipline_id, discipline_path in disciplines:
            cluster_discipline(discipline_id, discipline_path)
    
    elif args.discipline:
        discipline_path = LIBRARY_ROOT / args.discipline
        
        if not discipline_path.exists():
            print(f"❌ Discipline not found: {discipline_path}")
            return 1
        
        cluster_discipline(args.discipline, discipline_path)
    
    else:
        print("❌ Use --all or --discipline <name>")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
