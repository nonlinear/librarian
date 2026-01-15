# Storage Directory

This directory contains the MCP's persistent data:

## Files (auto-generated)

- `faiss.index` - Vector embeddings index (binary)
- `docstore.json` - Chunk-to-text mapping
- `metadata.json` - Navigation map (topics, books, tags)

## Initial Setup

This folder starts empty. Files are created automatically when you:

1. Add EPUB/PDF files to `books/`
2. Run `scripts/generate_metadata.py`
3. Run `scripts/indexer.py`

## BYOB (Bring Your Own Books)

This MCP is designed to work with **your** personal library.

The repository does not include books or indexes—you create them locally.
