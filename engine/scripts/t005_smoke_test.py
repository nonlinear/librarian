#!/usr/bin/env python3
"""
T005: FAISS Smoke Test (Simplified)
Tests FAISS search quality without JSON comparison (avoids OOM)

Validates:
- Query coverage across categories
- Score distribution sanity
- Result relevance (manual spot-check)
- No catastrophic failures

Usage:
    python t005_smoke_test.py
"""
import json
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from faiss_search import FAISSSearch

# Test query categories
TEST_QUERIES = {
    "factual": [
        "herbalism tinctures preparation",
        "machine learning neural networks",
        "tarot card meanings major arcana",
        "quantum mechanics wave function",
        "design thinking process steps",
        "chaos magick sigil creation",
        "meditation techniques mindfulness",
        "astrology planetary aspects",
        "permaculture principles design"
    ],
    "ambiguous": [
        "chaos",
        "ritual",
        "design",
        "energy",
        "power",
        "transformation",
        "balance",
        "flow"
    ],
    "long_tail": [
        "animism and plant communication",
        "retrograde mercury interpretation",
        "kundalini awakening symptoms",
        "hermetic principles correspondence",
        "manifestation scripting techniques",
        "shadow work integration process",
        "elemental magick invocation"
    ],
    "adversarial": [
        "machne lerning",  # misspelling
        "quantum",  # partial
        "design thinking innovation creativity",  # multi-intent
        "meditation yoga breathwork mindfulness",  # keyword stuffing
        "what is the meaning of life"  # philosophical
    ]
}


def run_smoke_test():
    """
    Run FAISS smoke test across query categories
    """
    print("🔧 Initializing FAISS smoke test...")
    
    # Load FAISS
    faiss = FAISSSearch("/app/books/faiss.index", "/app/books/metadata.json")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    print("✅ FAISS loaded\n")
    
    results_by_category = {}
    all_scores = []
    failures = []
    
    for category, queries in TEST_QUERIES.items():
        print(f"\n{'='*60}")
        print(f"📁 Category: {category.upper()}")
        print('='*60)
        
        category_scores = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Query: {query}")
            
            # Search
            results = faiss.search_text(query, model, k=5)
            
            if not results:
                print("   ❌ No results!")
                failures.append({"query": query, "category": category})
                continue
            
            # Extract scores
            scores = [r["score"] for r in results]
            top_score = scores[0]
            category_scores.extend(scores)
            all_scores.extend(scores)
            
            # Show top result
            top_result = results[0]
            print(f"   ✓ Top result: {top_result['book_title']} [{top_score:.3f}]")
            print(f"     Text: {top_result['text'][:80]}...")
            
            # Quality check
            if top_score < 0.4:
                print(f"   ⚠️  Low confidence (score < 0.4)")
            
            # Show score distribution
            print(f"   Scores: {[f'{s:.3f}' for s in scores[:3]]}")
        
        # Category stats
        if category_scores:
            avg_score = np.mean(category_scores)
            min_score = np.min(category_scores)
            max_score = np.max(category_scores)
            
            print(f"\n📊 {category.upper()} Summary:")
            print(f"   Average score: {avg_score:.3f}")
            print(f"   Range: [{min_score:.3f}, {max_score:.3f}]")
            
            results_by_category[category] = {
                "avg_score": avg_score,
                "min_score": min_score,
                "max_score": max_score,
                "query_count": len(queries)
            }
    
    # Overall summary
    print("\n" + "="*60)
    print("📊 OVERALL SUMMARY")
    print("="*60)
    
    total_queries = sum(len(qs) for qs in TEST_QUERIES.values())
    avg_score = np.mean(all_scores) if all_scores else 0
    
    print(f"Total queries: {total_queries}")
    print(f"Average score: {avg_score:.3f}")
    print(f"Score range: [{np.min(all_scores):.3f}, {np.max(all_scores):.3f}]")
    print(f"Failures (no results): {len(failures)}")
    
    # Status
    if avg_score >= 0.7 and len(failures) == 0:
        status = "🟢 PASS (high confidence)"
    elif avg_score >= 0.5 and len(failures) <= 2:
        status = "🟡 ACCEPTABLE (moderate confidence)"
    else:
        status = "🔴 FAIL (low confidence or too many failures)"
    
    print(f"\nStatus: {status}\n")
    
    # Category breakdown
    print("📋 By Category:")
    for cat, stats in results_by_category.items():
        print(f"   {cat:15s}: {stats['avg_score']:.3f} avg")
    
    # Save report
    report = {
        "status": status,
        "avg_score": avg_score,
        "total_queries": total_queries,
        "failures": failures,
        "by_category": results_by_category
    }
    
    with open("/app/books/t005_smoke_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n📄 Report saved to: /app/books/t005_smoke_report.json")
    
    return "PASS" in status


if __name__ == "__main__":
    import sys
    
    success = run_smoke_test()
    sys.exit(0 if success else 1)
