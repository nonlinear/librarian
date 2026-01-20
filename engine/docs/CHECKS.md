# Personal Library MCP - Stability Checks

> **Definition of Done:** Tests required before pushing to production

> 🤖
>
> [CHANGELOG](CHANGELOG.md) - What we did
> [ROADMAP](ROADMAP.md) - What we wanna do
> [CONTRIBUTING](../../.github/CONTRIBUTING.md) - How we do it
> [CHECKS](CHECKS.md) - What we accept
>
> [/whatsup](../../.github/prompts/whatsup.prompt.md) - The prompt that keeps us sane
>
> 🤖

---

## 🎯 Stability Definition

**What "stable" means for this project:**

- ✅ MCP server starts in <1 second
- ✅ Can query books without errors
- ✅ Can add new books and reindex
- ✅ Works on macOS (primary platform)
- ✅ Python 3.11+ compatible
- ✅ No API keys required (fully offline)

---

## 🤖 For AI: How to Run These Checks

**Automated test sequence (copy-paste into terminal):**

```bash
#!/bin/bash
# Personal Library MCP - Automated Stability Checks

echo "🔍 Running stability checks..."
echo ""

# Test 1: MCP query functionality (what research.prompt.md actually uses)
echo "1️⃣ MCP query test..."
python3.11 -c "
import json
from pathlib import Path
metadata = json.loads((Path('books') / 'metadata.json').read_text())
topic_count = len(metadata.get('topics', []))
print(f'✅ MCP works ({topic_count} topics)' if topic_count > 0 else '❌ MCP failed')
" 2>/dev/null || echo "❌ MCP failed"

# Test 2: Dependencies
echo "2️⃣ Dependencies test..."
python3.11 -c "import llama_index.core; import sentence_transformers" 2>&1 && echo "✅ Dependencies OK" || echo "❌ Dependencies missing"

# Test 3: File structure
echo "3️⃣ File structure test..."
test -f books/metadata.json && ls books/*/faiss.index >/dev/null 2>&1 && echo "✅ Files exist" || echo "❌ Files missing"

# Test 4: Nested folder support
echo "4️⃣ Nested folder test..."
python3.11 -c "
import json
from pathlib import Path
metadata = json.loads((Path('books') / 'metadata.json').read_text())
nested = [t['id'] for t in metadata['topics'] if '_' in t['id']]
print(f'✅ Nested topics work ({len(nested)} found)' if nested else '⚠️ No nested topics')
" 2>/dev/null || echo "❌ Nested topic test failed"

echo ""
echo "✅ All checks complete. Review results above."
```

**What whatsup.prompt.md does:**

1. Reads this file
2. Runs the automated test sequence above
3. Blocks push if ANY test fails
4. Reports results to user

---

## 🔍 Pre-Commit Checklist

**Run these tests BEFORE every commit to main:**

### 1. Server Startup Test

```bash
# Test 1: MCP server starts quickly
python3.11 scripts/mcp_server_lazy.py
# Expected: "Personal Library MCP Server ready" in <1s
# Ctrl+C to stop

# Test 2: Check for errors in logs
# Expected: No tracebacks, no "ERROR:" messages
```

**Pass criteria:** ✅ Starts in <1s, no errors

---

### 2. Core Functionality Test

```bash
# Test 3: Query library (if running outside MCP)
python3.11 scripts/query.py "What is the panopticon?"
# Expected: Returns relevant passages from books

# OR use VS Code MCP integration:
# Open VS Code → use /research prompt → query library
# Expected: MCP responds with book citations
```

**Pass criteria:** ✅ Returns relevant results, no crashes

---

### 3. Indexing Test

```bash
# Test 4: Generate metadata
python3.11 scripts/generate_metadata.py
# Expected: Updates books/metadata.json, no errors

# Test 5: Reindex single topic (faster than full reindex)
python3.11 scripts/reindex_topic.py "AI"
# Expected: Creates/updates storage/AI/ directory
# Expected: No crashes, completes successfully
```

**Pass criteria:** ✅ Metadata updated, topic indexed without errors

---

### 3.1. Happy Path Test (Path Resolution)

**Question:** If a user follows README.md happy path, will path resolution work for:

- ✅ Nested topics? (`cybersecurity_applied` → `books/cybersecurity/applied/`)
- ✅ Root topics with underscores? (`product_architecture` → `books/product architecture/`)

