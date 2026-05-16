#!/usr/bin/env python3
"""
Librarian EPUB Reader - FastAPI Server
Serves EPUBs from /app/books with epub.js frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import os

app = FastAPI(title="Librarian Reader")

BOOKS_DIR = Path("/app/books")
INDEX_STATE_PATH = BOOKS_DIR / ".index_state.json"

# Load book index from canonical .index_state.json
def load_index():
    if not INDEX_STATE_PATH.exists():
        return {"books": []}
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
    return {"books": books}

@app.get("/")
async def root():
    return FileResponse("/app/reader/static/index.html")

@app.get("/api/books")
async def list_books():
    """List all indexed books"""
    index = load_index()
    return {
        "books": [
            {
                "id": book["id"],
                "title": book["title"],
                "author": book.get("author", "Unknown"),
                "chunk_count": book.get("chunk_count", 0)
            }
            for book in index.get("books", [])
        ]
    }

@app.get("/books/{book_id}.epub")
async def get_book_epub(book_id: str):
    """Serve EPUB file (epub.js compatible)"""
    index = load_index()
    
    # Find book path
    book = next((b for b in index.get("books", []) if b["id"] == book_id), None)
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    epub_path = Path(book["path"])
    
    if not epub_path.exists():
        raise HTTPException(status_code=404, detail="EPUB file not found")
    
    return FileResponse(
        epub_path,
        media_type="application/epub+zip",
        filename=f"{book_id}.epub"
    )

@app.get("/api/books/{book_id}")
async def get_book(book_id: str):
    """Serve EPUB file"""
    index = load_index()
    
    # Find book path
    book = next((b for b in index.get("books", []) if b["id"] == book_id), None)
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    epub_path = Path(book["path"])
    
    if not epub_path.exists():
        raise HTTPException(status_code=404, detail="EPUB file not found")
    
    return FileResponse(
        epub_path,
        media_type="application/epub+zip",
        filename=f"{book_id}.epub"
    )

@app.get("/health")
async def health():
    return {"status": "ok", "service": "librarian-reader"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("READER_PORT", "8088"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
