#!/usr/bin/env python3
"""
Cluster Selection Logic — v3 MVP

Selects relevant clusters based on query + conversation context.
Works with mocked clusters (HDBSCAN integration comes later).
"""
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

# Load embedding model (same as indexer)
MODEL_NAME = "BAAI/bge-small-en-v1.5"
embed_model = None  # Lazy load


def get_embed_model():
    """Lazy load embedding model (shared across calls)."""
    global embed_model
    if embed_model is None:
        embed_model = SentenceTransformer(MODEL_NAME)
    return embed_model


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def build_query_embedding(query: str, history: List[str] = None) -> np.ndarray:
    """
    Build query embedding from query + conversation context.
    
    Splits query and context into separate embeddings, then blends:
    - 70% query (preserves intent)
    - 30% context (adds nuance)
    
    Context uses decay weights (recent messages matter more).
    
    This prevents:
    - Context from diluting the core query
    - Old conversation topics from polluting new queries
    
    Args:
        query: User query
        history: List of recent messages (last 3-5)
    
    Returns:
        Query embedding (384-dim)
    """
    model = get_embed_model()
    
    # Query embedding (primary signal)
    query_emb = model.encode(query, convert_to_numpy=True)
    
    if history and len(history) > 0:
        # CONTEXT DECAY: recent messages matter more
        # weights: [0.5, 0.3, 0.2] for [msg-1, msg-2, msg-3]
        recent_history = history[-3:]  # Last 3 messages
        weights = [0.5, 0.3, 0.2][:len(recent_history)]  # Decay weights
        weights = weights[::-1]  # Reverse (oldest → newest)
        
        # Weighted context embedding
        context_embs = []
        for msg, weight in zip(recent_history, weights):
            msg_emb = model.encode(msg, convert_to_numpy=True)
            context_embs.append(weight * msg_emb)
        
        context_emb = np.sum(context_embs, axis=0)
        
        # Normalize context embedding
        context_emb = context_emb / np.linalg.norm(context_emb)
        
        # Blend: 70% query + 30% context
        final_emb = 0.7 * query_emb + 0.3 * context_emb
        return final_emb
    else:
        # No context: pure query
        return query_emb


def score_clusters(query_emb: np.ndarray, clusters: List[Dict]) -> List[Dict]:
    """
    Score clusters by similarity to query embedding.
    
    Penalizes large clusters (to prevent "generic" clusters from dominating).
    
    Args:
        query_emb: Query embedding (384-dim)
        clusters: List of cluster dicts with 'id' and 'centroid'
    
    Returns:
        List of scored clusters (sorted by adjusted score, descending)
    """
    results = []
    
    for cluster in clusters:
        centroid = np.array(cluster["centroid"])
        raw_score = cosine_similarity(query_emb, centroid)
        
        # PENALIZE LARGE CLUSTERS: prevents "misc" clusters from always winning
        cluster_size = len(cluster.get("book_ids", []))
        size_penalty = np.log(cluster_size + 1)  # log damping (gentle)
        adjusted_score = raw_score / size_penalty
        
        results.append({
            "cluster_id": cluster["id"],
            "name": cluster.get("name", cluster["id"]),
            "score": float(adjusted_score),
            "raw_score": float(raw_score),  # for debugging
            "size_penalty": float(size_penalty),
            "book_ids": cluster.get("book_ids", [])
        })
    
    return sorted(results, key=lambda x: x["score"], reverse=True)


def select_clusters(
    scored: List[Dict],
    top_k: int = 3,
    relative_threshold: float = 0.7,
    ambiguity_threshold: float = 0.05
) -> List[str]:
    """
    Select top-K clusters using RELATIVE threshold.
    
    Handles ambiguity: if top scores are very close, select both
    (don't force the system to guess).
    
    Args:
        scored: Scored clusters (from score_clusters)
        top_k: Maximum number of clusters to select
        relative_threshold: Fraction of top score (0-1, default: 0.7)
        ambiguity_threshold: Max score difference for ambiguity (default: 0.05)
    
    Returns:
        List of selected cluster IDs
    """
    if not scored:
        return []
    
    # Top score (best cluster)
    top_score = scored[0]["score"]
    
    if top_score <= 0:
        # No meaningful similarity
        return []
    
    # Select clusters >= (top_score * threshold)
    min_score = top_score * relative_threshold
    
    selected = []
    for i, cluster in enumerate(scored):
        if cluster["score"] < min_score:
            break  # Already sorted, stop early
        
        selected.append(cluster["cluster_id"])
        
        # AMBIGUITY DETECTION: if next cluster is very close, include it too
        if i + 1 < len(scored) and len(selected) < top_k:
            next_score = scored[i + 1]["score"]
            score_diff = cluster["score"] - next_score
            
            if score_diff < ambiguity_threshold:
                # Too close to call — include next cluster
                continue  # Don't break, check next iteration
        
        if len(selected) >= top_k:
            break
    
    return selected


