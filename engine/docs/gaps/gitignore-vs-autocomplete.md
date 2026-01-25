# Gap: Gitignore vs VS Code Autocomplete

**Status:** ✅ SOLVED
**Impact:** Low (workaround implemented)
**Epic:** v0.5.0 Smart Indexing

---

## Problem

**VS Code `#file:` autocomplete only shows files tracked by git.**

Files in `.gitignore` don't appear in autocomplete, even when they exist on disk.

**Key Discovery:** There is **NO** VS Code setting to decouple gitignore from file picker autocomplete. The file picker ALWAYS uses git index.

**However:** You CAN separate git exclusion from Explorer/Search visibility using `.git/info/exclude` + `.vscode/settings.json`.

---

## Solution: Three-Layer Exclusion Strategy

\*\*TImplementation Details

### `.git/info/exclude` (Local git ignore)

**Purpose:** Exclude files from git WITHOUT blocking autocomplete.

**Location:** `.git/info/exclude` (not committed, local only)

```bash
# BYOB: Bring Your Own Books - Local files (not shared via .gitignore)
# These patterns prevent git commits but allow VS Code autocomplete

# Books (EPUBs and PDFs)
books/**/*.epub
books/**/*.pdf

# Embedding models (large downloads)
models/
```

**Why this works:**

