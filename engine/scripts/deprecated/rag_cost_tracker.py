#!/usr/bin/env python3
"""
Tracks embedding and query costs per book.
Triggered internally by other scripts whenever embeddings or queries are run.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class RAGCostTracker:
    def __init__(self, storage_path: str = "/Users/nfrota/Documents/literature/storage/costs.json"):
        self.storage_path = Path(storage_path)
        self.costs = self._load_costs()

        # Pricing per 1M tokens (update as needed)
        self.pricing = {
            "openai_embedding": 0.00013,  # text-embedding-3-small per 1K tokens
            "openai_query": 0.00013,
            "gemini_embedding": 0.0,  # Free tier
            "gemini_query": 0.0,
        }

    def _load_costs(self) -> Dict:
        """Load existing cost data"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {"books": {}, "monthly": {}}

    def _save_costs(self):
        """Save cost data"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.costs, f, indent=2)

    def log_embedding(self, book_name: str, num_tokens: int, model: str = "openai_embedding"):
        """Log embedding cost for a book"""
        cost = (num_tokens / 1000) * self.pricing[model]

        if book_name not in self.costs["books"]:
            self.costs["books"][book_name] = {
                "embedding_cost": 0,
                "embedding_tokens": 0,
                "embedding_date": None,
                "queries": []
            }

        self.costs["books"][book_name]["embedding_cost"] = cost
        self.costs["books"][book_name]["embedding_tokens"] = num_tokens
        self.costs["books"][book_name]["embedding_date"] = datetime.now().isoformat()

        self._save_costs()
        return cost

    def log_query(self, book_name: str, num_tokens: int, model: str = "openai_query"):
        """Log query cost for a book"""
        cost = (num_tokens / 1000) * self.pricing[model]
        month = datetime.now().strftime("%Y-%m")

        if book_name not in self.costs["books"]:
            self.costs["books"][book_name] = {
                "embedding_cost": 0,
                "embedding_tokens": 0,
                "queries": []
            }

        query_entry = {
            "date": datetime.now().isoformat(),
            "tokens": num_tokens,
            "cost": cost,
            "month": month
        }
        self.costs["books"][book_name]["queries"].append(query_entry)

        # Update monthly totals
        if month not in self.costs["monthly"]:
            self.costs["monthly"][month] = {}

        if book_name not in self.costs["monthly"][month]:
            self.costs["monthly"][month][book_name] = {
                "query_count": 0,
                "total_cost": 0,
                "total_tokens": 0
            }

        self.costs["monthly"][month][book_name]["query_count"] += 1
        self.costs["monthly"][month][book_name]["total_cost"] += cost
        self.costs["monthly"][month][book_name]["total_tokens"] += num_tokens

        self._save_costs()
        return cost

    def get_book_costs(self, book_name: str) -> Dict:
        """Get all costs for a specific book"""
        if book_name not in self.costs["books"]:
            return None

        book_data = self.costs["books"][book_name]
        total_query_cost = sum(q["cost"] for q in book_data["queries"])
        total_cost = book_data["embedding_cost"] + total_query_cost

        return {
            "book": book_name,
            "embedding_cost": book_data["embedding_cost"],
            "total_query_cost": total_query_cost,
            "total_cost": total_cost,
            "query_count": len(book_data["queries"])
        }

    def get_monthly_costs(self, month: str = None) -> Dict:
        """Get costs for a specific month (defaults to current)"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")

        return self.costs["monthly"].get(month, {})

    def print_report(self):
        """Print formatted cost report"""
        print("\n" + "=" * 80)
        print("📊 RAG COST REPORT")
        print("=" * 80)

        # Per-book costs
        print("\n📚 COST BY BOOK:\n")
        print(f"{'Book':<40} {'Embed $':<12} {'Queries':<10} {'Query $':<12} {'Total $':<12}")
        print("-" * 80)

        total_embedding = 0
        total_queries = 0
        total_query_cost = 0

        for book_name in sorted(self.costs["books"].keys()):
            costs = self.get_book_costs(book_name)
            if costs:
                # Truncate book name if too long
                display_name = book_name[:37] + "..." if len(book_name) > 40 else book_name
                print(f"{display_name:<40} ${costs['embedding_cost']:<11.4f} "
                      f"{costs['query_count']:<10} ${costs['total_query_cost']:<11.4f} "
                      f"${costs['total_cost']:<11.4f}")

                total_embedding += costs['embedding_cost']
                total_queries += costs['query_count']
                total_query_cost += costs['total_query_cost']

        print("-" * 80)
        print(f"{'TOTAL':<40} ${total_embedding:<11.4f} "
              f"{total_queries:<10} ${total_query_cost:<11.4f} "
              f"${total_embedding + total_query_cost:<11.4f}")

        # Monthly breakdown
        if self.costs["monthly"]:
            print("\n\n📅 MONTHLY COSTS:\n")
            print(f"{'Month':<10} {'Book':<40} {'Queries':<10} {'Cost $':<12}")
            print("-" * 80)

            for month in sorted(self.costs["monthly"].keys(), reverse=True):
                month_data = self.costs["monthly"][month]
                for book_name, data in sorted(month_data.items()):
                    display_name = book_name[:37] + "..." if len(book_name) > 40 else book_name
                    print(f"{month:<10} {display_name:<40} "
                          f"{data['query_count']:<10} ${data['total_cost']:<11.4f}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    # Example usage
    tracker = RAGCostTracker()
    tracker.print_report()
