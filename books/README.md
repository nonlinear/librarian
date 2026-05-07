# 📚 Your Book Library

Add your EPUB and PDF files here.

## Structure

You can organize books in subfolders (optional):

```
books/
├── design/
│   ├── atomic-design.epub
│   └── design-systems.epub
├── anarchism/
│   ├── mutual-aid.epub
│   └── conquest-of-bread.epub
└── fiction/
    └── frankenstein.epub
```

Or just drop everything in the root:

```
books/
├── book1.epub
├── book2.pdf
└── book3.epub
```

**Both work!** The indexer scans recursively.

---

## Supported Formats

- ✅ **EPUB** (preferred)
- ✅ **PDF** (text-based only, no scanned images)

---

## What happens when you add a book?

1. **Watcher detects** new file (5s debounce)
2. **Indexer extracts** text (chapter-level chunks)
3. **Embeddings generated** (384-dim vectors)
4. **FAISS index updated** (append-only)
5. **MCP reloaded** (hot-reload, no restart needed)

**Total time:** <10 seconds per book.

---

## Auto-indexing

The file watcher monitors this folder automatically.

**No manual commands needed** — just drop books here and wait ~10s.

Check logs:
```bash
docker logs librarian -f
```

---

## Excluded files

These are automatically skipped:
- Files in `no-indexing/` subfolder
- Files starting with `.` or `_`
- Non-EPUB/PDF files

---

## Test it!

1. Copy a test book:
   ```bash
   cp ../test-books/alice.epub .
   ```

2. Wait ~10 seconds

3. Query it:
   ```bash
   docker exec librarian python3 /app/engine/scripts/faiss_search.py "alice wonderland rabbit"
   ```

You should see results! 🎉
