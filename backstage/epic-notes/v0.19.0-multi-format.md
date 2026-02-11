# v0.19.0 - Multi-Format Support

**Status:** 💡 PROPOSED  
**Created:** 2026-02-10

---

## Problem

**Current:** Librarian only indexes EPUB files (+ partial PDF support).

**Limitation:** Nicholas has knowledge locked in other formats:
- 📊 **Excel spreadsheets** (data, tables, calculations)
- 🔗 **Web links** (articles, docs, saved pages)
- 📽️ **PowerPoint presentations** (slides, notes, diagrams)
- 📄 **PDFs** (books, papers, manuals)

**Pain:** Can't query across all knowledge sources. Research misses relevant info in non-EPUB formats.

---

## Vision

**Librarian becomes format-agnostic:**
- Ask "what does Graeber say about debt?" → searches books + Excel notes + saved articles
- Ask "ROI calculation methods" → finds spreadsheet formulas + PowerPoint slides + EPUB passages
- Single search → all your knowledge, regardless of format

---

## Proposed Formats

### ✅ Already Supported
- **EPUB** (full support)
- **PDF** (partial - needs improvement)

### 🆕 New Formats
1. **Excel (.xlsx, .xls)**
   - Extract: Cell values, formulas, sheet names, comments
   - Index: Text content + metadata (workbook structure)
   - Use case: Financial models, data tables, notes in spreadsheets

2. **Web Links (HTML scrape + archive)**
   - Scrape URL → save HTML snapshot
   - Extract: Article text, metadata, links
   - Index: Content + URL + timestamp
   - Use case: Saved articles, documentation, blog posts
   - Storage: `library/web-archive/<domain>/<timestamp>.html`

3. **PowerPoint (.pptx, .ppt)**
   - Extract: Slide titles, text, notes, speaker notes
   - Index: Content + slide numbers + presentation metadata
   - Use case: Conference talks, presentations, visual notes

4. **Markdown (.md)**
   - Extract: Headers, paragraphs, code blocks
   - Index: Content + header hierarchy
   - Use case: Personal notes, documentation, wikis

---

## Architecture

### Unified Extraction Pipeline

```python
# engine/extractors/
base.py            # BaseExtractor interface
epub_extractor.py  # Existing EPUB logic
pdf_extractor.py   # Enhanced PDF logic
excel_extractor.py # NEW
html_extractor.py  # NEW (web archive)
pptx_extractor.py  # NEW
md_extractor.py    # NEW

# Factory pattern
def get_extractor(file_path):
    ext = Path(file_path).suffix.lower()
    return {
        '.epub': EPUBExtractor,
        '.pdf': PDFExtractor,
        '.xlsx': ExcelExtractor,
        '.html': HTMLExtractor,
        '.pptx': PowerPointExtractor,
        '.md': MarkdownExtractor,
    }[ext](file_path)
```

### Metadata Schema Extension

```json
{
  "format": "xlsx",           // NEW field
  "sheets": ["Summary", "Data"], // Excel-specific
  "formulas": 42,             // Excel-specific
  "url": "https://...",       // HTML-specific
  "archived_date": "2026-02-10", // HTML-specific
  "slides": 15                // PPTX-specific
}
```

---

## Tasks

### Phase 1: Infrastructure (Foundation)
- [ ] Design `BaseExtractor` interface (extract_text, extract_metadata)
- [ ] Refactor existing EPUB extractor to implement BaseExtractor
- [ ] Add format detection (file extension → extractor mapping)
- [ ] Update metadata.json schema (add `format` field)
- [ ] Test backward compatibility (existing EPUB indexes still work)

### Phase 2: Excel Support
- [ ] Research: `openpyxl` vs `pandas` vs `xlrd` (which library?)
- [ ] Implement `ExcelExtractor`:
  - [ ] Extract cell values (all sheets)
  - [ ] Extract formulas (as text)
  - [ ] Extract sheet names
  - [ ] Extract comments/notes
- [ ] Chunk strategy: Sheet-level? Row-level? Cell range?
- [ ] Test with real spreadsheets (financial models, data tables)
- [ ] Add Excel to `index_library.py` scan
- [ ] Update SKILL.md with Excel examples

### Phase 3: Web Link Archive
- [ ] Design archive structure (`library/web-archive/<domain>/<hash>.html`)
- [ ] Implement HTML scraper:
  - [ ] Use `requests` + `BeautifulSoup`
  - [ ] Extract article text (remove nav, ads, footers)
  - [ ] Save snapshot with metadata (URL, timestamp, title)
