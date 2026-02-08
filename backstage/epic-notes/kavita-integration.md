# Kavita Integration - Book Linking System

**Epic:** Librarian skill enhancement  
**Goal:** When searching books via librarian, provide direct "Open in Kavita" links  
**Status:** ✅ Working (2026-02-05)

---

## Overview

**Problem:** Librarian skill searches PDFs/EPUBs in `~/Documents/librarian/`, but Nicholas has to manually find the book in Kavita to read it.

**Solution:** Auto-generate Kavita reader URLs so clicking a link opens the book directly.

---

## Architecture

### Data Flow:
```
~/Documents/librarian/  →  Syncthing  →  NAS:/books/  →  Kavita scans  →  Database
                                                                              ↓
User asks about book  →  Librarian searches  →  kavita-link.py  →  API lookup  →  URL
                                                                              ↓
                                                                    Open in browser
```

### Components:
1. **Syncthing** — syncs `~/Documents/librarian/` → NAS `/books/`
2. **Kavita** — scans `/books/`, creates database with IDs
3. **kavita-link.py** — Python script that maps book title → Kavita URL
4. **Librarian skill** — will include Kavita links in search results

---

## Kavita URL Structure

### Correct format:
```
http://192.168.1.152:5000/library/{libraryId}/series/{seriesId}/book/{chapterId}
```

### Example:
```
http://192.168.1.152:5000/library/1/series/522/book/934
```

**Parameters:**
- `libraryId` — Library ID (e.g., 1 = "Literature")
- `seriesId` — Unique ID for the book/series
- `chapterId` — Unique ID for the chapter/file (NOT volumeId!)

---

## API Endpoints Used

### 1. Login
```bash
POST http://192.168.1.152:5000/api/account/login
Content-Type: application/json

{
  "username": "nonlinear",
  "password": "#0uFyfT4K6$rwAJA8cGb"
}

# Returns JWT token
```

### 2. Search for book
```bash
GET http://192.168.1.152:5000/api/search/search?queryString=Molecular%20Red
Authorization: Bearer {token}

# Returns:
{
  "series": [
    {
      "seriesId": 522,
      "name": "Molecular Red: Theory for the Anthropocene",
      "libraryId": 1,
      ...
    }
  ]
}
```

### 3. Get chapters
```bash
GET http://192.168.1.152:5000/api/series/volumes?seriesId=522
Authorization: Bearer {token}

# Returns:
[
  {
    "id": 528,  // volumeId (DON'T USE IN URL!)
    "chapters": [
      {
        "id": 934,  // chapterId (USE THIS!)
        "title": "Molecular Red: Theory for the Anthropocene",
        "files": [
          {
            "filePath": "/books/theory/anthropocene/Molecular Red.epub"
          }
        ]
      }
    ]
  }
]
```

### 4. Construct URL
```
http://192.168.1.152:5000/library/1/series/522/book/934
                                    ↑          ↑         ↑
                                 libId    seriesId  chapterId
```

---

## Common Mistakes (Lessons Learned)

### ❌ WRONG:
```
http://192.168.1.152:5000/library/1/series/522/manga/528
                                                 ↑     ↑
                                            Wrong!  volumeId (wrong!)
```

**Why wrong:**
- Used `/manga/` instead of `/book/`
- Used `volumeId` (528) instead of `chapterId` (934)

### ✅ RIGHT:
```
http://192.168.1.152:5000/library/1/series/522/book/934
                                                ↑    ↑
                                            Correct! chapterId
```

**Key insight:**
- Kavita has **volumes** → contain **chapters**
- URL uses **chapterId**, NOT volumeId
- Get chapterId from: `volumes[0].chapters[0].id`

---

## Implementation: kavita-link.py

**Location:** `~/.openclaw/workspace/kavita-link.py`

**Usage:**
```bash
python3 ~/.openclaw/workspace/kavita-link.py "Molecular Red"
# Output:
# 📚 Molecular Red: Theory for the Anthropocene
# 🔗 http://192.168.1.152:5000/library/1/series/522/book/934

python3 ~/.openclaw/workspace/kavita-link.py "~/Documents/librarian/theory/anthropocene/Molecular Red.pdf"
# (Also works with file paths)
```

**How it works:**
1. Extract title from input (filename or raw title)
2. Login to Kavita API → get JWT token
3. Search for book by title
4. Get first result's `seriesId` and `libraryId`
5. Fetch volumes → get first chapter's `chapterId`
6. Construct URL: `http://.../library/{lib}/series/{series}/book/{chapter}`

