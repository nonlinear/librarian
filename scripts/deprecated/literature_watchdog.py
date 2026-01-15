#!/usr/bin/env python3
"""
Watchdog for automatic book indexing.
Triggered by any file change in literature/books/ (via Hammerspoon or CLI). Auto-indexes new/changed EPUBs.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.google import GeminiEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.readers.file import EpubReader
from rag_cost_tracker import RAGCostTracker

# Load environment
load_dotenv()

# Setup paths
BASE_DIR = Path(__file__).parent.parent
BOOKS_DIR = BASE_DIR / "books"
STORAGE_DIR = BASE_DIR / "storage"

# Initialize models
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

embed_model = GeminiEmbedding(model_name="models/embedding-001", api_key=api_key)
llm = GoogleGenAI(model="models/gemini-2.5-flash", api_key=api_key)
Settings.embed_model = embed_model
Settings.llm = llm

# Cost tracker
cost_tracker = RAGCostTracker()


def extract_keywords_from_book(book_text: str, book_name: str) -> list[str]:
    """Use LLM to extract keywords from book content"""
    prompt = f"""
    Analyze this book excerpt and extract 15-20 relevant keywords/topics.
    Book: {book_name}

    Excerpt: {book_text[:2000]}

    Return ONLY comma-separated keywords, lowercase, no explanation.
    Focus on: main themes, concepts, disciplines, related fields.
    """

    response = llm.complete(prompt)
    keywords_str = str(response).strip()
    keywords = [k.strip() for k in keywords_str.split(',')]
    return [k for k in keywords if k and len(k) > 2][:20]


def update_rag_topics(folder: Path, book_name: str, keywords: list[str]):
    """Update or create .rag-topics file"""
    topics_file = folder / ".rag-topics"

    if topics_file.exists():
        # Read existing
        content = topics_file.read_text()
        lines = content.split('\n')

        # Update keywords line
        new_lines = []
        keywords_updated = False
        books_updated = False

        for line in lines:
            if line.startswith('Keywords:'):
                # Merge with existing
                existing = line.split('Keywords:', 1)[1].strip()
                existing_keys = [k.strip() for k in existing.split(',')]
                merged = list(set(existing_keys + keywords))
                new_lines.append(f"Keywords: {', '.join(merged)}")
                keywords_updated = True
            elif line.startswith('Books:'):
                # Add book if not present
                existing_books = line.split('Books:', 1)[1].strip()
                if book_name not in existing_books:
                    new_lines.append(f"Books: {existing_books}, {book_name}")
                else:
                    new_lines.append(line)
                books_updated = True
            elif line.startswith('Last-indexed:'):
                new_lines.append(f"Last-indexed: {datetime.now().strftime('%Y-%m-%d')}")
            else:
                new_lines.append(line)

        if not keywords_updated:
            new_lines.insert(5, f"Keywords: {', '.join(keywords)}")
        if not books_updated:
            new_lines.insert(6, f"Books: {book_name}")

        content = '\n'.join(new_lines)
    else:
        # Create new
        content = f"""# RAG Topics Configuration
# Auto-generated: {datetime.now().strftime('%Y-%m-%d')}

Keywords: {', '.join(keywords)}

Books: {book_name}

Description: Auto-detected topics

