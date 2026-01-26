#!/usr/bin/env python3
"""
Index books using LlamaIndex + local sentence-transformers embeddings
V2.0: Per-topic metadata + page/paragraph extraction

Usage:
    python indexer.py [topic_id]           # Index one topic
    python indexer.py --all                # Index all topics
    python indexer.py --topics cooking ai_policy  # Index specific topics
"""

import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import EpubReader, PyMuPDFReader

# PDF/EPUB processing
try:
    from PyPDF2 import PdfReader
    HAS_PDF = True
except ImportError:
    print("⚠️  PyPDF2 not installed. PDF page extraction disabled.")
    print("   Install with: pip install PyPDF2")
    HAS_PDF = False

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    HAS_EPUB = True
except ImportError:
    print("⚠️  ebooklib/beautifulsoup4 not installed. EPUB chapter extraction disabled.")
    print("   Install with: pip install ebooklib beautifulsoup4")
    HAS_EPUB = False

# Setup local embeddings
MODELS_DIR = Path(__file__).parent.parent / "models"

# Available models
EMBEDDING_MODELS = {
    "minilm": {
        "name": "BAAI/bge-small-en-v1.5",
        "dim": 384,
        "desc": "Fast, lightweight (90MB)"
    },
    "bge": {
        "name": "BAAI/bge-small-en-v1.5",
        "dim": 384,
        "desc": "Better quality, slower (~130MB)"
    }
}

# Default model (will be set in main)
embed_model = None

# Node parser for chunking raw documents
node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)

# Paths
LIBRARY_ROOT = Path(__file__).parent.parent / "books"
MAIN_METADATA = LIBRARY_ROOT / ".library-index.json"

# Readers
epub_reader = EpubReader()
pdf_reader = PyMuPDFReader()


def extract_pdf_paragraphs(pdf_path: Path) -> List[Tuple[str, int, int]]:
    """
    Extract paragraphs from PDF with page numbers

    Returns:
        List of (text, page_num, para_num) tuples
    """
    if not HAS_PDF:
        return []

    paragraphs = []

    try:
        reader = PdfReader(str(pdf_path))

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            # Split by double newlines (simple heuristic for paragraphs)
            paras = [p.strip() for p in text.split('\n\n') if p.strip()]

            for para_num, para_text in enumerate(paras, start=1):
                paragraphs.append((para_text, page_num, para_num))

    except Exception as e:
        print(f"      ⚠️  PDF extraction failed: {e}")
        return []

    return paragraphs


def extract_epub_paragraphs(epub_path: Path) -> List[Tuple[str, str, int]]:
    """
    Extract paragraphs from EPUB with chapter IDs

    Returns:
        List of (text, chapter_id, para_num) tuples
    """
    if not HAS_EPUB:
        return []

    paragraphs = []

    try:
        book = epub.read_epub(str(epub_path))

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            chapter_id = item.get_name()  # e.g., "ch03.xhtml"
            html_content = item.get_body_content()

            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract paragraphs (p tags)
            paras = soup.find_all('p')

            for para_num, para_tag in enumerate(paras, start=1):
                para_text = para_tag.get_text().strip()
                if para_text:
                    paragraphs.append((para_text, chapter_id, para_num))

    except Exception as e:
        print(f"      ⚠️  EPUB extraction failed: {e}")
        return []

    return paragraphs


