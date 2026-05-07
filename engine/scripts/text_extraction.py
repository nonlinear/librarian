#!/usr/bin/env python3
"""
Text Extraction Layer — EPUB/PDF → Clean Text

Extracts full text from ebooks for embedding generation.

Supports:
- EPUB (via ebooklib + BeautifulSoup)
- PDF (via PyMuPDF/fitz)

Usage:
    from text_extraction import extract_text
    
    text = extract_text("book.epub")
    chunks = chunk_text(text, size=800, overlap=100)
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

# EPUB extraction
try:
    import ebooklib
    from ebooklib import epub, ITEM_DOCUMENT
    from bs4 import BeautifulSoup
    HAS_EPUB = True
except ImportError:
    HAS_EPUB = False

# PDF extraction
try:
    import fitz  # PyMuPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


def extract_epub(path: Path) -> str:
    """
    Extract text from EPUB file.
    
    Uses ebooklib + BeautifulSoup to parse HTML content.
    
    Args:
        path: Path to EPUB file
    
    Returns:
        Full text (concatenated chapters)
    """
    if not HAS_EPUB:
        raise ImportError("ebooklib not installed. Install with: pip install ebooklib beautifulsoup4")
    
    book = epub.read_epub(str(path))
    texts = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Parse HTML content
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            
            # Remove script/style tags
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            
            if text:  # Skip empty chapters
                texts.append(text)
    
    return "\n\n".join(texts)


def extract_epub_paragraphs(path: Path) -> List[Dict[str, Any]]:
    """
    Extract paragraphs from EPUB with structural position metadata.
    
    Returns list of paragraphs with stable location info:
    [
        {
            "text": "paragraph text",
            "spine_index": 3,
            "href": "chapter1.xhtml",
            "paragraph_idx": 10,
            "element_id": "para123"  # optional, if exists in source
        },
        ...
    ]
    
    Args:
        path: Path to EPUB file
    
    Returns:
        List of paragraph dicts with location metadata
    """
    if not HAS_EPUB:
        raise ImportError("ebooklib not installed. Install with: pip install ebooklib beautifulsoup4")
    
    book = epub.read_epub(str(path))
    spine = [item for item in book.get_items_of_type(ITEM_DOCUMENT)]
    
    all_paragraphs = []
    
    for spine_index, item in enumerate(spine):
        href = item.get_name()  # e.g., "chapter1.xhtml"
        content = item.get_content()
        soup = BeautifulSoup(content, "html.parser")
        
        # Remove script/style tags
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 🔑 Extract readable elements (NOT just <p>)
        # EPUBs use: div, span, li, headings
        # ⚠️ This selector MUST match reader's querySelector!
        elements = soup.find_all([
            "p", "li", "blockquote",
            "h1", "h2", "h3"
        ])
        
        for paragraph_idx, el in enumerate(elements):
            text = el.get_text(strip=True)
            if not text:  # Skip empty elements
                continue
            
            # Capture element ID if exists (improves navigation)
            element_id = el.get("id")
            
            all_paragraphs.append({
                "text": text,
                "spine_index": spine_index,
                "href": href,
                "paragraph_idx": paragraph_idx,
                "element_id": element_id  # may be None
            })
    
    return all_paragraphs


def extract_pdf(path: Path) -> str:
    """
    Extract text from PDF file.
    
    Uses PyMuPDF (fitz) for better structure preservation than pdfminer.
    
    Args:
        path: Path to PDF file
    
    Returns:
        Full text (concatenated pages)
    """
    if not HAS_PDF:
        raise ImportError("pymupdf not installed. Install with: pip install pymupdf")
    
    doc = fitz.open(str(path))
    texts = []
    
    for page in doc:
        text = page.get_text()
        if text.strip():  # Skip blank pages
            texts.append(text)
    
    doc.close()
    
    return "\n\n".join(texts)


def extract_pdf_paragraphs(path: Path) -> List[Dict[str, Any]]:
    """
    Extract paragraphs from PDF with page numbers.
    
    Returns list of paragraphs with page metadata:
    [
        {
            "text": "paragraph text",
            "page": 42,
            "paragraph_idx": 3
        },
        ...
    ]
    
    Note: Chunks never cross page boundaries.
    
    Args:
        path: Path to PDF file
    
    Returns:
        List of paragraph dicts with page metadata
    """
    if not HAS_PDF:
        raise ImportError("pymupdf not installed. Install with: pip install pymupdf")
    
    doc = fitz.open(str(path))
    all_paragraphs = []
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if not text.strip():  # Skip blank pages
            continue
        
        # Split by double newline (paragraph heuristic)
        # ⚠️ This is approximate — PDFs don't have semantic structure
        paragraphs = text.split("\n\n")
        
        for paragraph_idx, para_text in enumerate(paragraphs):
            para_text = para_text.strip()
            if not para_text:  # Skip empty
                continue
            
            all_paragraphs.append({
                "text": para_text,
                "page": page_num,
                "paragraph_idx": paragraph_idx
            })
    
    doc.close()
    
    return all_paragraphs


def extract_text(path: Path) -> str:
    """
    Extract text from EPUB or PDF file.
    
    Auto-detects file type based on extension.
    
    Args:
        path: Path to book file (.epub or .pdf)
    
    Returns:
        Extracted text (full book)
    
    Raises:
        ValueError: Unsupported file type
        ImportError: Required library not installed
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    ext = path.suffix.lower()
    
    if ext == '.epub':
        return extract_epub(path)
    elif ext == '.pdf':
        return extract_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .epub, .pdf")


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Overlap prevents cutting sentences/paragraphs awkwardly.
    
    Args:
        text: Full text to chunk
        size: Target chunk size (characters)
        overlap: Overlap between chunks (characters)
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    i = 0
    
    while i < len(text):
        chunk = text[i:i + size]
        chunks.append(chunk)
        i += size - overlap
    
    return chunks