- [ ] Implement `HTMLExtractor`:
  - [ ] Parse saved HTML
  - [ ] Extract text content
  - [ ] Extract metadata (title, author, publish date)
- [ ] Add CLI: `librarian archive <URL>` → scrape and index
- [ ] Handle errors (404, paywall, dynamic content)
- [ ] Test with common sites (Medium, blog posts, docs)

### Phase 4: PowerPoint Support
- [ ] Research: `python-pptx` library
- [ ] Implement `PowerPointExtractor`:
  - [ ] Extract slide titles
  - [ ] Extract slide text
  - [ ] Extract speaker notes
  - [ ] Extract slide numbers
- [ ] Chunk strategy: Slide-level (one chunk per slide)
- [ ] Test with real presentations
- [ ] Add PPTX to `index_library.py` scan

### Phase 5: Markdown Support
- [ ] Implement `MarkdownExtractor`:
  - [ ] Parse with `markdown` library
  - [ ] Extract headers (hierarchy)
  - [ ] Extract paragraphs
  - [ ] Extract code blocks (optionally)
- [ ] Chunk strategy: Section-level (by headers)
- [ ] Test with personal notes, documentation
- [ ] Add MD to `index_library.py` scan

### Phase 6: PDF Enhancement
- [ ] Improve existing PDF extractor:
  - [ ] Better text extraction (handle scanned PDFs with OCR?)
  - [ ] Extract page numbers correctly
  - [ ] Handle multi-column layouts
- [ ] Test with academic papers, manuals

### Phase 7: Integration
- [ ] Update `research.py` to handle all formats
- [ ] Update citation format:
  - Excel: `[File](path) (Sheet: Summary, Row 42)`
  - HTML: `[Title](archived_path) (URL: original_url, Archived: date)`
  - PPTX: `[Presentation](path) (Slide 7)`
- [ ] Update MCP server to expose format info
- [ ] Add `--format` filter: `librarian search "query" --format xlsx`
- [ ] Test cross-format queries (books + spreadsheets + web)

### Phase 8: Documentation
- [ ] Update README with supported formats
- [ ] Add examples for each format
- [ ] Document extraction limitations (e.g., no images, no macros)
- [ ] Update SKILL.md with multi-format usage

---

## Success Criteria

- ✅ Can index and search Excel files
- ✅ Can archive and search web links
- ✅ Can index and search PowerPoint presentations
- ✅ Can index and search Markdown files
- ✅ PDF support improved (better extraction)
- ✅ Single query searches across ALL formats
- ✅ Citations include format-specific metadata
- ✅ Backward compatible (existing EPUB indexes work)

---

## Open Questions

1. **Web archive strategy:**
   - Store full HTML or just extracted text?
   - How to handle dynamic sites (JavaScript-heavy)?
   - Periodic re-scraping (detect changes)?

2. **Excel chunking:**
   - Sheet-level (one chunk per sheet)?
   - Row-level (one chunk per row)?
   - Cell range (group related cells)?

3. **Format detection:**
   - File extension only?
   - MIME type detection?
   - Content-based (magic bytes)?

4. **Dependencies:**
   - How many new Python packages? (openpyxl, beautifulsoup4, python-pptx, markdown)
   - Keep minimal or go full-featured?

5. **OCR for scanned PDFs:**
   - Add OCR support (tesseract)?
   - Or require text-based PDFs only?

---

## Dependencies

**New Python packages:**
- `openpyxl` (Excel)
- `beautifulsoup4` + `requests` (HTML scraping)
- `python-pptx` (PowerPoint)
- `markdown` (Markdown parsing)
- `pytesseract` (optional, for OCR)

**Before this epic:**
- ✅ v0.15.0 (Skill as Protocol) - refactoring done
- ✅ v0.16.0 (Unified Indexing) - single pipeline ready

---

## Related Epics

- v0.16.0: Unified Indexing Pipeline (prerequisite)
- v1.2.1: Research Enhancement (better context for all formats)
- v1.4.0: Reader Integration (may need format-specific readers)

---

## Notes

**Philosophy:** Start simple, add complexity as needed.
- Phase 1-2 (Excel) = MVP
- Phase 3 (Web) = high value
- Phase 4-5 (PPTX/MD) = nice-to-have
- Phase 6 (PDF) = polish existing

**Don't overthink.** Ship Excel support first, iterate based on usage.