---

## Maintenance: Zero Required! 🎉

### Why it's stable:

**✅ No manual mapping needed**
- Search API finds book by title dynamically
- No lookup tables to maintain

**✅ IDs are persistent**
- Once Kavita scans a book, IDs stay the same
- Only change if you delete/recreate library (rare)

**✅ Title is primary key**
- Kavita indexes by filename + metadata
- Search handles fuzzy matching
- "Molecular Red" finds "Molecular Red: Theory for the Anthropocene"

### When IDs might change:
- ❌ Delete library and recreate
- ❌ Move to different Kavita server
- ❌ Rename file (might create duplicate entry)

**Solution:** If IDs change, search API still works! Just re-run lookup.

---

## Testing Results

### Test 1: Molecular Red ✅
```
Input: "Molecular Red"
Output: http://192.168.1.152:5000/library/1/series/522/book/934
Expected: http://192.168.1.152:5000/library/1/series/522/book/934
Status: ✅ MATCH
```

### Test 2: Heavenly Tyrant ✅
```
Input: "Heavenly Tyrant"
Output: http://192.168.1.152:5000/library/1/series/511/book/932
Expected: http://192.168.1.152:5000/library/1/series/511/book/932
Status: ✅ MATCH
```

### Test 3: I Ching ✅
```
Input: "I Ching"
Output: http://192.168.1.152:5000/library/1/series/635/book/885
Status: ✅ Works (not manually verified yet)
```

---

## Edge Cases & Solutions

### 1. Multiple books with similar titles
```python
# Example: "Introduction" returns 50 results
# Solution: Return top 3 + let user choose, or add author/year filter
```

### 2. Book not scanned yet
```python
# Syncthing synced but Kavita hasn't scanned
# Solution: Kavita auto-scans periodically, or trigger scan via API
```

### 3. Title mismatch (file vs metadata)
```python
# File: "Molecular Red.pdf"
# Metadata: "Molecular Red: Theory for the Anthropocene"
# Solution: Search API handles fuzzy matching
```

### 4. Authentication
```python
# Browser needs to be logged into Kavita
# Solution: User stays logged in, or we add ?apiKey=... to URL
```

---

## Future Enhancements

## Future Enhancements

### v1.1 - Librarian Integration (EPUB only) ✅ READY
**Status:** Tested and ready to implement

**What works:**
- ✅ kavita-link.py generates correct URLs for EPUB books
- ✅ Tested with 7 books (100% success rate on EPUBs)
- ✅ Search API reliable and fast
- ✅ **Links verified working by Nicholas** (2026-02-05)

**Implementation:**
1. Import `kavita-link.py` functions into librarian
2. After search results, check if file is `.epub`
3. If EPUB: call `get_kavita_url(book_title)`
4. Add to response: `📖 [Abrir no Kavita](URL)`

**Example output:**
```markdown
## Tarot Reading Explained

**Passage 1 (p. 42):**
> The Fool represents new beginnings...

**Passage 2 (p. 89):**
> Major Arcana cards are the soul of the deck...

📖 [Abrir no Kavita](http://192.168.1.152:5000/library/1/series/532/book/711)
```

**Code location:** `~/Documents/librarian/engine/` (TBD which module)

---

### v1.2 - Series vs Topics (folder linking)
**Status:** 🔍 INVESTIGATED - Series ≠ folders

**Question:** Can we link to topic folders (e.g., "magick/chaos" → all books in that topic)?

**Finding:**
- **Series** = individual books (e.g., "Molecular Red")
- **folderPath** = Kavita's internal folder (e.g., `/books/theory`)
- **NOT exact match** to librarian structure (e.g., `theory/anthropocene`)

**Kavita folder structure:**
```
/books/theory          → folderPath for all theory books
/books/magick          → folderPath for all magick books
```

**Librarian structure:**
```
~/Documents/librarian/books/theory/anthropocene/Molecular Red.epub
~/Documents/librarian/books/magick/chaos/The Chaos Apple.epub
```

**Conclusion:**
- Kavita groups by **top-level folder** only (`/books/theory`, not `/books/theory/anthropocene`)
- No direct "topic folder" linking
- **Series page** (`/library/1/series/{id}`) shows one book, not all books in topic

**Workaround (future):**
- Link to Kavita library browse page filtered by folder
- Or: Create Kavita "collections" for topics (manual curation)

**Decision:** Not worth implementing now. Individual book links are sufficient.

---