def get_clusters_for_discipline(discipline: str) -> List[Dict]:
    """
    Load clusters for a discipline.
    
    TODO: Replace with real cluster data from .discipline-index.json
    For now, returns mocked clusters for testing.
    
    Args:
        discipline: Discipline ID (e.g., "management_knowledge")
    
    Returns:
        List of cluster dicts
    """
    # MOCKED DATA (replace with real cluster loading later)
    # This simulates 3 clusters in management_knowledge
    
    if discipline == "management_knowledge":
        return [
            {
                "id": "taxonomies-classification",
                "name": "Taxonomies & Classification Systems",
                "centroid": get_embed_model().encode(
                    "taxonomy classification hierarchical faceted organization systems",
                    convert_to_numpy=True
                ),
                "book_ids": ["the_organization_of_information", "introduction_to_knowledge_organization"]
            },
            {
                "id": "information-retrieval",
                "name": "Information Retrieval & Search",
                "centroid": get_embed_model().encode(
                    "search retrieval indexing ranking query semantic similarity",
                    convert_to_numpy=True
                ),
                "book_ids": ["introduction_to_information_retrieval"]
            },
            {
                "id": "knowledge-management",
                "name": "Knowledge Management & Innovation",
                "centroid": get_embed_model().encode(
                    "knowledge management innovation networks organizational learning",
                    convert_to_numpy=True
                ),
                "book_ids": ["knowledge_management_and_innovation_in_networks", "knowledge_mapping_and_management"]
            }
        ]
    
    # Fallback: return empty (will trigger global search)
    return []


def cluster_aware_search(
    query: str,
    discipline: str,
    history: List[str] = None,
    top_k: int = 3,
    relative_threshold: float = 0.7
) -> Dict:
    """
    Main entry point: select clusters, then return filter for search.
    
    Now includes DYNAMIC CLUSTER ATTRIBUTION (DCA):
    - Explains WHY each cluster was selected
    - Provides reasoning for epistemic routing
    
    Args:
        query: User query
        discipline: Discipline ID
        history: Conversation context
        top_k: Max clusters to select
        relative_threshold: Fraction of top score (adaptive, default: 0.7)
    
    Returns:
        Dict with selected_clusters, metadata, AND attribution reasons
    """
    # 1. Build query embedding (with context)
    query_emb = build_query_embedding(query, history)
    
    # 2. Load clusters for discipline
    clusters = get_clusters_for_discipline(discipline)
    
    if not clusters:
        # No clusters → fallback to global search
        return {
            "selected_clusters": [],
            "fallback": "global",
            "reason": "no_clusters_found",
            "attribution": None
        }
    
    # 3. Score clusters
    scored = score_clusters(query_emb, clusters)
    
    # 4. Select top-K using relative threshold
    selected_ids = select_clusters(
        scored,
        top_k=top_k,
        relative_threshold=relative_threshold
    )
    
    if not selected_ids:
        # INTELLIGENT FALLBACK: use top-1 cluster anyway (better than nothing)
        # This prevents ignoring cluster layer when scores are low
        if scored and scored[0]["score"] > 0.1:  # Minimum sanity check
            selected_ids = [scored[0]["cluster_id"]]
            fallback_reason = "low_scores_forced_top1"
        else:
            # True fallback: global search
            return {
                "selected_clusters": [],
                "fallback": "global",
                "reason": "below_threshold",
                "top_score": scored[0]["score"] if scored else 0,
                "attribution": None
            }
    
    # 5. Return selected clusters + metadata + ATTRIBUTION
    selected_metadata = [c for c in scored if c["cluster_id"] in selected_ids]
    
    # BUILD ATTRIBUTION (why these clusters?)
    attribution = build_attribution(
        query=query,
        history=history,
        selected_clusters=selected_metadata,
        all_clusters=scored
    )
    
    return {
        "selected_clusters": selected_ids,
        "metadata": selected_metadata,
        "fallback": fallback_reason if 'fallback_reason' in locals() else None,
        "attribution": attribution  # NEW: DCA
    }


