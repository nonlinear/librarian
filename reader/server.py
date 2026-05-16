#!/usr/bin/env python3
"""
Librarian Reader — citation-addressed EPUB viewer.

Routes:
  GET /                       → wall page (no catalog)
  GET /book/{book_id}         → reader shell (epub.js)
  GET /books/{book_id}.epub   → raw EPUB file
  GET /api/books              → JSON book list (introspection)
  GET /health                 → liveness

Not a library app. Not a catalog. Just the page.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import json
import os

app = FastAPI(title="Librarian Reader")

BOOKS_DIR = Path("/app/books")
STATIC_DIR = Path("/app/reader/static")
INDEX_STATE_PATH = BOOKS_DIR / ".index_state.json"


def load_books():
    """Read canonical .index_state.json → list of {id, title, author, path}."""
    if not INDEX_STATE_PATH.exists():
        return []
    with open(INDEX_STATE_PATH) as f:
        state = json.load(f)
    books = []
    for book_hash, book in state.get("books", {}).items():
        books.append({
            "id": book_hash,
            "title": book.get("title") or Path(book["path"]).stem,
            "author": book.get("author", "Unknown"),
            "path": book["path"],
            "chunk_count": book.get("chunk_count", 0),
        })
    return books


def find_book(book_id: str):
    for b in load_books():
        if b["id"] == book_id:
            return b
    return None


@app.get("/", response_class=HTMLResponse)
async def wall():
    """Citation-addressed only. No catalog."""
    return FileResponse(STATIC_DIR / "wall.html")


@app.get("/book/{book_id}", response_class=HTMLResponse)
async def reader_shell(book_id: str):
    """Reader shell — minimal HTML, epub.js loads /books/{id}.epub, hash → CFI/href."""
    book = find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    template = (STATIC_DIR / "reader.html").read_text()
    html = (
        template
        .replace("{{BOOK_ID}}", book_id)
        .replace("{{BOOK_TITLE}}", book["title"])
    )
    return HTMLResponse(html)


@app.get("/books/{book_id}.epub")
async def get_book_epub(book_id: str):
    """Serve EPUB file (epub.js fetches this)."""
    book = find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    epub_path = Path(book["path"])
    if not epub_path.exists():
        raise HTTPException(status_code=404, detail="EPUB file not found")
    return FileResponse(
        epub_path,
        media_type="application/epub+zip",
        filename=f"{book_id}.epub",
    )


@app.get("/api/books")
async def list_books():
    """Introspection endpoint. Not surfaced in UI."""
    return {
        "books": [
            {k: b[k] for k in ("id", "title", "author", "chunk_count")}
            for b in load_books()
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "librarian-reader"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("READER_PORT", "8088"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
