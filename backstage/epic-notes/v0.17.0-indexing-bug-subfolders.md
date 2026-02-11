# v0.17.0 - Indexing Bug: Subfolders Not Discovered

**Epic:** Multi-Scope Queries (v0.17.0)  
**Date discovered:** 2026-02-10  
**Reporter:** Nicholas + Claw

---

## 🚨 Bug Description

**~50+ subfolders with books are NOT being indexed!**

**Examples of missing content:**
- `theory/system/` (DeLanda - Philosophy and Simulation)
- `magick/tarot/`, `magick/chaos/`, `magick/i ching/`, `magick/familiars/`
- `anarchy/hakim bey/`, `anarchy/james c scott/`, `anarchy/david graeber/`
- `design/usability/`, `design/typography/`, `design/generative/`
- `drawing/basics/`, `drawing/portrait/`, `drawing/clothes/`
- `finances/debt/`, `finances/taxes/`, `finances/mortgage/`
- `AI/theory/`, `AI/policy/`, `AI/prompt engineering/`
- And ~40+ more...

**Impact:** **Metade da biblioteca ou mais** não tá acessível via research!

---

## 🔍 Root Cause

**File:** `~/Documents/librarian/engine/scripts/index_library.py`  
**Function:** `scan_library_folders()` (lines 250-285)

**Problem:** 
```python
has_books = any(
    f.suffix.lower() in ['.epub', '.pdf']
    for f in item.iterdir()
    if f.is_file()
)
```

**Logic checks ONLY immediate folder for books**, não registra subfolders como topics independentes.

**Current behavior:**
- ✅ `books/theory/` (tem livros diretamente) → registra como topic
- ❌ `books/theory/system/` (tem livros, mas é subfolder) → **NÃO registra**

**Recursion EXISTS** (`scan_directory()` se chama recursivamente), **MAS** só adiciona ao registry se `has_books` = True no nível atual.

**Result:** 
- `registry['topics']` só tem pastas com livros diretamente
- `--all` indexa tudo no registry → subfolders ficam de fora

---

## 📐 Architecture Rule (Nicholas)

**NEVER:** Pasta com livros + subfolders ao mesmo tempo

**ALWAYS:** Topic folder OU tem subfolders OU tem livros (nunca ambos)

**Examples:**
- ✅ `theory/` → sem livros, só subfolders (`system/`, `anthropocene/`, etc.)
- ✅ `theory/system/` → TEM livros (Philosophy and Simulation, etc.)
- ❌ `theory/` → livros + subfolders (violates rule)

**Current structure already follows this!** Bug is in discovery logic not respecting it.

---

## ✅ Solution

**Fix `scan_library_folders()` to:**

1. **Scan recursively** (already does this ✅)
2. **Register ANY folder with books as independent topic** (currently broken ❌)
3. **Ignore empty folders** (already does this ✅)

**Pseudocode:**
```python
def scan_directory(base_path, relative_path=""):
    for item in base_path.iterdir():
        if item.is_dir():
            # Check if THIS folder has books
            has_books = any(f.suffix in ['.epub', '.pdf'] for f in item.iterdir() if f.is_file())
            
            if has_books:
                # Register as topic
                topic_id = slugify(relative_path + "/" + item.name)
                topics.append({'id': topic_id, 'path': relative_path + "/" + item.name})
            
            # ALWAYS recurse into subfolders (even if current has books)
            scan_directory(item, relative_path + "/" + item.name)
```

**Key change:** Don't skip recursion when `has_books = True`. Check each folder independently.

---

## 🧪 Test Cases

**After fix, verify:**

1. **Existing topics still work:**
   - `theory/` → no books, has subfolders → NOT a topic ✅
   - `cooking/` → has books directly → IS a topic ✅

2. **Subfolders discovered:**
   - `theory/system/` → has books → IS a topic ✅
   - `magick/tarot/` → has books → IS a topic ✅

3. **Empty folders ignored:**
   - `design/unused/` → no books → NOT a topic ✅

4. **Deep nesting works:**
   - `design/usability/rosenfeld/` → has books → IS a topic ✅
   - `design/usability/general/` → has books → IS a topic ✅

5. **Run `--all` reindexes everything:**
   ```bash
   cd ~/Documents/librarian/engine/scripts
   python3 index_library.py --all
   ```

6. **Verify topic count:**
   ```bash
   cat ~/Documents/librarian/books/.library-index.json | jq '.topics | length'
   ```
   **Expected:** ~70+ topics (currently ~20)

---

## 📊 Validation

**Before fix:**
```bash
# Count current topics
cat ~/Documents/librarian/books/.library-index.json | jq '.topics | length'
# Output: ~20
```

**After fix:**
```bash
# Reindex
python3 index_library.py --all

# Count new topics
cat ~/Documents/librarian/books/.library-index.json | jq '.topics | length'
# Expected: ~70+

# Verify DeLanda findable
python3 research-tracked.sh "Philosophy and Simulation DeLanda"
# Should find: theory/system/Philosophy and Simulation.epub
```

---

## 🚧 Implementation Notes

**File to edit:** `~/Documents/librarian/engine/scripts/index_library.py`

**Function:** `scan_library_folders()` (lines 250-285)

**Keep:**
- Recursive scanning ✅
- Slugify logic ✅
- Skip hidden files/system files ✅

**Fix:**
- Register ALL folders with books (not just top-level)
- Don't skip recursion when folder has books

**After fix:**
- Run full reindex (`--all`)
- Test multi-topic search (v0.17.0 epic goal)
- Update topic count in docs

---

## 🔗 Related

**Epic:** v0.17.0 - Multi-Scope Queries  
**Blocked by:** This bug (can't test multi-topic if half the topics don't exist)  
**Priority:** HIGH (blocks v0.17.0 + breaks current research for ~50% of library)

---

**Next:** Fix → test → validate → merge → celebrate 🏴
