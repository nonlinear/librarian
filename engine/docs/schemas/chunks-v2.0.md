# Chunks Schema v2.0

**Purpose:** Add page/paragraph granularity to enable precise citation in research output

**Version:** 2.0
**Previous:** 1.0 (no page/para fields)

---

## Schema

```json
{
  "chunk_full": "The actual text content of the chunk...",
  "book_id": "book_slug",
  "book_title": "Book Title",
  "book_author": "Author Name",
  "topic_id": "topic_slug",
  "topic_label": "Topic Label",
  "chunk_index": 0,

  // NEW in v2.0: Source location metadata
  "filename": "Book.pdf", // Book filename (portable)
  "filetype": "pdf", // "pdf" or "epub"
  "page": 42, // PDF: page number | EPUB: null
  "chapter": "ch03", // EPUB: chapter ID | PDF: null
  "paragraph": 5 // Paragraph number within page/chapter
}
```

---

## Fields

### Existing (v1.0)

- `chunk_full`: Full text content of the chunk
- `book_id`: Slugified book identifier
- `book_title`: Human-readable book title
- `book_author`: Book author(s)
- `topic_id`: Slugified topic identifier
- `topic_label`: Human-readable topic name
- `chunk_index`: Sequential chunk number within book

### New (v2.0)

- `filename`: Book filename (portable, no paths)
- `filetype`: File format (`"pdf"` or `"epub"`)
- `page`: Page number (PDF only, null for EPUB)
- `chapter`: Chapter ID (EPUB only, null for PDF)
- `paragraph`: Paragraph number within page/chapter (both formats)

---

## Extraction Strategy

### PDF (PyPDF2 / pdfplumber)

```python
for page_num, page in enumerate(pdf.pages, start=1):
    text = page.extract_text()
    paragraphs = text.split('\n\n')  # Simple heuristic

    for para_num, para_text in enumerate(paragraphs, start=1):
        chunk_metadata = {
            "page": page_num,
            "chapter": None,
            "paragraph": para_num,
            "filetype": "pdf"
        }
```

### EPUB (ebooklib)

```python
for chapter in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    chapter_id = chapter.get_name()  # e.g., "ch03.xhtml"
    html = chapter.get_body_content()
    paragraphs = extract_paragraphs(html)  # Parse HTML

    for para_num, para_text in enumerate(paragraphs, start=1):
        chunk_metadata = {
            "page": None,
            "chapter": chapter_id,
            "paragraph": para_num,
            "filetype": "epub"
        }
```

---

## Migration

**From v1.0 → v2.0:**

- Existing chunks missing new fields → Set to `null`
- Reindexing required to populate new metadata
- Old chunks.json files will be replaced during reindexing

**Backward compatibility:** None needed (v2.0 is first modular release)

---

## Display Format

**research.py output example:**

```
📖 Bread Handbook PDF (pdf, p.42, ¶5)
   Similarity: 0.87

   "The actual text content explaining sourdough starter maintenance..."

   → books/cooking/Bread Handbook PDF.pdf
```

**Format:**

- `(pdf, p.42, ¶5)` - PDF page 42, paragraph 5
- `(epub, ch03, ¶12)` - EPUB chapter 3, paragraph 12

---

> 🤖: Part of Epic v0.5.0 Smart Indexing
> 🤖: See [v0.5.0 epic notes](../gaps/epic-notes/v0.5.0.md) for implementation details