def load_book_with_metadata(book_path: Path, book_meta: Dict, topic_id: str, topic_label: str) -> Tuple[List[Document], List[Dict]]:
    """
    Load book and extract page/paragraph metadata

    Returns:
        (documents, chunks_metadata) tuple
    """
    filetype = book_meta['filetype']
    documents = []
    chunks_metadata = []

    if filetype == 'pdf':
        paragraphs = extract_pdf_paragraphs(book_path)

        for text, page_num, para_num in paragraphs:
            doc = Document(text=text)
            doc.metadata = {
                'book_id': book_meta['id'],
                'book_title': book_meta['title'],
                'book_author': book_meta['author'],
                'topic_id': topic_id,
                'topic_label': topic_label,
                'filename': book_meta['filename'],
                'filetype': 'pdf',
                'page': page_num,
                'chapter': None,
                'paragraph': para_num
            }
            documents.append(doc)

            # Store for chunks.json
            chunks_metadata.append({
                'chunk_full': text,
                'book_id': book_meta['id'],
                'book_title': book_meta['title'],
                'book_author': book_meta['author'],
                'topic_id': topic_id,
                'topic_label': topic_label,
                'chunk_index': len(chunks_metadata),
                'filename': book_meta['filename'],
                'filetype': 'pdf',
                'page': page_num,
                'chapter': None,
                'paragraph': para_num
            })

    elif filetype == 'epub':
        paragraphs = extract_epub_paragraphs(book_path)

        for text, chapter_id, para_num in paragraphs:
            doc = Document(text=text)
            doc.metadata = {
                'book_id': book_meta['id'],
                'book_title': book_meta['title'],
                'book_author': book_meta['author'],
                'topic_id': topic_id,
                'topic_label': topic_label,
                'filename': book_meta['filename'],
                'filetype': 'epub',
                'page': None,
                'chapter': chapter_id,
                'paragraph': para_num
            }
            documents.append(doc)

            # Store for chunks.json
            chunks_metadata.append({
                'chunk_full': text,
                'book_id': book_meta['id'],
                'book_title': book_meta['title'],
                'book_author': book_meta['author'],
                'topic_id': topic_id,
                'topic_label': topic_label,
                'chunk_index': len(chunks_metadata),
                'filename': book_meta['filename'],
                'filetype': 'epub',
                'page': None,
                'chapter': chapter_id,
                'paragraph': para_num
            })

    return documents, chunks_metadata


def compute_content_hash(topic_path: Path) -> str:
    """Hash folder contents: filenames + mtimes"""
    files = sorted([
        f for f in os.listdir(topic_path)
        if f.endswith(('.pdf', '.epub'))
    ])

    hash_input = []
    for filename in files:
        filepath = topic_path / filename
        mtime = os.path.getmtime(filepath)
        hash_input.append(f"{filename}:{mtime}")

    combined = '|'.join(hash_input)
    return hashlib.sha256(combined.encode()).hexdigest()


def bootstrap_topic_metadata(topic_data: Dict) -> bool:
    """
    Create/update topic-index.json with book list only (no embedding/indexing)
    Useful for initializing metadata structure before full indexing

    Returns:
        True if successful, False if failed
    """
    topic_id = topic_data['id']
    topic_path = LIBRARY_ROOT / topic_data['path']
    metadata_file = topic_path / ".topic-index.json"

    print(f"📋 {topic_id}")

    # Ensure topic directory exists
    topic_path.mkdir(parents=True, exist_ok=True)

    # Scan for books
    books = []
    for ext in ['*.epub', '*.pdf']:
        for book_path in topic_path.glob(ext):
            # Skip metadata files
            if book_path.name in ['.chunks.json', '.topic-index.json', '.faiss.index']:
                continue

            book_id = book_path.stem.lower().replace(' ', '_')
            mtime = os.path.getmtime(book_path)

            books.append({
                'id': book_id,
                'title': book_path.stem,
                'filename': book_path.name,
                'author': 'Unknown',
                'tags': [],
                'last_modified': mtime
            })

    # Create or update metadata
    topic_meta = {
        "schema_version": "2.0",
        "topic_id": topic_id,
        "embedding_model": "pending",  # Will be set during actual indexing
        "chunk_settings": {
            "size": 1024,
            "overlap": 200
        },
        "last_indexed_at": None,
        "content_hash": None,
        "books": books
    }

    # Save
    with open(metadata_file, 'w') as f:
        json.dump(topic_meta, f, indent=2)

    print(f"   ✓ {len(books)} books registered")
    return True


