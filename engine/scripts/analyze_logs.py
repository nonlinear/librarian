#!/usr/bin/env python3
"""
Librarian Health Checks — Anti-Drift Protocol

Analyzes query-log.jsonl to detect system degradation.

Checks:
1. Fallback rate (cluster layer ignored?)
2. Cluster concentration (one cluster dominates?)
3. Ambiguity rate (too many unclear queries?)
4. Cluster-chunk mismatch (routing vs retrieval failure?)
5. Score distributions (which layer is failing?)
6. Context impact (context helps or hurts?)
7. Empty result rate (total failure?)

Usage:
    python analyze_logs.py [--last N]
    
Output:
    - report.json (metrics + status)
    - Terminal summary (pass/warn/fail)
"""
import os
import json
from pathlib import Path
from typing import List, Dict
from collections import Counter
import statistics

# Paths
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "query-log.jsonl"
REPORT_FILE = LOG_DIR / "health-report.json"

# Thresholds
THRESHOLDS = {
    "fallback_rate": {"warn": 0.30, "fail": 0.50},
    "top_cluster_concentration": {"warn": 0.40, "fail": 0.60},
    "ambiguity_rate": {"warn": 0.40, "fail": None},  # High ambiguity is ok
    "mismatch_rate": {"warn": 0.20, "fail": 0.30},
    "empty_rate": {"warn": 0.05, "fail": 0.10},
    "avg_cluster_score": {"warn": 0.40, "fail": 0.30},  # Low is bad
    "avg_chunk_score": {"warn": 0.35, "fail": 0.25}   # Low is bad
}


def load_logs(limit: int = None) -> List[Dict]:
    """
    Load query logs from query-log.jsonl.
    
    Args:
        limit: Return only last N entries (None = all)
    
    Returns:
        List of log entry dicts
    """
    if not LOG_FILE.exists():
        return []
    
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    if limit:
        lines = lines[-limit:]
    
    logs = []
    for line in lines:
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    
    return logs


def check_fallback_rate(logs: List[Dict]) -> Dict:
    """
    CHECK 1: Fallback rate (cluster layer ignored?)
    
    High fallback rate → cluster layer not working
    """
    total = len(logs)
    fallbacks = sum(1 for log in logs if log.get("fallback"))
    
    rate = fallbacks / total if total > 0 else 0
    
    return {
        "fallback_rate": rate,
        "fallback_count": fallbacks,
        "total_queries": total,
        "status": _check_threshold(rate, THRESHOLDS["fallback_rate"])
    }


def check_cluster_concentration(logs: List[Dict]) -> Dict:
    """
    CHECK 2: Cluster concentration (one cluster dominates?)
    
    High concentration → generic cluster problem
    """
    cluster_usage = Counter()
    
    for log in logs:
        for cluster_id in log.get("selected_clusters", []):
            cluster_usage[cluster_id] += 1
    
    total = len(logs)
    if total == 0 or not cluster_usage:
        return {
            "top_cluster_concentration": 0,
            "top_cluster_id": None,
            "status": "pass"
        }
    
    top_cluster, top_count = cluster_usage.most_common(1)[0]
    concentration = top_count / total
    
    return {
        "top_cluster_concentration": concentration,
        "top_cluster_id": top_cluster,
        "top_cluster_count": top_count,
        "total_queries": total,
        "cluster_distribution": dict(cluster_usage.most_common(5)),
        "status": _check_threshold(concentration, THRESHOLDS["top_cluster_concentration"])
    }


def check_ambiguity_rate(logs: List[Dict]) -> Dict:
    """
    CHECK 3: Ambiguity rate (too many unclear queries?)
    
    Ambiguity = top 2 cluster scores very close (<0.05 diff)
    """
    total = len(logs)
    ambiguous = 0
    
    for log in logs:
        scores = log.get("top_cluster_scores", [])
        if len(scores) >= 2:
            score_diff = scores[0]["score"] - scores[1]["score"]
            if score_diff < 0.05:
                ambiguous += 1
    
    rate = ambiguous / total if total > 0 else 0
    
    return {
        "ambiguity_rate": rate,
        "ambiguous_count": ambiguous,
        "total_queries": total,
        "status": _check_threshold(rate, THRESHOLDS["ambiguity_rate"])
    }


def check_mismatch_rate(logs: List[Dict]) -> Dict:
    """
    CHECK 4: Cluster-chunk mismatch (routing correct, retrieval fails?)
    
    Mismatch = high cluster score + low chunk score
    """
    total = len(logs)
    mismatches = sum(1 for log in logs if log.get("cluster_chunk_mismatch", False))
    
    rate = mismatches / total if total > 0 else 0
    
    return {
        "mismatch_rate": rate,
        "mismatch_count": mismatches,
        "total_queries": total,
        "status": _check_threshold(rate, THRESHOLDS["mismatch_rate"])
    }


