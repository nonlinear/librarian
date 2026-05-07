#!/usr/bin/env python3
"""
Cluster Integrity Check — Cross-Boundary Leakage Detection

Tests whether cluster boundaries are meaningful or arbitrary.

Checks:
1. Cross-cluster similarity (are books in one cluster too similar to another?)
2. Centroid separation (are cluster centroids sufficiently distant?)
3. Intra-cluster cohesion (are books within cluster actually similar?)

Usage:
    python cluster_integrity.py --discipline <discipline_id>
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict
import numpy as np

# Paths
LIBRARY_ROOT = Path(__file__).parent.parent.parent / "books"


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def load_discipline_index(discipline_path: Path) -> Dict:
    """Load .discipline-index.json."""
    index_path = discipline_path / ".discipline-index.json"
    
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found: {index_path}")
    
    with open(index_path, 'r') as f:
        return json.load(f)


def check_cross_cluster_leakage(index: Dict) -> Dict:
    """
    Check if books strongly belong to multiple clusters (boundary leakage).
    
    For each book in a cluster, compute similarity to OTHER cluster centroids.
    High cross-cluster similarity = weak boundaries.
    
    Args:
        index: Discipline index dict
    
    Returns:
        Leakage analysis dict
    """
    clusters = index.get("clusters", [])
    embeddings = index.get("embeddings", {})
    
    if not clusters or len(clusters) < 2:
        return {
            "status": "skip",
            "reason": "Need at least 2 clusters for leakage check"
        }
    
    # Build cluster centroids lookup
    cluster_centroids = {
        c["id"]: np.array(c["centroid"])
        for c in clusters
    }
    
    # For each book, compute similarity to all cluster centroids
    leakage_scores = []
    
    for cluster in clusters:
        cluster_id = cluster["id"]
        cluster_centroid = cluster_centroids[cluster_id]
        
        for book_id in cluster["book_ids"]:
            book_emb = np.array(embeddings.get(book_id, []))
            
            if len(book_emb) == 0:
                continue
            
            # Similarity to own cluster
            own_similarity = cosine_similarity(book_emb, cluster_centroid)
            
            # Similarity to OTHER clusters
            cross_similarities = []
            for other_cluster_id, other_centroid in cluster_centroids.items():
                if other_cluster_id == cluster_id:
                    continue
                cross_sim = cosine_similarity(book_emb, other_centroid)
                cross_similarities.append(cross_sim)
            
            max_cross_sim = max(cross_similarities) if cross_similarities else 0
            
            # Leakage = how close book is to OTHER clusters
            leakage = max_cross_sim / own_similarity if own_similarity > 0 else 0
            
            leakage_scores.append({
                "book_id": book_id,
                "cluster_id": cluster_id,
                "own_similarity": own_similarity,
                "max_cross_similarity": max_cross_sim,
                "leakage_ratio": leakage
            })
    
    # Aggregate stats
    avg_leakage = np.mean([s["leakage_ratio"] for s in leakage_scores])
    max_leakage = max([s["leakage_ratio"] for s in leakage_scores])
    
    # Threshold: leakage > 0.75 is bad (book almost equally belongs to another cluster)
    high_leakage_count = sum(1 for s in leakage_scores if s["leakage_ratio"] > 0.75)
    
    return {
        "status": "pass" if avg_leakage < 0.75 else "fail",
        "avg_leakage": avg_leakage,
        "max_leakage": max_leakage,
        "high_leakage_count": high_leakage_count,
        "total_books": len(leakage_scores),
        "leakage_scores": sorted(leakage_scores, key=lambda x: x["leakage_ratio"], reverse=True)[:5]  # Top 5 worst
    }


def check_centroid_separation(index: Dict) -> Dict:
    """
    Check if cluster centroids are sufficiently separated.
    
    Low separation = arbitrary boundaries (clusters too similar).
    
    Args:
        index: Discipline index dict
    
    Returns:
        Separation analysis dict
    """
    clusters = index.get("clusters", [])
    
    if not clusters or len(clusters) < 2:
        return {
            "status": "skip",
            "reason": "Need at least 2 clusters"
        }
    
    # Compute pairwise centroid distances
    centroids = [np.array(c["centroid"]) for c in clusters]
    
    distances = []
    for i in range(len(centroids)):
        for j in range(i + 1, len(centroids)):
            sim = cosine_similarity(centroids[i], centroids[j])
            distances.append({
                "cluster_1": clusters[i]["id"],
                "cluster_2": clusters[j]["id"],
                "similarity": sim,
                "distance": 1 - sim  # Convert to distance
            })
    
    avg_distance = np.mean([d["distance"] for d in distances])
    min_distance = min([d["distance"] for d in distances])
    
    # Threshold: distance < 0.2 is bad (centroids too close)
    return {
        "status": "pass" if min_distance > 0.2 else "fail",
        "avg_distance": avg_distance,
        "min_distance": min_distance,
        "pairwise_distances": distances
    }


def check_intra_cluster_cohesion(index: Dict) -> Dict:
    """
    Check if books within each cluster are actually similar.
    
    Low cohesion = cluster is incoherent.
    
    Args:
        index: Discipline index dict
    
    Returns:
        Cohesion analysis dict
    """
    clusters = index.get("clusters", [])
    embeddings = index.get("embeddings", {})
    
    if not clusters:
        return {
            "status": "skip",
            "reason": "No clusters found"
        }
    
    cohesion_scores = []
    
    for cluster in clusters:
        cluster_id = cluster["id"]
        book_ids = cluster["book_ids"]
        
        if len(book_ids) < 2:
            continue  # Can't measure cohesion with 1 book
        
        # Get embeddings for books in cluster
        cluster_embs = [np.array(embeddings[bid]) for bid in book_ids if bid in embeddings]
        
        # Compute pairwise similarities
        similarities = []
        for i in range(len(cluster_embs)):
            for j in range(i + 1, len(cluster_embs)):
                sim = cosine_similarity(cluster_embs[i], cluster_embs[j])
                similarities.append(sim)
        
        avg_cohesion = np.mean(similarities) if similarities else 0
        
        cohesion_scores.append({
            "cluster_id": cluster_id,
            "cohesion": avg_cohesion,
            "book_count": len(book_ids)
        })
    
    avg_cohesion = np.mean([c["cohesion"] for c in cohesion_scores]) if cohesion_scores else 0
    
    # Threshold: cohesion < 0.5 is bad (books not similar)
    return {
        "status": "pass" if avg_cohesion > 0.5 else "warn",
        "avg_cohesion": avg_cohesion,
        "cluster_cohesion": cohesion_scores
    }


def analyze_cluster_integrity(discipline_id: str, discipline_path: Path) -> Dict:
    """
    Run full cluster integrity analysis.
    
    Args:
        discipline_id: Discipline ID
        discipline_path: Path to discipline folder
    
    Returns:
        Full integrity report
    """
    print(f"\n🔍 Analyzing cluster integrity: {discipline_id}")
    print("─" * 70)
    
    # Load index
    index = load_discipline_index(discipline_path)
    
    # Run checks
    leakage_check = check_cross_cluster_leakage(index)
    separation_check = check_centroid_separation(index)
    cohesion_check = check_intra_cluster_cohesion(index)
    
    # Overall status
    statuses = [
        leakage_check.get("status"),
        separation_check.get("status"),
        cohesion_check.get("status")
    ]
    
    if "fail" in statuses:
        overall_status = "fail"
    elif "warn" in statuses:
        overall_status = "warn"
    elif "skip" in statuses:
        overall_status = "skip"
    else:
        overall_status = "pass"
    
    return {
        "discipline_id": discipline_id,
        "status": overall_status,
        "checks": {
            "leakage": leakage_check,
            "separation": separation_check,
            "cohesion": cohesion_check
        }
    }


def print_report(report: Dict):
    """Print human-readable integrity report."""
    print(f"\n{'='*70}")
    print(f"🔬 CLUSTER INTEGRITY REPORT: {report['discipline_id']}")
    print(f"{'='*70}\n")
    
    status_emoji = {
        "pass": "✅",
        "warn": "⚠️ ",
        "fail": "❌",
        "skip": "⏭️ "
    }
    
    print(f"{status_emoji.get(report['status'], '❓')} Overall Status: {report['status'].upper()}\n")
    
    # Leakage check
    leakage = report["checks"]["leakage"]
    print("─" * 70)
    print("CHECK 1: Cross-Boundary Leakage")
    print(f"  Status: {status_emoji.get(leakage['status'])} {leakage['status'].upper()}")
    
    if leakage["status"] != "skip":
        print(f"  Avg Leakage: {leakage['avg_leakage']:.2%}")
        print(f"  Max Leakage: {leakage['max_leakage']:.2%}")
        print(f"  High Leakage Count: {leakage['high_leakage_count']}/{leakage['total_books']}")
        
        if leakage.get("leakage_scores"):
            print("\n  Worst Offenders:")
            for score in leakage["leakage_scores"][:3]:
                print(f"    • {score['book_id']}: {score['leakage_ratio']:.2%} leakage")
    else:
        print(f"  Reason: {leakage.get('reason')}")
    
    # Separation check
    separation = report["checks"]["separation"]
    print("\n" + "─" * 70)
    print("CHECK 2: Centroid Separation")
    print(f"  Status: {status_emoji.get(separation['status'])} {separation['status'].upper()}")
    
    if separation["status"] != "skip":
        print(f"  Avg Distance: {separation['avg_distance']:.3f}")
        print(f"  Min Distance: {separation['min_distance']:.3f}")
    else:
        print(f"  Reason: {separation.get('reason')}")
    
    # Cohesion check
    cohesion = report["checks"]["cohesion"]
    print("\n" + "─" * 70)
    print("CHECK 3: Intra-Cluster Cohesion")
    print(f"  Status: {status_emoji.get(cohesion['status'])} {cohesion['status'].upper()}")
    
    if cohesion["status"] != "skip":
        print(f"  Avg Cohesion: {cohesion['avg_cohesion']:.2%}")
        if cohesion.get("cluster_cohesion"):
            print("\n  Per-Cluster:")
            for c in cohesion["cluster_cohesion"]:
                print(f"    • {c['cluster_id']}: {c['cohesion']:.2%} ({c['book_count']} books)")
    else:
        print(f"  Reason: {cohesion.get('reason')}")
    
    print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cluster Integrity Check")
    parser.add_argument('--discipline', required=True, help="Discipline ID (e.g., management/knowledge)")
    parser.add_argument('--json', action='store_true', help="JSON output only")
    
    args = parser.parse_args()
    
    discipline_path = LIBRARY_ROOT / args.discipline
    
    if not discipline_path.exists():
        print(f"❌ Discipline not found: {discipline_path}")
        return 1
    
    # Run analysis
    report = analyze_cluster_integrity(args.discipline, discipline_path)
    
    # Print or output JSON
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    
    # Exit code
    if report["status"] == "fail":
        return 2
    elif report["status"] == "warn":
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