Auto-update: true
Last-indexed: {datetime.now().strftime('%Y-%m-%d')}
"""

    topics_file.write_text(content)
    print(f"✓ Updated {topics_file}")


def index_book(epub_path: Path):
    """Index a single EPUB book"""
    book_name = epub_path.stem
    folder = epub_path.parent

    print(f"\n📚 Indexing: {book_name}")
    print(f"   Folder: {folder.name}")

    # Load book
    if epub_path.is_file():
        reader = SimpleDirectoryReader(
            input_files=[str(epub_path)],
            file_extractor={".epub": EpubReader()}
        )
    else:  # Directory (unzipped EPUB)
        reader = SimpleDirectoryReader(
            input_dir=str(epub_path),
            required_exts=[".html", ".xhtml"],
            recursive=True
        )

    documents = reader.load_data()
    print(f"   ✓ Loaded {len(documents)} chunks")

    # Extract keywords from first few chunks
    sample_text = ' '.join([doc.text for doc in documents[:3]])
    print(f"   🔍 Extracting keywords...")
    keywords = extract_keywords_from_book(sample_text, book_name)
    print(f"   ✓ Found {len(keywords)} keywords")

    # Update or create index
    if STORAGE_DIR.exists() and (STORAGE_DIR / "docstore.json").exists():
        print(f"   📊 Updating existing index...")
        storage_context = StorageContext.from_defaults(persist_dir=str(STORAGE_DIR))
        index = load_index_from_storage(storage_context)

        # Add new documents
        for doc in documents:
            index.insert(doc)
    else:
        print(f"   📊 Creating new index...")
        index = VectorStoreIndex.from_documents(documents)

    # Persist
    index.storage_context.persist(persist_dir=str(STORAGE_DIR))
    print(f"   ✓ Index saved")

    # Track costs
    total_chars = sum(len(doc.text) for doc in documents)
    tokens = int(total_chars * 0.75)
    cost = cost_tracker.log_embedding(book_name, tokens, "gemini_embedding")
    print(f"   💰 Cost: ${cost:.4f}")

    # Update .rag-topics
    print(f"   📝 Updating .rag-topics...")
    update_rag_topics(folder, book_name, keywords)

    print(f"✅ Done indexing {book_name}\n")


def remove_book_from_topics(folder: Path, book_name: str):
    """Remove book from .rag-topics file"""
    topics_file = folder / ".rag-topics"

    if not topics_file.exists():
        return

    content = topics_file.read_text()
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        if line.startswith('Books:'):
            # Remove book from list
            books_str = line.split('Books:', 1)[1].strip()
            books = [b.strip() for b in books_str.split(',')]
            books = [b for b in books if b != book_name]

            if books:
                new_lines.append(f"Books: {', '.join(books)}")
            else:
                # No books left, mark for deletion
                continue
        elif line.startswith('Last-indexed:'):
            new_lines.append(f"Last-indexed: {datetime.now().strftime('%Y-%m-%d')}")
        else:
            new_lines.append(line)

    if any('Books:' in line for line in new_lines):
        topics_file.write_text('\n'.join(new_lines))
        print(f"   ✓ Updated {topics_file}")
    else:
        # No books left, optionally delete .rag-topics
        print(f"   ⚠️  No books left in folder")


def remove_book_from_index(book_name: str):
    """Remove book documents from index (soft delete by marking)"""
    print(f"\n🗑️  Removing: {book_name}")

    # Note: LlamaIndex doesn't have built-in document removal
    # Best approach: rebuild index without the removed book
    # For now, just log it - user can re-index manually if needed

    print(f"   ℹ️  Book marked for removal")
    print(f"   💡 To fully remove, re-index all remaining books")
    print(f"   💡 Or use: python3 code/rebuild_index.py")

    # Track in costs (negative entry or flag)
    cost_tracker.costs.setdefault("removed_books", []).append({
        "name": book_name,
        "date": datetime.now().isoformat()
    })
    cost_tracker._save_costs()

    print(f"   ✓ Marked in tracking")



class BookHandler(FileSystemEventHandler):
    """On file event, index only changed EPUB or remove deleted EPUB from index"""

    def on_any_event(self, event):
        print(f"[DEBUG] Event received: type={event.event_type}, path={event.src_path}, is_directory={event.is_directory}")
        if event.is_directory:
            print("[DEBUG] Ignoring directory event.")
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".epub":
            if event.event_type in ("created", "modified", "moved"):
                print(f"🔄 Indexing changed file: {path}")
                try:
                    index_book(path)
                except Exception as e:
                    print(f"❌ Error indexing {path}: {e}")
            elif event.event_type == "deleted":
                print(f"🗑️ Removing deleted file: {path}")
                try:
                    remove_book_from_index(path.stem)
                    remove_book_from_topics(path.parent, path.stem)
                except Exception as e:
                    print(f"❌ Error removing {path}: {e}")


def reindex_all_books():
    """Reindex all EPUBs in all subfolders and update .rag-topics"""
    print("\n🚀 Reindexing all books...")
    for folder, _, files in os.walk(BOOKS_DIR):
        folder_path = Path(folder)
        epubs = [f for f in files if f.lower().endswith('.epub')]
        for epub in epubs:
            epub_path = folder_path / epub
            try:
                index_book(epub_path)
            except Exception as e:
                print(f"❌ Error indexing {epub}: {e}")
    print("\n✅ Reindexing complete.")


def main():
    """Start watchdog service"""
    print("=" * 60)
    print("📚 Literature Watchdog Service")
    print("=" * 60)
    print(f"Monitoring: {BOOKS_DIR}")
    print("Waiting for new EPUB files...\n")


    from watchdog.observers.polling import PollingObserver
    event_handler = BookHandler()
    observer = PollingObserver()
    observer.schedule(event_handler, str(BOOKS_DIR), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping watchdog...")
        observer.stop()

    observer.join()
    print("✓ Watchdog stopped")


if __name__ == "__main__":
    main()
