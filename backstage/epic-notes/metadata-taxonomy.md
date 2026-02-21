# Metadata Taxonomy - Librarian v2.0

**Created:** 2026-02-21  
**Purpose:** Document complete metadata structure for confidence navigation

---

## 📊 Overview (Subway Map)

```
.library-index.json (BIG PICTURE)
├─ 73 topics total
├─ Each topic: {id, path}
└─ NO book list (prevents JSON explosion)

Each topic folder:
└─ .topic-index.json (NARROW)
   └─ books: [{id, title, filename, author, tags, filetype}, ...]
```

---

## 🗂️ .library-index.json (Global Index)

**Location:** `~/Documents/librarian/skill/books/.library-index.json`

**Purpose:** Big picture - all topics in library

**Structure:**
```json
{
  "schema_version": "2.0",
  "library_path": "/path/to/librarian/books",
  "embedding_model": "bge-small-en-v1.5",
  "chunk_settings": {
    "size": 1024,
    "overlap": 200
  },
  "topics": [
    {
      "id": "magick_chaos",
      "path": "magick/chaos"
    },
    {
      "id": "finances_debt",
      "path": "finances/debt"
    }
  ]
}
```

**Fields:**
- `topics[]` - Array of topic objects (73 total)
  - `id` - Topic identifier (underscore format: `magick_chaos`)
  - `path` - Folder path relative to books/ (`magick/chaos`)

**Key insight:** **NO book list here.** Keeps JSON small (73 topics vs 100+ books).

---

## 📚 .topic-index.json (Topic Index)

**Location:** `~/Documents/librarian/skill/books/<topic-path>/.topic-index.json`

**Example:** `~/Documents/librarian/skill/books/magick/chaos/.topic-index.json`

**Purpose:** Narrow view - books in specific topic

**Structure:**
```json
{
  "schema_version": "2.0",
  "topic_id": "magick_chaos",
  "embedding_model": "bge-small-en-v1.5",
  "chunk_settings": {
    "size": 1024,
    "overlap": 200
  },
  "last_indexed_at": 1770694800.8638778,
  "content_hash": "6794e57...",
  "books": [
    {
      "id": "condensed_chaos",
      "title": "Condensed Chaos",
      "filename": "Condensed Chaos.epub",
      "author": "Unknown",
      "tags": [],
      "last_modified": 1769833763.344015,
      "filetype": "epub"
    },
    {
      "id": "the_chaos_apple",
      "title": "The Chaos Apple",
      "filename": "The Chaos Apple.epub",
      "author": "Unknown",
      "tags": [],
      "last_modified": 1762816392.719323,
      "filetype": "epub"
    }
  ]
}
```

**Fields:**
- `topic_id` - Matches `id` from .library-index.json
- `books[]` - Array of book objects
  - `id` - Book identifier (slug: `condensed_chaos`)
  - `title` - **User-facing name** (NO extension: "Condensed Chaos")
  - `filename` - **Internal reference** (WITH extension: "Condensed Chaos.epub")
  - `author` - Author name (or "Unknown")
  - `tags` - Array of tags (currently unused)
  - `filetype` - "epub" or "pdf"
  - `last_modified` - Unix timestamp

**🔴 CRITICAL: Extension handling**

- **User says:** "I Ching hexagram"
- **AI matches:** `title: "I Ching, The Oracle of the Cosmic Way"`
- **Wrapper receives:** `filename: "I Ching, The Oracle of the Cosmic Way.epub"`
- **User NEVER types:** ".epub" or ".pdf" (irrelevant to them)

**Extension = metadata detail, not user concern.**

---

## 🧭 Navigation Patterns (Confidence Logic)

### 1-Step Navigation (Topic Scope)

**User query:** "chaos magick sigils"

**Flow:**
1. Load `.library-index.json`
2. Fuzzy match query → `topics[]` array
3. Found: `{id: "magick_chaos", path: "magick/chaos"}`
4. **DONE** - scope = topic, call wrapper

**Cost:** 1 JSON read (~6KB)

---

### 2-Step Navigation (Book Scope)

**User query:** "I Ching hexagram 23"

**Flow:**
1. Load `.library-index.json`
2. Scan `topics[]` → NO match (books not in global index)
3. **Step 2:** Infer likely topics (e.g., "magick_i_ching")
4. Load `.topic-index.json` from likely topic(s)
5. Fuzzy match query → `books[]` array
6. Found: `{title: "I Ching, The Oracle of the Cosmic Way", filename: "...epub"}`
7. **DONE** - scope = book, call wrapper

**Cost:** 1 global JSON + N topic JSONs (scan folders)

**Why slower:** Must load multiple .topic-index.json to find book.

---

## 🔍 Fuzzy Matching Rules

### Topic Match

**Match against:** `topics[].id` and `topics[].path`

**Examples:**
- "chaos magick" → matches `magick_chaos`
- "debt finance" → matches `finances_debt`
- "I Ching" → matches `magick_i_ching`

**Case-insensitive, substring matching.**