def detect_file_changes(library_root: Path, registry: Dict) -> set:
    """
    Detect which topics have new/modified files
    Returns set of topic paths that need reindexing

    More granular than hash-based detection:
    - Checks individual file mtimes vs topic-index.json
    - Returns only affected topics
    """
    affected_topics = set()

    for topic in registry.get('topics', []):
        topic_path_str = topic['path']
        topic_dir = library_root / topic_path_str
        topic_index = topic_dir / '.topic-index.json'

        if not topic_index.exists():
            # No index yet, needs indexing
            affected_topics.add(topic_path_str)
            continue

        with open(topic_index, 'r') as f:
            topic_data = json.load(f)

        # Build map of filename -> last_modified from index
        indexed_files = {
            book['filename']: book.get('last_modified')
            for book in topic_data.get('books', [])
        }

        # Check all PDF/EPUB files in topic directory
        has_changes = False
        for ext in ['*.epub', '*.pdf']:
            for filepath in topic_dir.glob(ext):
                filename = filepath.name

                # Skip hidden/system files
                if filename.startswith('.'):
                    continue

                # New file not in index
                if filename not in indexed_files:
                    has_changes = True
                    break

                # Modified file (mtime > last_modified in index)
                file_mtime = os.path.getmtime(filepath)
                indexed_mtime = indexed_files[filename]

                if indexed_mtime is None or file_mtime > indexed_mtime:
                    has_changes = True
                    break

            if has_changes:
                break

        if has_changes:
            affected_topics.add(topic_path_str)

    return affected_topics


def index_topic(topic_data: Dict, registry: Dict, force: bool = False) -> bool:
    """
    Index a single topic

    Args:
        topic_data: Topic entry from registry
        registry: Main metadata.json content
        force: If True, skip delta detection and always reindex

    Returns:
        True if successful, False if failed
    """
    topic_id = topic_data['id']
    topic_path = LIBRARY_ROOT / topic_data['path']
    metadata_file = topic_path / ".topic-index.json"

    print(f"\n{'='*60}")
    print(f"📖 Indexing: {topic_id}")
    print(f"   Path: {topic_path.relative_to(LIBRARY_ROOT.parent)}")
    print(f"{'='*60}")

    # 1. Load or create per-topic metadata
    if not metadata_file.exists():
        # Create minimal topic-index.json for force mode
        topic_meta = {
            "schema_version": "2.0",
            "topic_id": topic_id,
            "embedding_model": embed_model.model_name.split('/')[-1],
            "chunk_settings": {
                "size": Settings.chunk_size,
                "overlap": Settings.chunk_overlap
            },
            "last_indexed_at": None,
            "content_hash": None,
            "books": []
        }
        print(f"   💡 Creating new topic-index.json")
    else:
        with open(metadata_file, 'r') as f:
            topic_meta = json.load(f)

    books_count = len(topic_meta['books'])
    print(f"   📚 Books: {books_count}")

    # 2. Delta detection (skip if --force)
    if not force:
        current_hash = compute_content_hash(topic_path)
        stored_hash = topic_meta.get('content_hash')

        if current_hash == stored_hash and stored_hash is not None:
            print(f"   ⏭️  No changes detected (hash match)")
            print(f"   💡 Use --force to reindex anyway")
            return True

        if stored_hash:
            print(f"   🔄 Changes detected (hash mismatch)")
        else:
            print(f"   🆕 First indexing (no hash stored)")

    # 2. Load all raw documents
    raw_documents = []
    failed_books = []

    for book in topic_meta['books']:
        book_path = topic_path / book['filename']

        if not book_path.exists():
            print(f"      ⚠️  Not found: {book['filename']}")
            failed_books.append({
                'filename': book['filename'],
                'error': 'File not found'
            })
            continue

        print(f"      Loading: {book['title']}")

        try:
            # Detect file type and load
            file_ext = book_path.suffix.lower()

            if file_ext == '.epub':
                docs = epub_reader.load_data(str(book_path))
            elif file_ext == '.pdf':
                docs = pdf_reader.load_data(str(book_path))
            else:
                print(f"         ⚠️  Unsupported: {file_ext}")
                continue

            # Add metadata to raw documents
            for doc in docs:
                doc.metadata = {
                    'book_id': book['id'],
                    'book_title': book['title'],
                    'book_author': book.get('author', 'Unknown'),
                    'topic_id': topic_id,
                    'topic_folder': topic_data['path'],
                    'tags': ','.join(book.get('tags', []))
                }

            raw_documents.extend(docs)
            print(f"         ✓ {len(docs)} raw docs")

        except Exception as e:
            print(f"         ❌ Error: {e}")
            failed_books.append({
                'filename': book['filename'],
                'error': str(e)
            })

    if not raw_documents:
        print(f"   ❌ No documents loaded")
        return False

    # 3. Apply chunking to raw documents
    print(f"\n   ✂️  Chunking {len(raw_documents)} raw docs...")
    nodes = node_parser.get_nodes_from_documents(raw_documents)
    print(f"   📝 Generated {len(nodes)} chunks")

    if not nodes:
        print(f"   ❌ No chunks generated")
        return False

    # 4. Build embeddings manually (no VectorStoreIndex needed)
    print(f"\n   🔨 Generating embeddings...")

    try:
        import numpy as np
        import faiss
        from sentence_transformers import SentenceTransformer

        # Use configured embedding model from Settings
        model_name = Settings.embed_model.model_name
        model = SentenceTransformer(model_name, cache_folder=str(MODELS_DIR))

        texts = [node.text for node in nodes]
        embeddings_list = model.encode(texts, show_progress_bar=True, batch_size=32)
        print(f"      ✓ Embeddings generated")
    except Exception as e:
        print(f"      ❌ Indexing failed: {e}")
        return False

    # 5. Save to topic folder
    print(f"\n   💾 Saving...")

    # Build and save FAISS index
    faiss_path = topic_path / ".faiss.index"
    try:
        embeddings_array = np.array(embeddings_list, dtype=np.float32)
        dimension = embeddings_array.shape[1]

        faiss_index = faiss.IndexFlatL2(dimension)
        faiss_index.add(embeddings_array)

        faiss.write_index(faiss_index, str(faiss_path))
        print(f"      ✓ {faiss_path.name}")
    except Exception as e:
        print(f"      ❌ Failed to save index: {e}")
        return False

    # Save chunks.json
    chunks_file = topic_path / ".chunks.json"
    chunks_list = []
    for i, node in enumerate(nodes):
        chunks_list.append({
            'chunk_full': node.text,
            'book_id': node.metadata.get('book_id'),
            'book_title': node.metadata.get('book_title'),
            'book_author': node.metadata.get('book_author'),
            'topic_id': node.metadata.get('topic_id'),
            'topic_folder': node.metadata.get('topic_folder'),
            'chunk_index': i
        })

    try:
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_list, f, ensure_ascii=False, indent=2)
        print(f"      ✓ {chunks_file.name} ({len(chunks_list)} chunks)")
    except Exception as e:
        print(f"      ❌ Failed to save chunks: {e}")
        return False

    # 5. Update topic metadata
    topic_meta['last_indexed_at'] = time.time()
    topic_meta['content_hash'] = compute_content_hash(topic_path)

    with open(metadata_file, 'w') as f:
        json.dump(topic_meta, f, indent=2)

    print(f"      ✓ {metadata_file.name} updated")

    # 6. Report failures
    if failed_books:
        print(f"\n   ⚠️  {len(failed_books)} book(s) failed:")
        for book in failed_books:
            print(f"      • {book['filename']}: {book['error']}")

    print(f"\n   ✅ Topic indexed successfully")
    return True


