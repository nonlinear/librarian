"""
Update literature index: only index EPUBs that are not already in the index.
Run manually to keep the index up to date without watching.
"""
import os
from pathlib import Path
from literature_watchdog import index_book, BOOKS_DIR, STORAGE_DIR

import json

# Path to the denylist JSON file
INDEXED_JSON_PATH = Path(__file__).parent / "indexed_books.json"


def get_indexed_books():
    """Return a set of (folder, book_name) tuples for all indexed books from the JSON denylist."""
    if not INDEXED_JSON_PATH.exists():
        # First run: populate with all existing books
        all_books = []
        for folder, _, files in os.walk(BOOKS_DIR):
            folder_path = Path(folder)
            folder_name = folder_path.name
            for epub in files:
                if epub.lower().endswith('.epub'):
                    book_name = Path(epub).stem
                    all_books.append({"folder": folder_name, "book_name": book_name})
        with open(INDEXED_JSON_PATH, "w") as f:
            json.dump(all_books, f, indent=2)
        return set((item["folder"], item["book_name"]) for item in all_books)
    try:
        with open(INDEXED_JSON_PATH, "r") as f:
            data = json.load(f)
        return set((item["folder"], item["book_name"]) for item in data)
    except Exception as e:
        print(f"[WARN] Could not load indexed_books.json: {e}")
        return set()




def update_literature(specific_topic=None):
    print("\n🔎 Scanning for new EPUBs..." + (f" (topic: {specific_topic})" if specific_topic else ""))
    indexed_books = get_indexed_books()
    all_epubs = []
    search_dir = BOOKS_DIR if not specific_topic else Path(BOOKS_DIR) / specific_topic
    if not search_dir.exists():
        print(f"[ERROR] Folder not found: {search_dir}")
        return
    for folder, _, files in os.walk(search_dir):
        folder_path = Path(folder)
        folder_name = folder_path.name
        for epub in files:
            if epub.lower().endswith('.epub'):
                book_name = Path(epub).stem
                all_epubs.append({"folder": folder_name, "book_name": book_name, "path": str(folder_path / epub)})

    # Only index books not present in the denylist JSON
    to_index = [item for item in all_epubs if (item["folder"], item["book_name"]) not in indexed_books]

    if not to_index:
        print("No new books to index. ✅")
        return

    indexed = []
    errors = []
    for item in to_index:
        epub_path = Path(item["path"])
        try:
            index_book(epub_path)
            indexed.append(item)
        except Exception as e:
            errors.append((item["path"], str(e)))

    # Add newly indexed books to denylist JSON
    try:
        with open(INDEXED_JSON_PATH, "r") as f:
            data = json.load(f)
        # Add new books
        for item in indexed:
            data.append({"folder": item["folder"], "book_name": item["book_name"]})
        with open(INDEXED_JSON_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[WARN] Could not update indexed_books.json: {e}")

    print("\n=== Update Report ===")
    if indexed:
        print("Indexed:")
        for item in indexed:
            print(f"  - {item['path']}")
    if errors:
        print("\nErrors:")
        for path, err in errors:
            print(f"  - {path}: {err}")
    print("\n✅ Update complete.")

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    update_literature(topic)
