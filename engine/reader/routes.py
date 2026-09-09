"""
Reader routes — mounted into librarian_http.py.

Routes:
  GET /wall                    → wall page (no catalog)
  GET /reader/{book_id}        → reader shell (epub.js)
  GET /books/{book_id}.epub    → raw EPUB file (resolved via book_registry)
  GET /api/books               → JSON book list (introspection)

Responsibility: resolve book_id → filesystem path → serve.
Does NOT touch: FAISS, metadata, chunks, MCP.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import json

# Single source of truth for all runtime paths is the ConfigResolver
# (engine/config.py). routes.py must NOT keep a second env/fallback copy —
# a duplicated default is exactly what drift between reader and resolver.
from config import get_config

_cfg = get_config()
router = APIRouter()

# Resolved paths — derived by the ConfigResolver (generic defaults elsewhere).
BOOKS_DIR = _cfg.corpus_path
STATIC_DIR = _cfg.reader_static_dir
BOOK_REGISTRY_PATH = _cfg.book_registry_path

# Cache book registry on first load
_book_registry = None


def _load_book_registry() -> dict:
    """Load book_registry.json → {book_id: {title, path, author, ...}}."""
    global _book_registry
    if _book_registry is not None:
        return _book_registry
    if not BOOK_REGISTRY_PATH.exists():
        _book_registry = {}
        return _book_registry
    try:
        with open(BOOK_REGISTRY_PATH) as f:
            _book_registry = json.load(f)
    except Exception:
        _book_registry = {}
    return _book_registry


def find_book(book_id: str) -> dict | None:
    """Look up book_id in book_registry. Returns book info or None."""
    reg = _load_book_registry()
    book = reg.get(book_id)
    if book:
        return book
    # Fallback: search by path suffix (for legacy lookups)
    for bid, info in reg.items():
        if info.get("path", "").endswith(f"/{book_id}.epub"):
            return info
    return None


@router.get("/wall", response_class=HTMLResponse, include_in_schema=False)
async def wall():
    """Citation-addressed only. No catalog."""
    wall_path = STATIC_DIR / "wall.html"
    if not wall_path.exists():
        return HTMLResponse("<html><body><h1>Reader</h1><p>Citation-addressed only.</p></body></html>")
    return FileResponse(wall_path)


@router.get("/reader/{book_id}", response_class=HTMLResponse)
async def reader_shell(book_id: str):
    """Reader shell — minimal HTML, epub.js loads /books/{id}.epub, hash → CFI/href."""
    book = find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    template_path = STATIC_DIR / "reader.html"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Reader template not found")

    template = template_path.read_text()
    title = book.get("title") or Path(book.get("path", "")).stem or book_id
    html = (
        template
        .replace("{{BOOK_ID}}", book_id)
        .replace("{{BOOK_TITLE}}", title)
    )
    return HTMLResponse(html)


@router.get("/books/{book_id}.epub")
async def get_book_epub(book_id: str):
    """Serve EPUB file using book_registry → absolute path resolution."""
    # Strip .epub suffix if included
    if book_id.endswith(".epub"):
        book_id = book_id[:-5]

    book = find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    epub_path_str = book.get("path")
    if not epub_path_str:
        raise HTTPException(status_code=404, detail="Book path not found in registry")

    epub_path = Path(epub_path_str)
    # If path is relative, resolve against BOOKS_DIR
    if not epub_path.is_absolute():
        epub_path = BOOKS_DIR / epub_path

    if not epub_path.exists():
        raise HTTPException(status_code=404, detail="EPUB file not found on disk")

    return FileResponse(
        epub_path,
        media_type="application/epub+zip",
        filename=f"{book_id}.epub",
    )


@router.get("/api/books")
async def list_books():
    """Introspection endpoint. Not surfaced in UI."""
    reg = _load_book_registry()
    books = []
    for book_id, info in reg.items():
        books.append({
            "id": book_id,
            "title": info.get("title") or Path(info.get("path", "")).stem,
            "author": info.get("author", "Unknown"),
            "chunk_count": info.get("chunk_count", 0),
        })
    return {"books": books}