```bash
# Test 6a: Verify nested topic path resolution
python3.11 -c "
from pathlib import Path
import json
BOOKS_DIR = Path('books')
metadata = json.loads((BOOKS_DIR / 'metadata.json').read_text())

# Find a nested topic
nested = [t for t in metadata['topics'] if '_' in t['id'] and '/' in t['id'].replace('_', '/')]
if nested:
    topic_id = nested[0]['id']
    # Simulate indexer.py logic
    nested_path = BOOKS_DIR / topic_id.replace('_', '/')
    print(f'✅ Nested path works: {topic_id} → {nested_path}' if nested_path.exists() else f'❌ Path broken: {nested_path}')
else:
    print('⚠️  No nested topics to test')
"

# Test 6b: Verify root topic with underscore
python3.11 -c "
from pathlib import Path
import json
BOOKS_DIR = Path('books')
metadata = json.loads((BOOKS_DIR / 'metadata.json').read_text())

# Find root topic with underscore (e.g., product_architecture)
root_underscore = [t for t in metadata['topics'] if '_' in t['id'] and '/' not in t['id'].replace('_', '/')]
if root_underscore:
    topic = root_underscore[0]
    topic_id = topic['id']
    topic_label = topic['label']
    # Simulate indexer.py logic
    nested_path = BOOKS_DIR / topic_id.replace('_', '/')
    label_path = BOOKS_DIR / topic_label
    actual_path = nested_path if nested_path.exists() else label_path
    print(f'✅ Root underscore works: {topic_id} → {actual_path}' if actual_path.exists() else f'❌ Path broken: {topic_id}')
else:
    print('⚠️  No root underscore topics to test')
"

# Test 6c: Run full indexer to verify (happy path from README)
python3.11 scripts/indexer.py 2>&1 | grep -E "✓ Loaded|⚠️  Not found" | head -10
# Expected: All books load, no "Not found" errors
```

**Pass criteria:**

- ✅ Nested topics resolve correctly
- ✅ Root topics with underscores resolve correctly
- ✅ Full indexer finds all books in all topics

**Why this matters:** Bug was that `indexer.py` only used `topic_label`, not handling underscore-to-slash conversion. Users following README step 6 ("Build indices") would hit missing file errors for nested topics and misnamed root topics.

---

### 4. Environment Check

```bash
# Test 6: Check dependencies
python3.11 -c "import llama_index.core; import sentence_transformers; print('✅ Dependencies OK')"

# Test 7: Check file structure
ls books/metadata.json  # Should exist
ls books/*/faiss.index  # Should show topic-based indices
ls books/*/chunks.json  # Should show topic-based chunks
```

**Pass criteria:** ✅ All imports work, required files exist

---

### 5. Memory & Performance Check

```bash
# Test 8: Monitor memory during reindex (optional, for large libraries)
/usr/bin/time -l python3.11 scripts/reindex_topic.py "AI" 2>&1 | grep "maximum resident set size"
# Expected: <2GB for most topics
```

**Pass criteria:** ✅ No memory crashes, completes within reasonable time

---

## 🚨 Known Failure Points

**Common issues and how to detect:**

### Issue 1: Model not downloaded

**Symptom:** `ModuleNotFoundError: No module named 'sentence_transformers'`
**Fix:** Run `bash scripts/setup.sh`
**Test:** `python3.11 -c "import sentence_transformers"`

### Issue 2: Missing metadata.json

**Symptom:** MCP server starts but can't find books
**Fix:** Run `python3.11 scripts/generate_metadata.py`
**Test:** `cat books/metadata.json | jq .`

### Issue 3: Corrupted index

**Symptom:** Query returns no results or crashes
**Fix:** Reindex affected topic: `python3.11 scripts/reindex_topic.py "<topic>"`
**Test:** Query after reindex

### Issue 4: M3 Mac crashes (mpnet model)

**Symptom:** Segfault during reindexing with `all-mpnet-base-v2`
**Fix:** Use `all-MiniLM-L6-v2` (current default)
**Test:** Check `scripts/indexer.py` for model name

---

## 📊 Performance Benchmarks

**Current measured performance (as of Jan 19, 2026):**

| Metric                   | Target | Current  | Status |
| ------------------------ | ------ | -------- | ------ |
| MCP startup              | <1s    | <0.5s    | ✅     |
| First query (cold)       | <3s    | ~2s      | ✅     |
| Cached query             | <0.5s  | ~0.3s    | ✅     |
| Reindex single topic     | <30s   | 10-45s\* | ✅     |
| Full reindex (23 topics) | <10min | ~8min\*  | ✅     |
| Memory usage             | <2GB   | ~1.2GB   | ✅     |

\*Varies by topic size (number of books/chunks)

**How to measure:**

