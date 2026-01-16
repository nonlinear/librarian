#!/usr/bin/env python3
"""
Generate metadata.json from books/ folder structure.

This script:
1. Scans books/ for topics (folders) and EPUBs
2. Extracts metadata (title, author) from EPUB files
3. Generates semantic tags from book content using KeyBERT
4. Creates storage/metadata.json (the navigation map)
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from keybert import KeyBERT
import re


# Paths
BOOKS_DIR = Path(__file__).parent.parent / "books"
STORAGE_DIR = Path(__file__).parent.parent / "storage"
METADATA_FILE = STORAGE_DIR / "metadata.json"

# Tag extraction model (KeyBERT with MiniLM backend)
print("Loading KeyBERT model...")
kw_model = KeyBERT('all-MiniLM-L6-v2')
print("✅ Model loaded")


def slugify(text: str) -> str:
    """Convert text to lowercase slug."""
    return re.sub(r'[^\w\s-]', '', text.lower()).strip().replace(' ', '_')


def extract_epub_metadata(epub_path: Path) -> Dict:
    """Extract title, author from EPUB metadata."""
    try:
        book = epub.read_epub(str(epub_path))

        title = book.get_metadata('DC', 'title')
        title = title[0][0] if title else epub_path.stem

        author = book.get_metadata('DC', 'creator')
        author = author[0][0] if author else "Unknown"

        # Extract year if available
        date = book.get_metadata('DC', 'date')
        year = None
        if date:
            year_match = re.search(r'\d{4}', date[0][0])
            year = int(year_match.group()) if year_match else None

        return {
            "title": title,
            "author": author,
            "year": year
        }
    except Exception as e:
        print(f"⚠️  Error reading {epub_path.name}: {e}")
        return {
            "title": epub_path.stem,
            "author": "Unknown",
            "year": None
        }


def extract_sample_text(epub_path: Path, max_chars: int = 5000) -> str:
    """Extract sample text from EPUB for tag generation."""
    try:
        book = epub.read_epub(str(epub_path))
        text_parts = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text()
            text_parts.append(text)

            if len(' '.join(text_parts)) > max_chars:
                break

        return ' '.join(text_parts)[:max_chars]
    except Exception as e:
        print(f"⚠️  Error extracting text from {epub_path.name}: {e}")
        return ""


def generate_tags_from_text(text: str, num_tags: int = 6) -> List[str]:
    """
    Generate semantic tags from text using KeyBERT.

    KeyBERT uses embeddings to extract keywords that best represent the document.
    More accurate than simple frequency counting.
    """
    if not text or len(text.strip()) < 100:
        return ["untagged"]

    try:
        # Extract keywords with KeyBERT
        # keyphrase_ngram_range=(1, 2) = unigrams and bigrams
        # stop_words='english' = remove common words
        # top_n = number of keywords to extract
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=num_tags,
            use_mmr=True,  # Maximal Marginal Relevance for diversity
            diversity=0.5
        )

        # Convert to slug format
        tags = [kw[0].lower().replace(' ', '-') for kw in keywords]

        return tags if tags else ["untagged"]

    except Exception as e:
        print(f"   ⚠️  Tag extraction failed: {e}")
        return ["untagged"]


def scan_books_folder() -> Dict:
    """
    Scan books/ and generate metadata structure.

    CRITICAL: books/ is the TERRITORY (source of truth).
              metadata.json is the MAP (follows territory).

    This function ALWAYS does a full scan of books/ folder and regenerates
    metadata.json from scratch. Any existing metadata.json is IGNORED and
    OVERWRITTEN. If there's a discrepancy, books/ wins, always.

    The map follows the territory, never the other way around.
    """
    # Get absolute path to library root (parent of books/ folder)
    library_path = str(BOOKS_DIR.parent.absolute())

    topics = []

    for topic_dir in sorted(BOOKS_DIR.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name.startswith('.'):
            continue

        topic_id = slugify(topic_dir.name)
        books = []

        # Find all EPUBs in topic
        for epub_file in sorted(topic_dir.glob("*.epub")):
            print(f"📚 Processing: {topic_dir.name}/{epub_file.name}")

            # Extract metadata
            metadata = extract_epub_metadata(epub_file)

            # Generate tags from content
            sample_text = extract_sample_text(epub_file)
            tags = generate_tags_from_text(sample_text)

            book_entry = {
                "id": slugify(epub_file.stem),
                "title": metadata["title"],
                "author": metadata["author"],
                "year": metadata["year"],
                "tags": tags,
                "filename": epub_file.name
            }

            books.append(book_entry)
            print(f"   Tags: {', '.join(tags)}")

        if books:
            # Topic description = first few tags from all books
            all_tags = []
            for book in books:
                all_tags.extend(book["tags"])
            topic_tags = list(set(all_tags))[:8]

            topic_entry = {
                "id": topic_id,
                "label": topic_dir.name,
                "description": ", ".join(topic_tags),
                "books": books
            }

            topics.append(topic_entry)

    return {
        "library_path": library_path,
        "topics": topics
    }


def main():
    """Generate metadata.json from books/ folder."""
    print("🔨 Generating metadata.json from books/")
    print(f"📁 Books directory: {BOOKS_DIR}")
    print()

    # Scan books
    metadata = scan_books_folder()

    # Ensure storage/ exists
    STORAGE_DIR.mkdir(exist_ok=True)

    # Write metadata.json
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print()
    print(f"✅ Generated: {METADATA_FILE}")
    print(f"   Topics: {len(metadata['topics'])}")
    print(f"   Books: {sum(len(t['books']) for t in metadata['topics'])}")


if __name__ == "__main__":
    main()