---

### Book Match

**Match against:** `books[].title` and `books[].filename` (without extension)

**Examples:**
- "Condensed Chaos" → matches `title: "Condensed Chaos"`
- "I Ching Cosmic Way" → matches `title: "I Ching, The Oracle of the Cosmic Way"`
- "Graeber debt" → matches `title: "Debt - The First 5000 Years"` (from author context)

**Case-insensitive, substring matching. NEVER match extension.**

---

## 🎯 Confidence Decision Tree

```
Query → Load .library-index.json
         ↓
    Match topics[]?
         ↓
    YES → Topic scope (1 step) ✅
         ↓
    NO → Infer likely topics
         ↓
    Load .topic-index.json (N topics)
         ↓
    Match books[] in any topic?
         ↓
    YES → Book scope (2 steps) ✅
         ↓
    NO → CLARIFY (hard stop) 🛑
```

**Tiebreaker:** If matches BOTH topic AND book → **TOPIC WINS** (future: mixed searches).

---

## 🚨 Edge Cases

### 1. Multiple Books Match

**Example:** "I Ching" matches 18 books in `magick_i_ching` topic.

**Decision:**
- If query is vague → CLARIFY
- If query has distinguishing keyword → pick best match
  - "I Ching cosmic way" → "I Ching, The Oracle of the Cosmic Way"
  - "I Ching Wilhelm" → "...translated - Richard Wilhelm"

**Rule:** Prefer specificity. If ambiguous → ask user.

---

### 2. Book Name = Topic Name

**Example:** User says "chaos magick"

**Could mean:**
- Topic: `magick_chaos` (all books in topic)
- Book: "Condensed Chaos" (single book)

**Decision:** **TOPIC WINS** (tiebreaker rule).

**Why:** Topic = broader scope (more results). If user wants book, they'll be more specific.

---

### 3. Extension in User Query

**Example:** User says "I Ching.epub"

**Handling:**
- Strip extension before matching
- Match against `title` (NOT `filename`)
- "I Ching.epub" → "I Ching" → match books with "I Ching" in title

**Why:** Extension = internal detail, user shouldn't need to know.

---

## 📁 Sample Data (Real Examples)

### Topic: magick_chaos

**Books:**
- Condensed Chaos.epub
- The Chaos Apple.epub
- Journal to the self.epub
- Grouo Explorations in Ego Magick.pdf (typo in title)
- Egregore.pdf

**Note:** Mix of .epub and .pdf in same topic.

---

### Topic: finances_debt

**Books:**
- How to invest in debt a complete guide to alternative.pdf

**Note:** Single book in topic (perfectly valid).

---

### Topic: magick_i_ching

**Books:** 18 total I Ching books (various translations, authors)

**Note:** Large topic, needs specific queries.

---

## 🛠️ Wrapper Syntax Reference

**Topic search:**
```bash
./librarian.sh "chaos magick sigils" "topic" "magick_chaos" 5
#                  ↑ query            ↑ type  ↑ topic_id
```

**Book search:**
```bash
./librarian.sh "hexagram 23" "book" "I Ching, The Oracle of the Cosmic Way.epub" 3
#                  ↑ query    ↑ type  ↑ filename (WITH extension)
```

**Key points:**
- `topic_id` = from .library-index.json (underscore format)
- `filename` = from .topic-index.json (WITH extension)
- Query = user's natural language (no extension needed)

---

## 🔄 Future Optimizations (v0.16.0+)

**Problem:** Book search scans all 73 topics (2 steps, slow).

**Solution options:**

**A) Book-level global index**
```json
// .library-index.json
{
  "topics": [...],
  "books": {
    "condensed_chaos": {"topic": "magick_chaos", "filename": "Condensed Chaos.epub"},
    ...
  }
}
```
- **Pro:** 1-step book search
- **Con:** JSON explosion (100+ books)

**B) Lazy loading with cache**
- First query → scan all topics, cache results
- Subsequent queries → use cache
- **Pro:** Fast after first query
- **Con:** First query still slow

**C) Full-text search index**
- Pre-build title → topic mapping
- **Pro:** Instant lookup
- **Con:** More complex indexing

**Decision:** Defer to v0.16.0+ (current rudimentar approach works).

---

## 📝 Lessons & Insights

**1. JSON size vs query speed**
- Global book list = faster queries, larger JSON
- Per-topic indexes = smaller global JSON, slower book queries
- **Trade-off:** Optimized for topic-heavy workflow (Nicholas's use case)

**2. Extension handling**
- User-facing = NO extension (title)
- Internal = WITH extension (filename)
- **Why:** User doesn't care, system needs precision

**3. Tiebreaker philosophy**
- Topic wins over book (broader > narrow)
- Future: mixed searches (book WITHIN topic)
- **Pragmatic:** Start simple, refine with usage

---

**Documented:** 2026-02-21  
**Status:** Complete metadata taxonomy for confidence navigation  
**Next:** Real-world validation (Nicholas uses skill, edge cases surface)