def check_score_distributions(logs: List[Dict]) -> Dict:
    """
    CHECK 5: Average cluster vs chunk scores (which layer is failing?)
    """
    cluster_scores = []
    chunk_scores = []
    
    for log in logs:
        # Top cluster score
        top_cluster = log.get("top_cluster_scores", [])
        if top_cluster:
            cluster_scores.append(top_cluster[0]["score"])
        
        # Top result score
        results = log.get("results", [])
        if results:
            chunk_scores.append(results[0]["similarity"])
    
    avg_cluster = statistics.mean(cluster_scores) if cluster_scores else 0
    avg_chunk = statistics.mean(chunk_scores) if chunk_scores else 0
    
    # Interpretation
    if avg_cluster > 0.6 and avg_chunk < 0.4:
        interpretation = "retrieval_problem"  # Cluster good, chunk bad
    elif avg_cluster < 0.4 and avg_chunk > 0.5:
        interpretation = "routing_problem"   # Cluster bad, chunk good
    elif avg_cluster < 0.4 and avg_chunk < 0.4:
        interpretation = "embedding_problem"  # Both bad
    else:
        interpretation = "healthy"
    
    return {
        "avg_cluster_score": avg_cluster,
        "avg_chunk_score": avg_chunk,
        "interpretation": interpretation,
        "cluster_status": _check_threshold(avg_cluster, THRESHOLDS["avg_cluster_score"], invert=True),
        "chunk_status": _check_threshold(avg_chunk, THRESHOLDS["avg_chunk_score"], invert=True)
    }


def check_empty_rate(logs: List[Dict]) -> Dict:
    """
    CHECK 7: Empty result rate (total failure?)
    """
    total = len(logs)
    empty = sum(1 for log in logs if log.get("results_count", 0) == 0)
    
    rate = empty / total if total > 0 else 0
    
    return {
        "empty_rate": rate,
        "empty_count": empty,
        "total_queries": total,
        "status": _check_threshold(rate, THRESHOLDS["empty_rate"])
    }


def _check_threshold(value: float, thresholds: Dict, invert: bool = False) -> str:
    """
    Check value against thresholds.
    
    Args:
        value: Metric value
        thresholds: Dict with 'warn' and 'fail' keys
        invert: If True, low values are bad (for scores)
    
    Returns:
        "pass", "warn", or "fail"
    """
    if invert:
        # For scores: low is bad
        if thresholds.get("fail") and value < thresholds["fail"]:
            return "fail"
        elif thresholds.get("warn") and value < thresholds["warn"]:
            return "warn"
        else:
            return "pass"
    else:
        # For rates: high is bad
        if thresholds.get("fail") and value > thresholds["fail"]:
            return "fail"
        elif thresholds.get("warn") and value > thresholds["warn"]:
            return "warn"
        else:
            return "pass"


def compute_overall_status(checks: Dict) -> str:
    """
    Compute overall system status from individual checks.
    
    Returns:
        "healthy", "degraded", "skewed", or "broken"
    """
    # Count statuses
    statuses = []
    for check_name, check_result in checks.items():
        if isinstance(check_result, dict):
            status = check_result.get("status")
            if status:
                statuses.append(status)
    
    # Decision logic
    if "fail" in statuses:
        # Check specific failure types
        if checks["fallback"]["status"] == "fail":
            return "broken"
        elif checks["cluster_concentration"]["status"] == "fail":
            return "skewed"
        elif checks["mismatch"]["status"] == "fail":
            return "degraded"
        else:
            return "degraded"
    elif "warn" in statuses:
        return "degraded"
    else:
        return "healthy"


def analyze(limit: int = None) -> Dict:
    """
    Run all health checks.
    
    Args:
        limit: Analyze only last N queries (None = all)
    
    Returns:
        Report dict
    """
    logs = load_logs(limit=limit)
    
    if not logs:
        return {
            "error": "No logs found",
            "log_file": str(LOG_FILE)
        }
    
    # Run checks
    checks = {
        "fallback": check_fallback_rate(logs),
        "cluster_concentration": check_cluster_concentration(logs),
        "ambiguity": check_ambiguity_rate(logs),
        "mismatch": check_mismatch_rate(logs),
        "scores": check_score_distributions(logs),
        "empty": check_empty_rate(logs)
    }
    
    # Overall status
    overall_status = compute_overall_status(checks)
    
    # Build report
    report = {
        "timestamp": logs[-1]["timestamp"] if logs else None,
        "total_queries_analyzed": len(logs),
        "status": overall_status,
        "checks": checks
    }
    
    return report


