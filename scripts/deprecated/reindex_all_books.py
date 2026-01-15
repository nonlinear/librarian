"""
Reindex all EPUBs in the books directory, rebuilding the index from scratch.
Deletes the storage directory before starting.
"""
import os
import shutil
from pathlib import Path
from literature_watchdog import index_book, BOOKS_DIR, STORAGE_DIR

def clean_storage():
    if STORAGE_DIR.exists():
        print(f"Deleting storage directory: {STORAGE_DIR}")
        shutil.rmtree(STORAGE_DIR)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def reindex_all():
    print("\n🚀 Reindexing all books from scratch...")
    for folder, _, files in os.walk(BOOKS_DIR):
        folder_path = Path(folder)
        epubs = [f for f in files if f.lower().endswith('.epub')]
        for epub in epubs:
            epub_path = folder_path / epub
            try:
                index_book(epub_path)
            except Exception as e:
                print(f"❌ Error indexing {epub_path}: {e}")
    print("\n✅ Reindexing complete.")

if __name__ == "__main__":
    clean_storage()
    reindex_all()
