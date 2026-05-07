# 📖 Test Books

Sample books for testing Librarian (all public domain).

## Included

1. **Alice's Adventures in Wonderland** (Lewis Carroll, 1865)
   - Classic children's fantasy
   - Good for testing: "rabbit hole", "mad hatter", "cheshire cat"

2. **Frankenstein** (Mary Shelley, 1818)
   - Gothic science fiction
   - Good for testing: "creature", "science", "responsibility"

3. **Moby Dick** (Herman Melville, 1851)
   - Epic whaling tale
   - Good for testing: "whale", "obsession", "revenge"

## Source

All books from [Project Gutenberg](https://www.gutenberg.org/) (public domain in the US).

## Usage

Copy to your library to test:

```bash
cp test-books/*.epub books/
```

Then query:

```bash
docker exec librarian python3 /app/engine/scripts/faiss_search.py "white whale revenge"
```

---

**Note:** These are EPUB versions with clean metadata. Perfect for testing semantic search!
