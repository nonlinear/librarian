#!/usr/bin/env python3
"""
Detailed cost report for Literature RAG.
Triggered by CLI: python3 scripts/view_detailed_costs.py
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
BOOKS_DIR = BASE_DIR / "literature" / "books"
COSTS_FILE = STORAGE_DIR / "costs.json"


def load_costs():
    """Load costs from JSON"""
    if not COSTS_FILE.exists():
        return {"books": {}, "monthly": {}}

    with open(COSTS_FILE, 'r') as f:
        return json.load(f)


def get_book_folder(book_name):
    """Find which folder a book belongs to"""
    for folder in BOOKS_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue

        for item in folder.iterdir():
            if item.stem == book_name and (item.suffix == '.epub' or (item.is_dir() and item.suffix == '.epub')):
                return folder.name

    return "Unknown"


def print_book_costs(costs):
    """Print detailed costs per book"""
    print("\n" + "=" * 100)
    print("📚 COSTS PER BOOK")
    print("=" * 100)

    print(f"\n{'Book':<40} {'Folder':<15} {'Embedding $':<15} {'Queries':<10} {'Query $':<15} {'Total $':<15}")
    print("-" * 100)

    books_data = costs.get("books", {})
    total_embedding = 0
    total_queries = 0
    total_query_cost = 0

    for book_name, book_data in sorted(books_data.items()):
        folder = get_book_folder(book_name)
        embedding_cost = book_data.get("embedding_cost", 0)
        queries = book_data.get("queries", [])
        query_cost = sum(q.get("cost", 0) for q in queries)
        query_count = len(queries)
        total_cost = embedding_cost + query_cost

        # Truncate long names
        display_name = book_name[:37] + "..." if len(book_name) > 40 else book_name

        print(f"{display_name:<40} {folder:<15} ${embedding_cost:<14.4f} {query_count:<10} ${query_cost:<14.4f} ${total_cost:<14.4f}")

        total_embedding += embedding_cost
        total_queries += query_count
        total_query_cost += query_cost

    print("-" * 100)
    print(f"{'TOTAL':<40} {'':<15} ${total_embedding:<14.4f} {total_queries:<10} ${total_query_cost:<14.4f} ${total_embedding + total_query_cost:<14.4f}")


def print_folder_costs(costs):
    """Print costs aggregated by folder"""
    print("\n\n" + "=" * 100)
    print("📁 COSTS PER FOLDER")
    print("=" * 100)

    # Aggregate by folder
    folder_stats = defaultdict(lambda: {
        "books": [],
        "embedding_cost": 0,
        "query_count": 0,
        "query_cost": 0,
        "total_cost": 0
    })

    books_data = costs.get("books", {})
    for book_name, book_data in books_data.items():
        folder = get_book_folder(book_name)

        embedding_cost = book_data.get("embedding_cost", 0)
        queries = book_data.get("queries", [])
        query_cost = sum(q.get("cost", 0) for q in queries)
        query_count = len(queries)

        folder_stats[folder]["books"].append(book_name)
        folder_stats[folder]["embedding_cost"] += embedding_cost
        folder_stats[folder]["query_count"] += query_count
        folder_stats[folder]["query_cost"] += query_cost
        folder_stats[folder]["total_cost"] += embedding_cost + query_cost

    print(f"\n{'Folder':<20} {'Books':<8} {'Embedding $':<15} {'Queries':<10} {'Query $':<15} {'Total $':<15}")
    print("-" * 100)

    for folder, stats in sorted(folder_stats.items()):
        print(f"{folder:<20} {len(stats['books']):<8} ${stats['embedding_cost']:<14.4f} "
              f"{stats['query_count']:<10} ${stats['query_cost']:<14.4f} ${stats['total_cost']:<14.4f}")

        # Show books in folder
        for book in stats['books']:
            print(f"  └─ {book}")

    print("-" * 100)
    total_books = sum(len(stats['books']) for stats in folder_stats.values())
    total_embedding = sum(stats['embedding_cost'] for stats in folder_stats.values())
    total_queries = sum(stats['query_count'] for stats in folder_stats.values())
    total_query_cost = sum(stats['query_cost'] for stats in folder_stats.values())
    total_cost = total_embedding + total_query_cost

    print(f"{'TOTAL':<20} {total_books:<8} ${total_embedding:<14.4f} {total_queries:<10} ${total_query_cost:<14.4f} ${total_cost:<14.4f}")


def print_monthly_costs(costs):
    """Print monthly query costs with frequency"""
    print("\n\n" + "=" * 100)
    print("📅 MONTHLY QUERY COSTS")
    print("=" * 100)

    monthly_data = costs.get("monthly", {})

    if not monthly_data:
        print("\nNo monthly data yet.")
        return

    print(f"\n{'Month':<12} {'Book':<40} {'Folder':<15} {'Queries':<10} {'Cost $':<15}")
    print("-" * 100)

    for month in sorted(monthly_data.keys(), reverse=True):
        month_books = monthly_data[month]

        for book_name, data in sorted(month_books.items()):
            folder = get_book_folder(book_name)
            display_name = book_name[:37] + "..." if len(book_name) > 40 else book_name

            print(f"{month:<12} {display_name:<40} {folder:<15} "
                  f"{data['query_count']:<10} ${data['total_cost']:<14.4f}")

    # Monthly totals
    print("\n" + "=" * 100)
    print("📊 MONTHLY TOTALS")
    print("=" * 100)

    print(f"\n{'Month':<12} {'Total Queries':<20} {'Total Cost $':<15}")
    print("-" * 100)

    for month in sorted(monthly_data.keys(), reverse=True):
        total_queries = sum(data['query_count'] for data in monthly_data[month].values())
        total_cost = sum(data['total_cost'] for data in monthly_data[month].values())

        print(f"{month:<12} {total_queries:<20} ${total_cost:<14.4f}")


def print_usage_frequency(costs):
    """Print usage frequency statistics"""
    print("\n\n" + "=" * 100)
    print("📈 USAGE FREQUENCY")
    print("=" * 100)

    books_data = costs.get("books", {})

    # Calculate query frequency
    usage_stats = []
    for book_name, book_data in books_data.items():
        queries = book_data.get("queries", [])
        if not queries:
            continue

        folder = get_book_folder(book_name)
        first_query = datetime.fromisoformat(queries[0]["date"])
        last_query = datetime.fromisoformat(queries[-1]["date"])
        days_span = (last_query - first_query).days + 1

        queries_per_day = len(queries) / days_span if days_span > 0 else len(queries)

        usage_stats.append({
            "book": book_name,
            "folder": folder,
            "total_queries": len(queries),
            "days_span": days_span,
            "queries_per_day": queries_per_day,
            "last_used": last_query.strftime("%Y-%m-%d")
        })

    # Sort by usage frequency
    usage_stats.sort(key=lambda x: x["queries_per_day"], reverse=True)

    print(f"\n{'Book':<40} {'Folder':<15} {'Queries':<10} {'Days':<8} {'Queries/Day':<15} {'Last Used':<12}")
    print("-" * 100)

    for stat in usage_stats:
        display_name = stat['book'][:37] + "..." if len(stat['book']) > 40 else stat['book']
        print(f"{display_name:<40} {stat['folder']:<15} {stat['total_queries']:<10} "
              f"{stat['days_span']:<8} {stat['queries_per_day']:<15.2f} {stat['last_used']:<12}")


def main():
    """Generate comprehensive cost report"""
    print("=" * 100)
    print("📊 LITERATURE RAG - COMPREHENSIVE COST REPORT")
    print("=" * 100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    costs = load_costs()

    # All reports
    print_book_costs(costs)
    print_folder_costs(costs)
    print_monthly_costs(costs)
    print_usage_frequency(costs)

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