def print_report(report: Dict):
    """Print human-readable report to terminal."""
    print("\n" + "="*70)
    print("🩺 LIBRARIAN HEALTH CHECK")
    print("="*70 + "\n")
    
    if "error" in report:
        print(f"❌ {report['error']}")
        print(f"   Log file: {report['log_file']}")
        return
    
    # Overall status
    status_emoji = {
        "healthy": "✅",
        "degraded": "⚠️ ",
        "skewed": "⚠️ ",
        "broken": "❌"
    }
    
    print(f"{status_emoji.get(report['status'], '❓')} Overall Status: {report['status'].upper()}")
    print(f"📊 Queries Analyzed: {report['total_queries_analyzed']}\n")
    
    # Individual checks
    checks = report["checks"]
    
    print("─" * 70)
    print("CHECK 1: Fallback Rate")
    print(f"  Status: {_status_icon(checks['fallback']['status'])} {checks['fallback']['status'].upper()}")
    print(f"  Rate: {checks['fallback']['fallback_rate']:.1%} ({checks['fallback']['fallback_count']}/{checks['fallback']['total_queries']})")
    print(f"  Threshold: warn={THRESHOLDS['fallback_rate']['warn']:.0%}, fail={THRESHOLDS['fallback_rate']['fail']:.0%}")
    
    print("\n" + "─" * 70)
    print("CHECK 2: Cluster Concentration")
    print(f"  Status: {_status_icon(checks['cluster_concentration']['status'])} {checks['cluster_concentration']['status'].upper()}")
    print(f"  Top cluster: {checks['cluster_concentration']['top_cluster_id']}")
    print(f"  Concentration: {checks['cluster_concentration']['top_cluster_concentration']:.1%}")
    print(f"  Distribution: {json.dumps(checks['cluster_concentration']['cluster_distribution'], indent=4)}")
    
    print("\n" + "─" * 70)
    print("CHECK 3: Ambiguity Rate")
    print(f"  Status: {_status_icon(checks['ambiguity']['status'])} {checks['ambiguity']['status'].upper()}")
    print(f"  Rate: {checks['ambiguity']['ambiguity_rate']:.1%} ({checks['ambiguity']['ambiguous_count']}/{checks['ambiguity']['total_queries']})")
    
    print("\n" + "─" * 70)
    print("CHECK 4: Cluster-Chunk Mismatch")
    print(f"  Status: {_status_icon(checks['mismatch']['status'])} {checks['mismatch']['status'].upper()}")
    print(f"  Rate: {checks['mismatch']['mismatch_rate']:.1%} ({checks['mismatch']['mismatch_count']}/{checks['mismatch']['total_queries']})")
    
    print("\n" + "─" * 70)
    print("CHECK 5: Score Distributions")
    print(f"  Avg Cluster Score: {checks['scores']['avg_cluster_score']:.3f} [{_status_icon(checks['scores']['cluster_status'])}]")
    print(f"  Avg Chunk Score: {checks['scores']['avg_chunk_score']:.3f} [{_status_icon(checks['scores']['chunk_status'])}]")
    print(f"  Interpretation: {checks['scores']['interpretation']}")
    
    print("\n" + "─" * 70)
    print("CHECK 6: Empty Result Rate")
    print(f"  Status: {_status_icon(checks['empty']['status'])} {checks['empty']['status'].upper()}")
    print(f"  Rate: {checks['empty']['empty_rate']:.1%} ({checks['empty']['empty_count']}/{checks['empty']['total_queries']})")
    
    print("\n" + "="*70 + "\n")


def _status_icon(status: str) -> str:
    """Get emoji for status."""
    return {
        "pass": "✅",
        "warn": "⚠️ ",
        "fail": "❌"
    }.get(status, "❓")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Librarian Health Checks")
    parser.add_argument('--last', type=int, help="Analyze only last N queries")
    parser.add_argument('--json', action='store_true', help="Output JSON only (no terminal)")
    
    args = parser.parse_args()
    
    # Run analysis
    report = analyze(limit=args.last)
    
    # Save report
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
        print(f"📁 Report saved: {REPORT_FILE}")
    
    # Exit code based on status
    status = report.get("status", "healthy")
    if status == "broken":
        return 2
    elif status in ["degraded", "skewed"]:
        return 1
    else:
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