def build_attribution(
    query: str,
    history: List[str],
    selected_clusters: List[Dict],
    all_clusters: List[Dict]
) -> Dict:
    """
    Build Dynamic Cluster Attribution (DCA).
    
    Explains WHY these clusters were selected:
    - Keyword overlap
    - Context continuity
    - Semantic similarity
    - Relative ranking
    
    Args:
        query: User query
        history: Conversation context
        selected_clusters: Clusters that were selected
        all_clusters: All scored clusters
    
    Returns:
        Attribution dict with reasons
    """
    if not selected_clusters:
        return None
    
    # Primary cluster (top-1)
    primary = selected_clusters[0]
    
    # Build reasons
    reasons = []
    
    # 1. Semantic similarity score
    score = primary["score"]
    if score > 0.8:
        reasons.append(f"Very high semantic match (score: {score:.2f})")
    elif score > 0.6:
        reasons.append(f"High semantic match (score: {score:.2f})")
    elif score > 0.4:
        reasons.append(f"Moderate semantic match (score: {score:.2f})")
    else:
        reasons.append(f"Low semantic match (score: {score:.2f}) — forced selection")
    
    # 2. Keyword overlap (simple heuristic for MVP)
    cluster_name = primary.get("name", "")
    query_lower = query.lower()
    name_tokens = set(cluster_name.lower().split())
    query_tokens = set(query_lower.split())
    overlap = name_tokens & query_tokens
    
    if overlap:
        reasons.append(f"Keyword overlap: {', '.join(sorted(overlap))}")
    
    # 3. Context continuity (if history used)
    if history and len(history) > 0:
        # Check if context contributed (weighted embedding)
        # For now, just flag that context was used
        reasons.append("Context from conversation influenced selection")
    
    # 4. Relative ranking
    rank = 1  # Primary cluster is always rank 1
    if len(all_clusters) > 1:
        second_score = all_clusters[1]["score"]
        score_diff = score - second_score
        
        if score_diff < 0.05:
            reasons.append(f"Ambiguous: very close to next cluster (diff: {score_diff:.3f})")
        elif score_diff > 0.3:
            reasons.append(f"Clear winner: significantly ahead of next cluster (diff: {score_diff:.2f})")
    
    # 5. Multi-cluster attribution (if multiple selected)
    secondary_clusters = None
    if len(selected_clusters) > 1:
        secondary_clusters = [
            {
                "name": c.get("name", c["cluster_id"]),
                "score": c["score"],
                "weight": c["score"] / sum(sc["score"] for sc in selected_clusters)
            }
            for c in selected_clusters[1:]
        ]
    
    # Build attribution object
    attribution = {
        "primary_cluster": {
            "id": primary["cluster_id"],
            "name": primary.get("name", primary["cluster_id"]),
            "score": primary["score"]
        },
        "reasons": reasons,
        "secondary_clusters": secondary_clusters,
        "total_clusters_considered": len(all_clusters)
    }
    
    return attribution


# Test/demo
if __name__ == "__main__":
    # Example: query with context
    query = "How do taxonomies differ from folksonomies"
    history = [
        "We're discussing knowledge organization systems",
        "I'm interested in bottom-up versus top-down approaches"
    ]
    
    result = cluster_aware_search(
        query=query,
        discipline="management_knowledge",
        history=history,
        top_k=2,
        relative_threshold=0.7
    )
    
    print("\n🎯 Cluster Selection Result:\n")
    print(f"Query: {query}")
    print(f"Context: {history}\n")
    
    if result["fallback"]:
        print(f"⚠️  Fallback: {result['fallback']} ({result.get('reason', 'unknown')})")
    else:
        print(f"✅ Selected {len(result['selected_clusters'])} clusters:\n")
        
        # Show attribution
        attribution = result.get("attribution")
        if attribution:
            print(f"📚 Primary Cluster: {attribution['primary_cluster']['name']}")
            print(f"   Score: {attribution['primary_cluster']['score']:.3f}\n")
            
            print("💡 Reasons:")
            for reason in attribution["reasons"]:
                print(f"   • {reason}")
            
            if attribution.get("secondary_clusters"):
                print("\n📖 Secondary Clusters:")
                for sec in attribution["secondary_clusters"]:
                    print(f"   • {sec['name']} (weight: {sec['weight']:.0%})")