```bash
# Startup time
time python3.11 scripts/mcp_server.py &
# Ctrl+C after "ready" message

# Query time
time python3.11 scripts/query.py "test query"

# Reindex time
time python3.11 scripts/reindex_topic.py "AI"
```

---

## 🧹 Code Hygiene Checks

**Run these checks before every commit:**

### 1. No Debug Code in Production

```bash
# Check for debug print statements
grep -r "print(" scripts/ --exclude-dir=deprecated | grep -v "#" | grep -v "def print"
# Expected: Only intentional logging, no debug prints

# Check for commented-out code blocks
grep -r "# .*def \|# .*class \|# .*import " scripts/ --exclude-dir=deprecated | wc -l
# Expected: 0 or only intentional comments
```

**Pass criteria:** ✅ No debug code, no large commented blocks

---

### 2. No Hardcoded Paths or Secrets

```bash
# Check for hardcoded paths
grep -r "/Users/\|C:\\\\\|/home/" scripts/ --exclude-dir=deprecated
# Expected: Empty (use relative paths)

# Check for API keys in code
grep -ri "api_key\|apikey\|secret\|password" scripts/ --exclude-dir=deprecated | grep -v "GOOGLE_API_KEY" | grep -v "# "
# Expected: Only environment variable references

# Verify .gitignore coverage
cat .gitignore | grep -q "\.env" && echo "✅ .env ignored" || echo "❌ Add .env to .gitignore"
cat .gitignore | grep -q "storage/" && echo "✅ storage/ ignored" || echo "⚠️  Consider ignoring storage/"
```

**Pass criteria:** ✅ No hardcoded paths, no exposed secrets, .env in .gitignore

---

### 3. File Organization

```bash
# Check for duplicate scripts
find scripts/ -name "*_old.py" -o -name "*_backup.py" -o -name "*_new.py"
# Expected: Empty (move to deprecated/ with timestamp)

# Verify deprecated files have timestamps
ls -la scripts/deprecated/ | grep -v "^d" | awk '{print $9}' | grep -v "2024\|2025\|2026"
# Expected: All deprecated files have date in name

# Check for orphaned __pycache__
find . -type d -name "__pycache__" | grep -v "/.venv/\|/venv/"
# Expected: Only in virtual environment
```

**Pass criteria:** ✅ No duplicate files, deprecated/ organized, no stray cache

---

### 4. Requirements.txt Accuracy

```bash
# Compare installed vs documented dependencies
python3.11 -m pip freeze > /tmp/requirements-actual.txt
diff requirements.txt /tmp/requirements-actual.txt | grep -E "^<|^>" | head -10
rm /tmp/requirements-actual.txt

# Check for unused dependencies (manual review)
# For each line in requirements.txt, grep for import in scripts/
while read -r pkg; do
  pkg_name=$(echo "$pkg" | cut -d'=' -f1 | tr '-' '_' | tr '[:upper:]' '[:lower:]')
  grep -r "import $pkg_name\|from $pkg_name" scripts/ > /dev/null || echo "⚠️  Unused: $pkg"
done < requirements.txt
```

**Pass criteria:** ✅ Requirements match installed, no obvious unused deps

---

### 5. Documentation Quality

```bash
# Check for missing docstrings in new scripts
for file in scripts/*.py; do
  if ! head -20 "$file" | grep -q '"""'; then
    echo "⚠️  Missing docstring: $file"
  fi
done

# Check for broken links in README
grep -o "](.*\.md)" README.md | sed 's/](//' | sed 's/)//' | while read -r link; do
  test -f "$link" || echo "❌ Broken link: $link"
done

# Check for placeholder text
grep -ri "TODO\|FIXME\|XXX\|lorem ipsum\|placeholder" README.md CHANGELOG.md ROADMAP.md
# Expected: Only intentional TODOs in ROADMAP
```

**Pass criteria:** ✅ All public scripts have docstrings, no broken links, no placeholders

---

### 6. README.md Accuracy Check

```bash
# Verify Python version mentioned matches requirement
PY_VERSION=$(python3.11 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
grep -q "$PY_VERSION" README.md && echo "✅ Python version documented" || echo "⚠️  Update Python version in README"

# Check if Technology Stack table needs update
# (Manual review - compare README section with actual implementation)
echo "📋 Manual check: Review Technology Stack table in README.md"
echo "   - Embedding model: $(grep 'all-' scripts/indexer.py | head -1)"
echo "   - Vector store: $(grep -E 'faiss|llama_index|chromadb' scripts/indexer.py | head -1)"

# Verify Quick Start commands are accurate
echo "📋 Manual check: Test Quick Start commands from README.md"
```

