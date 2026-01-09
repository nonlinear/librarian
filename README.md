# Literature RAG (2026)

Minimal, manual workflow for local book retrieval and question-answering.

## How it works

1. Place `.epub` or `.pdf` files in a folder under `books/` (e.g., `books/urbanism/`).
2. Use one of the three prompts/scripts:
   - **update_literature**: Index only new/unindexed books and update `.rag-topics`.
   - **reindex_all_books**: Delete the index and reindex everything from scratch.
   - **literature (query)**: Ask questions to your indexed books.

No watcher, no Hammerspoon, no file monitoring. All updates are manual and reliable.

## Requirements

- Python 3.11+
- llama-index
- ebooklib
- beautifulsoup4
- google-generativeai (Gemini API)
- pymupdf (for PDF support)
- Gemini API key in `.env`

## Usage

1. Add or remove `.epub` or `.pdf` files in `books/`.
2. Run:

   ```sh
   /opt/homebrew/bin/python3.11 scripts/update_literature.py
   ```

   Only new books will be indexed. To force a full rebuild, run:

   ```sh
   /opt/homebrew/bin/python3.11 scripts/reindex_all_books.py
   ```

3. Use the literature prompt to query your books.

## Prompts

- **update_literature**: Index new books and update topics. Reports new books and total cost.
- **reindex_all_books**: Rebuild the entire index from scratch.
- **literature**: Query your indexed books.

---