def main():
    parser = argparse.ArgumentParser(description='Index books with v2.0 metadata')
    parser.add_argument('topics', nargs='*', help='Topic IDs to index')
    parser.add_argument('--all', action='store_true', help='Index all topics (with hash-based delta detection)')
    parser.add_argument('--smart', action='store_true', help='Smart mode: detect file changes and only reindex affected topics')
    parser.add_argument('--bootstrap', action='store_true', help='Only create/update topic-index.json files (no embedding/indexing)')
    parser.add_argument('--topic', help='Index specific topic (e.g., theory/anthropocene)')
    parser.add_argument('--force', action='store_true', help='Force reindex (skip delta detection)')
    parser.add_argument('--topics', dest='topic_list', nargs='+', help='List of topic IDs')
    parser.add_argument('--model', choices=['minilm', 'bge'], default='bge',
                        help='Embedding model: bge (better quality, default) or minilm (faster)')

    args = parser.parse_args()

    # Setup embedding model
    global embed_model
    model_config = EMBEDDING_MODELS[args.model]
    embed_model = HuggingFaceEmbedding(
        model_name=model_config["name"],
        cache_folder=str(MODELS_DIR)
    )
    Settings.embed_model = embed_model
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 200

    print("🚀 Librarian Indexer v2.0")
    print("=" * 60)
    print(f"✓ Model: {args.model} - {model_config['desc']}")
    print(f"✓ Embedding: {model_config['name']} ({model_config['dim']}-dim)")
    print("✓ Chunking: 1024 chars, 200 overlap")
    print("✓ Schema: chunks.json v2.0 (page/paragraph metadata)")

    # Load registry
    if not MAIN_METADATA.exists():
        print(f"\n❌ Registry not found: {MAIN_METADATA}")
        print(f"💡 Run migrate_to_v2.py first")
        return 1

    with open(MAIN_METADATA, 'r') as f:
        registry = json.load(f)

    # Bootstrap mode: just create/update topic-index.json files
    if args.bootstrap:
        print(f"\n🏗️  Bootstrap mode: Creating/updating topic-index.json files...")
        print(f"   (No embedding or indexing will be performed)\n")

        topics_to_bootstrap = registry['topics']
        success_count = 0

        for topic in topics_to_bootstrap:
            if bootstrap_topic_metadata(topic):
                success_count += 1

        print(f"\n{'='*60}")
        print(f"✅ Bootstrap Complete")
        print(f"{'='*60}")
        print(f"   Created/updated: {success_count}/{len(topics_to_bootstrap)} topics")
        print(f"\n💡 Run without --bootstrap to perform full indexing")
        return 0

    # Default to smart mode if no mode specified
    if not (args.smart or args.all or args.topic or args.topic_list or args.topics):
        args.smart = True
        print(f"\n💡 No mode specified, defaulting to --smart")

    # Determine which topics to index
    if args.smart:
        # Smart mode: detect file-level changes
        print(f"\n🧠 Smart mode: Detecting file changes...")
        affected_topic_paths = detect_file_changes(LIBRARY_ROOT, registry)

        if not affected_topic_paths:
            print(f"\n✅ No changes detected - nothing to reindex!")
            return 0

        topics_to_index = [t for t in registry['topics'] if t['path'] in affected_topic_paths]

        print(f"\n📊 Changes detected in {len(topics_to_index)} topics:")
        for topic in topics_to_index:
            print(f"   • {topic['path']}")

        # Force reindex affected topics
        args.force = True

    elif args.all:
        topics_to_index = registry['topics']
        print(f"\n📋 Indexing all {len(topics_to_index)} topics")
    elif args.topic:
        # Single topic via --topic flag (supports paths like theory/anthropocene)
        topics_to_index = [t for t in registry['topics'] if t['path'] == args.topic]
        if not topics_to_index:
            print(f"\n❌ Topic '{args.topic}' not found")
            return 1
        print(f"\n📋 Indexing topic: {args.topic}")
    elif args.topic_list:
        topic_ids = args.topic_list
        topics_to_index = [t for t in registry['topics'] if t['id'] in topic_ids]
        print(f"\n📋 Indexing {len(topics_to_index)} topics: {', '.join(topic_ids)}")
    elif args.topics:
        topic_ids = args.topics
        topics_to_index = [t for t in registry['topics'] if t['id'] in topic_ids]
        print(f"\n📋 Indexing {len(topics_to_index)} topics: {', '.join(topic_ids)}")
    else:
        print(f"\n❌ No topics specified")
        print(f"💡 Usage:")
        print(f"   python indexer_v2.py --all                       # Index all (delta detection)")
        print(f"   python indexer_v2.py --topic theory/anthropocene # Index one topic")
        print(f"   python indexer_v2.py --force --all               # Force reindex all")
        print(f"   python indexer_v2.py cooking ai_policy           # Index multiple topics")
        return 1

    # Index topics
    results = {
        'success': [],
        'failed': []
    }

    for topic in topics_to_index:
        success = index_topic(topic, registry, force=args.force)  # Use --force flag
        if success:
            results['success'].append(topic['id'])
        else:
            results['failed'].append(topic['id'])

    # Update library-index.json with embedding model
    if not args.bootstrap and results['success']:
        registry['embedding_model'] = embed_model.model_name.split('/')[-1]
        with open(MAIN_METADATA, 'w') as f:
            json.dump(registry, f, indent=2)
        print(f"\n📝 Updated library-index.json with model: {registry['embedding_model']}")

    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 Indexing Complete")
    print(f"{'='*60}")
    print(f"\n📊 Summary:")
    print(f"   ✅ Success: {len(results['success'])} topics")
    if results['failed']:
        print(f"   ❌ Failed: {len(results['failed'])} topics")
        for topic_id in results['failed']:
            print(f"      • {topic_id}")

    return 0 if not results['failed'] else 1


if __name__ == "__main__":
    exit(main())