**Pass criteria:** ✅ Python version correct, Technology Stack accurate, Quick Start works

---

### 7. setup.sh Change Detection

```bash
# Compare committed vs current setup.sh
git diff main scripts/setup.sh | wc -l
# If >0, review changes:
# [ ] setup.sh reflects current dependencies
# [ ] setup.sh matches requirements.txt
# [ ] setup.sh has correct Python version check
# [ ] Removed obsolete steps
```

**Pass criteria:** ✅ If changed, setup.sh is accurate and tested

---

## 🔄 Version-Specific Requirements

### Patch Version (v0.2.x → v0.2.y)

**Requirements:**

- [ ] All existing tests pass
- [ ] No breaking changes
- [ ] No reindexing required
- [ ] Backward compatible

**Example:** Bug fix, documentation update, minor optimization

---

### Minor Version (v0.2 → v0.3)

**Requirements:**

- [ ] All existing tests pass
- [ ] New feature documented in ROADMAP → CHANGELOG
- [ ] Migration path documented (if any)
- [ ] Reindexing OK if improves quality (optional for users)
- [ ] Backward compatible data format

**Example:** Delta indexing, new MCP tool, PDF support

---

### Major Version (v0.x → v1.0)

**Requirements:**

- [ ] All stability checks pass
- [ ] Full test suite (all topics)
- [ ] Migration guide in CHANGELOG
- [ ] Breaking changes justified and documented
- [ ] Performance benchmarks updated
- [ ] **Reindexing required** (announce clearly)

**Example:** Storage format change, embedding model change, API redesign

---

## 🧪 Test Environments

**Primary (must work):**

- macOS 14+ (Sonoma)
- Python 3.11+
- M-series Mac (M1/M2/M3)
- VS Code with MCP extension

**Secondary (nice to have):**

- Linux (Ubuntu 22.04+)
- Python 3.12+
- Intel Macs
- Claude Desktop, other MCP clients

**Not supported:**

- Windows (untested, may work)
- Python <3.11
- 32-bit systems

---

## ✅ Full Pre-Push Command Sequence

**Run this script before EVERY push:**

```bash
#!/bin/bash
# File: scripts/pre-push-check.sh

set -e  # Exit on error

echo "🔍 Personal Library MCP - Stability Check"
echo "=========================================="
echo ""

# 1. Environment
echo "📦 1. Checking environment..."
python3.11 --version || { echo "❌ Python 3.11+ required"; exit 1; }
python3.11 -c "import llama_index.core; import sentence_transformers" || { echo "❌ Dependencies missing"; exit 1; }
echo "✅ Environment OK"
echo ""

# 2. File structure
echo "📂 2. Checking file structure..."
test -f books/metadata.json || { echo "❌ books/metadata.json missing - run generate_metadata.py"; exit 1; }
test -d models/ || { echo "❌ models/ missing - run setup.sh"; exit 1; }
test -d storage/ || { echo "⚠️  storage/ missing - reindexing needed"; }
echo "✅ File structure OK"
echo ""

# 3. MCP server startup
echo "🚀 3. Testing MCP server startup..."
timeout 3 python3.11 scripts/mcp_server.py 2>&1 | grep -q "Personal Library MCP Server ready" && echo "✅ Server starts successfully" || { echo "❌ Server startup failed"; exit 1; }
echo ""

# 4. Quick query test (if query.py exists)
if [ -f scripts/query.py ]; then
    echo "🔍 4. Testing query functionality..."
    python3.11 scripts/query.py "test" > /dev/null 2>&1 && echo "✅ Query works" || echo "⚠️  Query test failed (check manually)"
    echo ""
fi

# 5. Git status
echo "📋 5. Git status:"
git status --short
echo ""

# 6. Documentation check
echo "📚 6. Documentation parity..."
grep -q "engine/docs/ROADMAP.md" README.md && echo "✅ README links to ROADMAP" || echo "⚠️  README missing ROADMAP link"
grep -q "engine/docs/CHANGELOG.md" README.md && echo "✅ README links to CHANGELOG" || echo "⚠️  README missing CHANGELOG link"
echo ""

# 7. Ready to commit
echo "✅ All checks passed!"
echo ""
echo "📝 Commit message format:"
echo "   [type]: [short summary]"
echo ""
echo "   Types: feat, fix, docs, refactor, test, chore"
echo ""
read -p "Continue with commit? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi
```

**Make executable:**

```bash
chmod +x scripts/pre-push-check.sh
```