def chunk_paragraphs(paragraphs: List[Dict[str, Any]], max_chars: int = 1024) -> List[Dict[str, Any]]:
    """
    Group paragraphs into chunks (~1024 chars).
    
    Preserves paragraph boundaries (no mid-paragraph cuts).
    Each chunk contains:
    {
        "text": "combined text",
        "paragraphs": [
            {"idx": 10, "text": "...", "element_id": "..." (epub)},
            {"idx": 11, "text": "...", "page": 42 (pdf)}
        ],
        "source": {
            "type": "epub",
            "spine_index": 3,
            "href": "chapter1.xhtml"
        }  # OR {"type": "pdf"} for PDF
    }
    
    Args:
        paragraphs: List of paragraph dicts from extract_epub_paragraphs() or extract_pdf_paragraphs()
        max_chars: Target chunk size (soft limit)
    
    Returns:
        List of chunk dicts
    """
    if not paragraphs:
        return []
    
    # Determine source type from first paragraph
    first_para = paragraphs[0]
    is_epub = "spine_index" in first_para
    
    chunks = []
    current_chunk = {
        "text": "",
        "paragraphs": [],
        "source": {}
    }
    
    for para in paragraphs:
        # Would adding this paragraph exceed limit?
        if current_chunk["text"] and len(current_chunk["text"]) + len(para["text"]) > max_chars:
            # Save current chunk (if not empty)
            if current_chunk["paragraphs"]:
                chunks.append(current_chunk)
            
            # Start new chunk
            current_chunk = {
                "text": "",
                "paragraphs": [],
                "source": {}
            }
        
        # Add paragraph to chunk
        current_chunk["text"] += para["text"] + "\n"
        
        # Build paragraph metadata
        para_meta = {
            "idx": para["paragraph_idx"],
            "text": para["text"]
        }
        
        if is_epub:
            # EPUB metadata
            para_meta["element_id"] = para.get("element_id")
            current_chunk["source"] = {
                "type": "epub",
                "spine_index": para["spine_index"],
                "href": para["href"]
            }
        else:
            # PDF metadata
            para_meta["page"] = para["page"]
            current_chunk["source"] = {
                "type": "pdf"
            }
        
        current_chunk["paragraphs"].append(para_meta)
    
    # Save final chunk
    if current_chunk["paragraphs"]:
        chunks.append(current_chunk)
    
    return chunks


def extract_and_chunk(path: Path, chunk_size: int = 800, chunk_overlap: int = 100) -> dict:
    """
    Extract text from book and chunk it (one-step helper).
    
    Args:
        path: Path to book file
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
    
    Returns:
        Dict with 'text' (full) and 'chunks' (list)
    """
    text = extract_text(path)
    chunks = chunk_text(text, size=chunk_size, overlap=chunk_overlap)
    
    return {
        "path": str(path),
        "filename": path.name,
        "text": text,
        "chunks": chunks,
        "chunk_count": len(chunks),
        "total_chars": len(text)
    }


# Test/demo
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python text_extraction.py <book.epub|book.pdf>")
        sys.exit(1)
    
    book_path = Path(sys.argv[1])
    
    print(f"\n📖 Extracting text from: {book_path.name}")
    print("─" * 60)
    
    try:
        result = extract_and_chunk(book_path)
        
        print(f"✅ Extracted {result['total_chars']:,} characters")
        print(f"✅ Split into {result['chunk_count']} chunks")
        print(f"\n📝 First 500 characters:\n")
        print(result['text'][:500])
        print("\n...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