- Git honors exclusions (files won't be committed)
- Files NOT in `.gitignore` → appear in file picker
- Each user maintains their own `.git/info/exclude`

---

### `.vscode/settings.json` (UI exclusions)

**Purpose:** Hide files from Explorer/Search while keeping autocomplete.

**Location:** `.vscode/settings.json` (can be committed)

```json
{
  // Hide books from Explorer and Search (still show in #file: autocomplete)
  "files.exclude": {
    "**/*.epub": true,
    "**/*.pdf": true,
    "**/.DS_Store": true
  },
  "search.exclude": {
    "**/*.epub": true,
    "**/*.pdf": true,
    "**/node_modules": true,
    "**/__pycache__": true
  }
}
```

**Why this works:**

- `files.exclude` → hides from File Explorer sidebar
- `search.exclude` → excludes from Ctrl+Shift+F search
- Neither affects file picker (`Ctrl+P` / `#file:`)
- Can be shared via git (all users get clean UI)

---

### `.gitignore` (Shared exclusions)

**Purpose:** Only shared patterns (indices, cache, generated files).

**Location:** `.gitignore` (committed to repo)

```gitignore
# Books metadata/indices (books themselves excluded via .git/info/exclude)
books/**/*.pkl
books/**/*.index
booAlternative Solutions Considered

### A) Track books in git (❌ Reject
__pycache__/
*.pyc

# macOS
.DS_Store
```

**Why NOT put books here:**

- ❌ Blocks autocomplete
- ❌ Can't reference books with `#file:`
- ❌ Defeats BYOB principle visibility

---

## Why This Solution Works

**The Matrix:**

| File Type   | .gitignore | .git/info/exclude | .vscode/settings.json | Autocomplete | Git Tracked | Explorer | Search |
| ----------- | ---------- | ----------------- | --------------------- | ------------ | ----------- | -------- | ------ |
| **Books**   | ❌ No      | ✅ Yes            | ✅ Yes (exclude)      | ✅ Yes       | ❌ No       | ❌ No    | ❌ No  |
| **Indices** | ✅ Yes     | -                 | -                     | ❌ No        | ❌ No       | ❌ No    | ❌ No  |
| **Code**    | ❌ No      | ❌ No             | ❌ No                 | ✅ Yes       | ✅ Yes      | ✅ Yes   | ✅ Yes |

**Key insight:** VS Code cannot decouple search/files exclusions from gitignore. You must handle git exclusion externally (`.git/info/exclude`) to preserve autocomplete.

---

## Previous Workarounds (Now Obsolete)

**Rationale:**

- Books are copyrighted content (user provides their own)
- Average book: 1-10MB
- 430 books × 5MB avg = ~2GB repo size
- GitHub has 1GB soft limit per repo
- Slower clone/push/pull for all contributors

**Trade-off:** Lightweight repo vs autocomplete convenience

---

## Current Workarounds

### Option 1: List books in terminal

```bash
# Find all books in a topic
ls books/theory/anthropocene/*.{epub,pdf}

# Search for book by keyword
find books -name "*forest*" -type f
```

### Option 2: Use library-index.json

```bash
# All books with metadata
cat books/library-index.json | jq '.topics[] | .path'

# Books in specific topic
cat books/theory/anthropocene/topic-index.json | jq '.books[].title'
```

### Option 3: Use research.py directly

```bash
# Query by topic (always works)
python3.11 scripts/research.py "query" --topic anthropocene

# Query by book (copy/paste filename)
python3.11 scripts/research.py "query" --book "How forests think.epub"
```

### Option 4: Attach topic folder instead

```
#file:books/theory/anthropocene
```

Then specify book name in natural language:

> "Search for 'infrastructure' in the book 'How Infrastructure Works'"

Let MCP parse book name from context (requires v0.6.0 NLP enhancement).

---

## Potential Solutions

### A) Track books in git (❌ Not Recommended)

**Approach:** Remove `books/**/*.pdf` from gitignore

**Pros:**

- ✅ Books appear in autocomplete
- ✅ Full git history of library changes

**Cons:**

- ❌ Repo size: ~2GB (exceeds GitHub limits)
- ❌ Slow clones/pushes
- ❌ Copyright concerns for public repos
- ❌ Can't share repo publicly

**Verdict:** Defeats BYOB design principle

---

### B) Git LFS (⚠️ Complex)

**Approach:** Use Git Large File Storage for books

```bash
git lfs install
git lfs track "books/**/*.epub"
git lfs track "books/**/*.pdf"
```

**Pros:**

- ✅ Books appear in autocomplete
- ✅ Lightweight repo (LFS stores pointers)
- ✅ Large files stored separately

**Cons:**

- ⚠️ Requires GitHub LFS setup (bandwidth limits)
- ⚠️ Free tier: 1GB storage, 1GB bandwidth/month
- ⚠️ Cost: $5/month per 50GB storage
- ❌ Still has copyright concerns
- ❌ Users must `git lfs pull` to download

**Verdict:** Adds complexity without solving copyright issue

---

### C) Document workaround (✅ Current Approach)

**Approach:** Accept limitation, provide good workarounds

**Implementation:**

1. Document `ls` and `find` commands in README
2. Enhance research.prompt.md to explain usage
3. Add topic-level autocomplete (folders work fine)
4. v0.6.0: Add NLP to parse book names from natural language

**Pros:**

- ✅ Simple, no infrastructure changes
- ✅ Maintains BYOB principle
- ✅ Works well with conversational UX
- ✅ Can improve in v0.6.0 with NLP

**Cons:**

- ⚠️ UX friction for book-level queries
- ⚠️ Requires copy/paste or typing

**Verdict:** Best balance of simplicity and functionality

---

### D) Custom VS Code extension (🔮 Future)

**Approach:** Create extension that reads `.vscode/library-books.json`

```json
{
  "books": [
    "books/theory/anthropocene/How forests think.epub",
    "books/cooking/Bread Handbook PDF.pdf"
  ]
}
```

Extension provides custom autocomplete for books, bypassing git index.

**Pros:**

- ✅ Books appear in autocomplete
- ✅ No gitignore changes
- ✅ Lightweight repo

**Cons:**

- ❌ Requires maintaining extension
- ❌ Users must install extension
- ❌ Complex for minimal gain

**Verdict:** Overkill for current scope, revisit in v1.0

---

## Recommendation: Option C

**Accept limitation, improve UX through:**

1. **Documentation** (this gap.md)
2. **Topic-level autocomplete** (works today)
3. **v0.6.0 NLP**: Parse book names from chat
   - User: "Search 'infrastructure' in How Infrastructure Works"
   - MCP extracts: `--book "How Infrastructure Works.epub"`

**Benefits:**

- Maintains BYOB principle
- No infrastructure complexity
- Conversational UX improves over time
- Can revisit if pain point grows

---

## Usage Guide

**Recommended workflow:**

```markdown
1. Attach topic folder with #file:
   #file:books/theory/anthropocene

2. In chat, specify book naturally:
   "Search for 'climate adaptation' in the book How Forests Think"

3. Or use CLI directly:
   python3.11 scripts/research.py "climate" --book "How forests think.epub"
```

**Quick reference:**

```bash
# List all books in topic
ls books/theory/anthropocene/*.{epub,pdf}

# Find book by keyword
find books -name "*forest*" -type f

# Get book metadata
cat books/theory/anthropocene/topic-index.json | jq '.books'
```

---

## Status

**Current:** Option C implemented (v0.5.0)
**Next:** v0.6.0 NLP enhancement for book name parsing
**Future:** Consider custom extension if friction increases