### v1.3 - Granular Linking (paragraph/page precision) 🎯
**Status:** 💡 PLANNED - Open book at exact location

**Goal:** When librarian finds a passage, link directly to that paragraph/page in Kavita reader

**Current state:**
- Link opens book at **first page** (chapter start)
- User has to manually navigate to passage

**Desired state:**
- EPUB: Open at **paragraph** (we already index paragraph IDs)
- PDF: Open at **page number** (we already extract page numbers)

**Kavita URL structure (research needed):**
```
http://192.168.1.152:5000/library/1/series/522/book/934?page=42
http://192.168.1.152:5000/library/1/series/522/book/934#paragraph-id
```

**Implementation:**
1. Check if Kavita reader supports URL params (`?page=X`, `#anchor`)
2. If yes: append page/paragraph to URL
3. If no: Explore Kavita API for "jump to location"

**Edge case - Currently reading:**
If Nicholas is already reading the book in Kavita (has progress), opening at a different location might:
- ❌ Lose his place
- ❌ Confuse reading progress tracking

**Solution:**
- Check Kavita API: "Get current reading position for book X"
- If reading in progress: **Show warning** or **open in new session**
- Or: Link to passage but preserve bookmark

**Priority:** High (this would be SUPER useful!)

**Next step:** Research Kavita reader URL params and reading progress API

---

### v1.4 - PDF Support (blocked)
**Status:** ⏸️ BLOCKED - Kavita not indexing PDFs

**Problem:**
- Kavita supports PDF (documented)
- libraryFileTypes configured: `[2, 3, 4]` (Image, EPUB, PDF)
- Container restarted, force scans run
- PDFs still not appearing in search results

**What we tried:**
1. ✅ Added PDF (4) to libraryFileTypes
2. ✅ Restarted Kavita container
3. ✅ Multiple force scans (normal + analyzeFiles=true)
4. ❌ PDFs still not indexed

**Possible causes:**
- Bug in Kavita 0.8.9.1
- Missing configuration (not documented)
- PDF parser issue (logs show some PDFs corrupt/encrypted)
- Large file filter (Celestial Mechanics = 65MB)

**Next steps (when investigating):**
1. Check Kavita forums/GitHub issues
2. Test with small, simple PDF
3. Try different Kavita version
4. Contact Kavita support

**Workaround:** Fallback to local PDF open if Kavita fails
```python
url = get_kavita_url(title)
if not url:
    subprocess.run(['open', pdf_path])
```

---

### v1.2 - Smart Caching
- [ ] Cache `seriesId` → `chapterId` mappings locally
- [ ] Reduce API calls for frequently accessed books
- [ ] Invalidate cache on Kavita rescan

### v1.3 - Multi-file Books
- [ ] Handle books with multiple chapters/volumes
- [ ] Let user choose specific chapter
- [ ] Remember last-read position (via Kavita API)

### v1.4 - Direct File Access
- [ ] If Kavita URL fails, fallback to direct PDF open
- [ ] `open ~/Documents/librarian/.../book.pdf`

---

## Configuration

**Kavita credentials:**
```python
KAVITA_URL = "http://192.168.1.152:5000"
USERNAME = "nonlinear"
PASSWORD = "#0uFyfT4K6$rwAJA8cGb"
API_KEY = "88ef5c57-c06d-408e-8d75-a32a8e9879bd"  # For OPDS/image-only access
```

**Stored in:** `~/.openclaw/workspace/kavita-link.py`

---

## Troubleshooting

### URL doesn't open (blank page)
**Cause:** Not logged into Kavita in browser  
**Solution:** Login once at http://192.168.1.152:5000, then links work

### "Book not found" error
**Cause:** Kavita hasn't scanned the file yet  
**Solution:** Wait for auto-scan or trigger manual scan in Kavita UI

### Wrong book opens
**Cause:** Multiple books with same title  
**Solution:** Add author or year to search query

### API returns 401 Unauthorized
**Cause:** JWT token expired (10 days)  
**Solution:** Script auto-logins on each run, no action needed

---

## Related Files

- **Script:** `~/.openclaw/workspace/kavita-link.py`
- **Skill:** `~/.openclaw/skills/librarian/SKILL.md` (future integration)
- **Books:** `~/Documents/librarian/` → NAS `/books/`
- **Kavita:** http://192.168.1.152:5000

---

**Last updated:** 2026-02-05  
**Status:** ✅ Tested and working  
**Next step:** Integrate into librarian skill for seamless book opening 📚✨
