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
METADATA_FILE = BOOKS_DIR / "metadata.json"
FAILED_FILE = Path(__file__).parent.parent / "engine" / "docs" / "FAILED.md"

# Track failed books (reset on each run)
FAILED_BOOKS = []

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
        FAILED_BOOKS.append({
            "file": str(epub_path.relative_to(BOOKS_DIR.parent)),
            "error": str(e),
            "type": "epub_metadata"
        })
        return {
            "title": epub_path.stem,
            "author": "Unknown",
            "year": None
        }


def extract_pdf_metadata(pdf_path: Path) -> Dict:
    """Extract title, author from PDF metadata."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        metadata = doc.metadata

        title = metadata.get('title', pdf_path.stem)
        if not title or title.strip() == '':
            title = pdf_path.stem

        author = metadata.get('author', 'Unknown')
        if not author or author.strip() == '':
            author = 'Unknown'

        # Extract year from creation date or modification date
        year = None
        for date_field in ['creationDate', 'modDate']:
            if date_field in metadata and metadata[date_field]:
                year_match = re.search(r'\d{4}', metadata[date_field])
                if year_match:
                    year = int(year_match.group())
                    break

        doc.close()
        return {
            "title": title,
            "author": author,
            "year": year
        }
    except Exception as e:
        print(f"⚠️  Error reading {pdf_path.name}: {e}")
        FAILED_BOOKS.append({
            "file": str(pdf_path.relative_to(BOOKS_DIR.parent)),
            "error": str(e),
            "type": "pdf_metadata"
        })
        return {
            "title": pdf_path.stem,
            "author": "Unknown",
            "year": None
        }


def extract_sample_text_pdf(pdf_path: Path, max_chars: int = 5000) -> str:
    """Extract sample text from PDF for tag generation."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        text_parts = []

        # Extract text from first few pages
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            text_parts.append(page.get_text())

        doc.close()
        full_text = ' '.join(text_parts)
        return full_text[:max_chars] if len(full_text) > max_chars else full_text
    except Exception as e:
        print(f"⚠️  Error extracting text from {pdf_path.name}: {e}")
        return ""


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
        FAILED_BOOKS.append({
            "file": "tag_extraction",
            "error": str(e),
            "type": "tag_generation"
        })
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

    def process_topic_folder(topic_dir: Path, parent_topic_id: str = None, parent_path: str = None):
        """Process a topic folder and optionally its subfolders."""
        topic_id = slugify(topic_dir.name)
        # Build folder path relative to books/
        folder_path = topic_dir.name if parent_path is None else f"{parent_path}/{topic_dir.name}"

        if parent_topic_id:
            topic_id = f"{parent_topic_id}_{topic_id}"

        books = []

        # Find all EPUBs and PDFs in this folder (not subfolders)
        book_files = list(topic_dir.glob("*.epub")) + list(topic_dir.glob("*.pdf"))
        for book_file in sorted(book_files):
            print(f"📚 Processing: {topic_dir.name}/{book_file.name}")

            # Extract metadata based on file type
            if book_file.suffix.lower() == '.epub':
                metadata = extract_epub_metadata(book_file)
                sample_text = extract_sample_text(book_file)
            elif book_file.suffix.lower() == '.pdf':
                metadata = extract_pdf_metadata(book_file)
                sample_text = extract_sample_text_pdf(book_file)
            else:
                continue

            # Generate tags from content
            tags = generate_tags_from_text(sample_text)

            book_entry = {
                "id": slugify(book_file.stem),
                "title": metadata["title"],
                "author": metadata["author"],
                "year": metadata["year"],
                "tags": tags,
                "filename": book_file.name
            }

            books.append(book_entry)
            print(f"   Tags: {', '.join(tags)}")

        result_topics = []

        if books:
            # Topic description = first few tags from all books
            all_tags = []
            for book in books:
                all_tags.extend(book["tags"])
            topic_tags = list(set(all_tags))[:8]

            topic_entry = {
                "id": topic_id,
                "label": topic_dir.name,
                "folder_path": folder_path,  # e.g., "AI/theory" or "product architecture"
                "description": ", ".join(topic_tags),
                "books": books
            }

            result_topics.append(topic_entry)

        # Process subfolders as separate topics
        for subfolder in sorted(topic_dir.iterdir()):
            if subfolder.is_dir() and not subfolder.name.startswith('.'):
                # Recursively process subfolder
                subfolder_topics = process_topic_folder(subfolder, topic_id, folder_path)
                result_topics.extend(subfolder_topics)

        return result_topics

    for topic_dir in sorted(BOOKS_DIR.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name.startswith('.'):
            continue

        # Process this topic and its subfolders
        topic_results = process_topic_folder(topic_dir)
        topics.extend(topic_results)

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

    # Write metadata.json
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Write fresh FAILED.md (replaces previous file)
    if FAILED_BOOKS:
        FAILED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FAILED_FILE, 'w', encoding='utf-8') as f:
            f.write("# Failed Books\n\n")
            f.write(f"**Last updated:** {Path(__file__).parent.parent.name} metadata generation\n\n")
            f.write(f"**Total failures:** {len(FAILED_BOOKS)}\n\n")
            f.write("---\n\n")

            for failure in FAILED_BOOKS:
                f.write(f"## {failure['file']}\n\n")
                f.write(f"- **Type:** {failure['type']}\n")
                f.write(f"- **Error:** `{failure['error']}`\n\n")

            # Add navigation menu
            f.write("---\n\n")
            f.write("> 🤖: See [ROADMAP](ROADMAP.md) for planned features & in-progress work\n")
            f.write("> 🤖: See [CHANGELOG](CHANGELOG.md) for version history & completed features\n")
            f.write("> 🤖: See [CHECKS](CHECKS.md) for stability requirements & testing\n")
            f.write("> 👷: Consider using [/whatsup prompt](https://github.com/nonlinear/nonlinear.github.io/blob/main/.github/prompts/whatsup.prompt.md) for updates\n")

        print()
        print(f"⚠️  Failed books written to: {FAILED_FILE}")
        print(f"   Total failures: {len(FAILED_BOOKS)}")
    else:
        # Remove FAILED.md if all books processed successfully
        if FAILED_FILE.exists():
            FAILED_FILE.unlink()
            print()
            print("✅ All books processed successfully - FAILED.md removed")

    print()
    print(f"✅ Generated: {METADATA_FILE}")
    print(f"   Topics: {len(metadata['topics'])}")
    print(f"   Books: {sum(len(t['books']) for t in metadata['topics'])}")


if __name__ == "__main__":
    main()
