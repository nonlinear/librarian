# Gap: VS Code File Picker Size Limit

**Status:** ❌ UNSOLVABLE (VS Code limitation)
**Impact:** Medium (affects UX, workaround available)
**Epic:** v0.5.0 Smart Indexing

---

## Problem

**Books (EPUBs/PDFs) don't appear in VS Code `#file:` autocomplete** (chat, Quick Open, etc.), even when:

- Removed from `.gitignore`
- Removed from `files.exclude`
- Removed from `.git/info/exclude`
- Tracked by git (showing as `??` untracked)

## Root Cause

**VS Code file picker has an undocumented hardcoded file size limit** (~1-2MB threshold):

- ✅ Small files (< 1MB) appear in autocomplete
- ❌ Large files (> 1MB) don't appear, **regardless of git/exclude settings**
- ✅ **Folders always appear**, regardless of size

## Validation

Tested multiple hypotheses:

### 1. .gitignore blocking ❌

- **Hypothesis:** `.gitignore` prevents autocomplete
- **Test:** Removed books from `.gitignore`
- **Result:** Still don't appear

### 2. files.exclude blocking ❌

- **Hypothesis:** `files.exclude` hides from autocomplete
- **Test:** Removed `files.exclude` from settings.json
- **Result:** Books appear in Explorer, but still not in autocomplete

### 3. .git/info/exclude blocking ❌

- **Hypothesis:** `.git/info/exclude` treated differently than `.gitignore`
- **Test:** Cleared `.git/info/exclude`, books show as `??` untracked
- **Result:** Still don't appear in autocomplete (gray out in Explorer)
- **Discovery:** VS Code treats `.git/info/exclude` same as `.gitignore` for UI

### 4. File size discrimination ✅ **ROOT CAUSE**

- **Hypothesis:** Large files filtered by size
- **Test:** Created `test.txt` (5 bytes) → ✅ **Appears in autocomplete!**
- **Result:** Size is the discriminator

**Test Results:**

```
test.txt (5 bytes)                   → ✅ Appears
Marx in the Anthropocene (342KB)     → ❌ Doesn't appear
Molecular Red (314KB)                → ❌ Doesn't appear
Psychopolitics (701KB)               → ❌ Doesn't appear
How forests think (2.5MB)            → ❌ Doesn't appear
How Infrastructure Works (8.4MB)     → ❌ Doesn't appear
```

**Folders (always work):**

```
books/design/              → ✅ Appears
books/theory/anthropocene/ → ✅ Appears
books/cooking/             → ✅ Appears
```

---

## Attempted Solutions

### 1. Three-Layer Exclusion Strategy ❌ DOESN'T WORK

**Strategy:**

- `.gitignore` → metadata only
- `.git/info/exclude` → books
- `.vscode/settings.json` → search.exclude only

**Result:** VS Code treats all exclusion patterns the same for UI. `.git/info/exclude` causes "gray out" just like `.gitignore`.

### 2. search.maxFileSize Setting ❌ DOESN'T WORK

```json
{
  "search.maxFileSize": 50 // MB
}
```

**Result:** Only affects **search index** (Cmd+Shift+F), **NOT file picker** (Cmd+P, `#file:`).

### 3. Remove files.exclude ❌ DOESN'T HELP

**Result:** Files appear in Explorer, but size limit still blocks autocomplete.

---

## Workaround: Use Folder Autocomplete

**Instead of:**

```
❌ #file: Marx in the Anthropocene.epub
❌ #file: How Infrastructure Works.epub
```

**Use:**

```
✅ #file: anthropocene
✅ #file: design
✅ #file: cooking
```

Folders always appear regardless of size. Then manually specify book name in prompt.

---

## Future Enhancement (v0.6.0)

**NLP book name extraction** from user text:

```
User: "what does Marx in the Anthropocene say about..."
Agent: [extracts "Marx in the Anthropocene"]
      → searches books/theory/anthropocene/
      → finds Marx in the Anthropocene.epub
```

This removes need for `#file:` autocomplete entirely.

---

## Implementation Details

### `.git/info/exclude` (Local git ignore)

```bash
# BYOB: Bring Your Own Books - Local files (not shared via .gitignore)
# These patterns prevent git commits but allow VS Code autocomplete

# Books (EPUBs and PDFs)
books/**/*.epub
books/**/*.pdf

# Embedding models (large downloads)
engine/models/
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
python3.11 engine/scripts/research.py "query" --topic anthropocene

# Query by book (copy/paste filename)
python3.11 engine/scripts/research.py "query" --book "How forests think.epub"
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
   python3.11 engine/scripts/research.py "climate" --book "How forests think.epub"
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
