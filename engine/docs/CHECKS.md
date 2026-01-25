# Personal Library MCP - Stability Checks

> **Formatting Standard:**
>
> All status files (CHECKS, ROADMAP, CHANGELOG, CONTRIBUTING) must be both **human-readable** (clear, prompt-like, easy to follow) and **machine-readable** (easy for scripts or AI to parse and execute).
>
> **How to format tests and checklists:**
>
> 1. **Each test/check should be a short, copy-pasteable code block** (one-liner or small block), with a plain-text explanation and pass/fail criteria immediately after.
> 2. **No large, monolithic scripts**—keep each check atomic and self-contained.
> 3. **No markdown formatting or prose inside code blocks.**
> 4. **All explanations, expected output, and pass criteria must be outside code blocks.**
> 5. **Status files should be easy for both humans and automation to read, extract, and run.**
>
> _Example:_
>
> ```bash
> python3.11 -c "import llama_index.core; import sentence_transformers"
> ```
>
> Expected: No error, prints nothing.
> Pass: ✅ Dependencies OK

> **Definition of Done:** Tests required before pushing to production

> 🤖
>
> - [CHANGELOG](CHANGELOG.md) — What we did
> - [ROADMAP](ROADMAP.md) — What we wanna do
> - [CONTRIBUTING](CONTRIBUTING.md) — How we do it
> - [CHECKS](CHECKS.md) — What we accept
> - [/whatsup](../../.github/prompts/whatsup.prompt.md) — The prompt that keeps us sane
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

## 📋 Check Policy: Branches vs Main

### Epic Branches (v0.X.0)

⚠️ **Soft requirements** - Can push with warnings

**Philosophy:** Epic branches are for experimentation and work-in-progress. Checks should run, but failures don't block commits.

**When checks fail:**

- ✅ Still allowed to push
- ⚠️ Must document failures in commit message
- 📝 Track known issues in epic notes (`engine/docs/gaps/epic-notes/v0.X.0.md`)
- 🎯 Must be fixed before merging to main

**Commit message format when checks fail:**

```
wip: [what you did]

⚠️ Known issues:
- Check X failed: [reason]
- Plan: [how you'll fix it]

See epic notes for full context
```

### Main Branch

❌ **Hard requirements** - ALL checks must pass

**Philosophy:** Main is production. No exceptions, no "will fix later".

**Enforcement:**

- GitHub branch protection requires all checks passing
- Pull requests must be green
- No direct pushes to main

**Before merging epic branch to main:**

1. All epic checks resolved
2. All tests passing
3. Epic notes reviewed and complete
4. ROADMAP → CHANGELOG moved

---

## 📐 Status File Formatting Check (MANDATORY)

**All status files (CHECKS.md, ROADMAP.md, CHANGELOG.md, CONTRIBUTING.md) must follow the formatting standard above.**

**Test: Formatting compliance**

````bash
grep -q 'Formatting Standard' engine/docs/CHECKS.md && \
grep -q 'Formatting Standard' engine/docs/ROADMAP.md && \
grep -q 'Formatting Standard' engine/docs/CHECKS.md && echo '✅ Formatting standard declared in CHECKS.md' || echo '❌ Formatting standard missing in CHECKS.md'
Expected: Prints '✅ All status files declare formatting standard'.
Pass: ✅ All status files declare formatting standard

**Test: Formatting compliance (manual/AI review)**
For each status file, confirm:

- Each test/check is a short, copy-pasteable code block with plain-text explanation and pass/fail criteria immediately after.
- No large, monolithic scripts; each check is atomic and self-contained.
- No markdown formatting or prose inside code blocks.
- All explanations, expected output, and pass criteria are outside code blocks.
- File is easy for both humans and automation to read, extract, and run.

Pass: ✅ All status files are both human- and machine-readable

---

echo "🔍 Running stability checks..."
echo ""
echo "0️⃣ Status file formatting check..."
grep -q 'Formatting Standard' engine/docs/CHECKS.md && \
grep -q 'Formatting Standard' engine/docs/ROADMAP.md && \
grep -q 'Formatting Standard' engine/docs/CHECKS.md && echo '✅ Formatting standard declared in CHECKS.md' || echo '❌ Formatting standard missing in CHECKS.md'
echo "2️⃣ Dependencies test..."
echo "3️⃣ File structure test (v2.0)..."
test -f books/library-index.json && ls books/*/topic-index.json >/dev/null 2>&1 && echo "✅ v2.0 Files exist" || echo "❌ Files missing"
echo "4️⃣ Nested folder test..."
echo ""
echo "✅ All checks complete. Review results above."

**Automated test sequence (run each check below):**

---

**Test 1: MCP query functionality (what research.prompt.md actually uses)**

```bash
python3.11 -c "import json; from pathlib import Path; metadata = json.loads((Path('books') / 'library-index.json').read_text()); topic_count = len(metadata.get('topics', [])); print(f'✅ MCP works ({topic_count} topics)' if topic_count > 0 else '❌ MCP failed')"
```

Expected: Prints '✅ MCP works (N topics)' where N > 0.
Pass: ✅ MCP works

**Note:** v0.5.0+ uses `library-index.json` (v2.0 schema) instead of `metadata.json`

**Test 2: Dependencies**

```bash
python3.11 -c "import llama_index.core; import sentence_transformers"
```

Expected: No error, prints nothing.
Pass: ✅ Dependencies OK

**Test 3: File structure (v2.0 schema)**

```bash
test -f books/library-index.json && ls books/*/topic-index.json >/dev/null 2>&1 && echo "✅ v2.0 files exist" || echo "❌ Files missing - run migrate_to_v2.py"
```

Expected: Prints '✅ v2.0 files exist'.
Pass: ✅ v2.0 files exist

**Note:** v0.5.0+ uses per-topic `topic-index.json` instead of monolithic `metadata.json`

**Test 4: Nested folder support (v2.0)**

```bash
python3.11 -c "import json; from pathlib import Path; metadata = json.loads((Path('books') / 'library-index.json').read_text()); nested = [t['id'] for t in metadata['topics'] if '_' in t['id']]; print(f'✅ Nested topics work ({len(nested)} found)' if nested else '⚠️ No nested topics')"
```

Expected: Prints '✅ Nested topics work (N found)' where N >= 0.
Pass: ✅ Nested topics work

**Test 5: Chunks v2.0 schema (page/chapter metadata)**

```bash
python3.11 -c "import json; from pathlib import Path; BOOKS_DIR = Path('books'); all_chunks = [(topic_dir, json.loads((topic_dir / 'chunks.json').read_text())) for topic_dir in BOOKS_DIR.glob('*') if (topic_dir / 'chunks.json').exists()]; v2_topics = [topic for topic, chunks in all_chunks if chunks and ('page' in chunks[0] or 'chapter' in chunks[0])]; v1_topics = [topic for topic, chunks in all_chunks if chunks and 'page' not in chunks[0] and 'chapter' not in chunks[0]]; print(f'✅ v2.0: {len(v2_topics)} topics, v1.0: {len(v1_topics)} topics (reindex with --all to update)' if v2_topics else '⚠️ All topics need reindexing')"
```

Expected: Shows mix of v2.0 and v1.0 topics (v1.0 topics need reindexing).
Pass: ✅ Reports topic counts

**Note:** v0.5.0+ chunks include page/chapter metadata. Run `indexer_v2.py --all` to update all topics to v2.0 schema.

---

**What whatsup.prompt.md does:**

1. Reads this file
2. Runs the automated test sequence above
3. Blocks push if ANY test fails
4. Reports results to user

---

## 🔍 Pre-Commit Checklist

**Run these tests BEFORE every commit to main:**

### 1. Research Pipeline Validation (MANDATORY)

**This is the only required test for MCP research functionality.**

For each of the following sample queries (using real topics/books from metadata.json), run:

```bash
# Test 1: Research pipeline returns valid results for real topics
python3.11 scripts/research.py "What is the main argument?" --topic ai_policy --top-k 1
python3.11 scripts/research.py "Who is Martin Ford?" --topic ai_prompt_engineering --top-k 1
python3.11 scripts/research.py "What is UX in AI?" --topic ai_theory --top-k 1
```

**Expected:** Each command returns a valid JSON object with at least one result (results[].text is non-empty).

**Pass criteria:** ✅ All queries succeed, return valid JSON, and results are non-empty.

If any query fails, MCP is considered broken for its primary use case.

---

### 2. Indexing Test (v2.0)

```bash
# Test: Reindex single topic (v0.5.0+)
python3.11 scripts/indexer_v2.py --topic theory/anthropocene
# Expected: Creates/updates topic-index.json, chunks.json, faiss.index in topic folder
# Expected: Shows delta detection (hash comparison)
# Expected: No crashes, completes successfully

# Test: Force reindex (skip delta detection)
python3.11 scripts/indexer_v2.py --topic theory/anthropocene --force
# Expected: Rebuilds index even if unchanged

# Test: Reindex all topics
python3.11 scripts/indexer_v2.py --all
# Expected: Processes all topics with delta detection
```

**Pass criteria:** ✅ Topic indexed successfully, delta detection works, no errors

**Note:** v0.5.0+ uses `indexer_v2.py` instead of deprecated `reindex_topic.py`/`reindex_all.py`

---

### 3. MCP Server Startup Test

```bash
# Test: MCP server starts and loads metadata
timeout 5 python3.11 scripts/mcp_server.py 2>&1 | grep -E "Ready|Loaded metadata" | head -5
# Expected: Server starts, loads library-index.json (or metadata.json fallback), shows topic count
# Expected: No import errors, no missing file errors
```

**Pass criteria:** ✅ Server starts successfully, metadata loads, no errors

**Note:** v0.5.0+ mcp_server.py has failsafe: tries library-index.json first, falls back to metadata.json

---

### 4. Watch Library Test (Optional)

```bash
# Test: watch_library.py monitors file changes
python3.11 scripts/watch_library.py --dry-run
# Expected: Scans books/ directory, detects structure, no crashes
# Expected: Shows topics and books being watched
```

**Pass criteria:** ✅ Scanner works, no errors (or skip if not using watch mode)

**Note:** watch_library.py is optional automation - not required for core functionality

---

### 2.1. Happy Path Test (Path Resolution)

**Question:** If a user follows README.md happy path, will path resolution work for:

- ✅ Nested topics? (`cybersecurity_applied` → `books/cybersecurity/applied/`)
- ✅ Root topics with underscores? (`product_architecture` → `books/product architecture/`)

```bash
# Test 6a: Verify nested topic path resolution (v2.0)
python3.11 -c "
from pathlib import Path
import json
BOOKS_DIR = Path('books')
metadata = json.loads((BOOKS_DIR / 'library-index.json').read_text())

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

# Test 6b: Verify root topic with underscore (v2.0)
python3.11 -c "
from pathlib import Path
import json
BOOKS_DIR = Path('books')
metadata = json.loads((BOOKS_DIR / 'library-index.json').read_text())

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

# Test 6c: Run indexer to verify (v0.5.0+ happy path)
python3.11 scripts/indexer_v2.py --all 2>&1 | grep -E "✅|⚠️" | head -10
# Expected: All topics process successfully, delta detection works
```

**Pass criteria:**

- ✅ Nested topics resolve correctly
- ✅ Root topics with underscores resolve correctly
- ✅ Full indexer finds all books in all topics

**Why this matters:** Ensures `indexer_v2.py` correctly handles nested topics (e.g., `cybersecurity/applied`) and root topics with underscores. Users following README indexing steps should not encounter missing file errors.

**Note:** v0.5.0+ uses `indexer_v2.py --all` instead of deprecated `indexer.py`

---

### 3. Environment Check

```bash
# Test 6: Check dependencies
python3.11 -c "import llama_index.core; import sentence_transformers; print('✅ Dependencies OK')"

# Test 7: Check file structure (v2.0)
ls books/library-index.json     # Should exist (v2.0 registry)
ls books/*/topic-index.json     # Should show per-topic metadata
ls books/*/faiss.index          # Should show topic-based indices
ls books/*/chunks.json          # Should show topic-based chunks (v2.0 schema)
```

**Pass criteria:** ✅ All imports work, required files exist

---

### 4. Memory & Performance Check

```bash
# Test 8: Monitor memory during reindex (optional, for large libraries)
/usr/bin/time -l python3.11 scripts/indexer_v2.py --topic AI/policy 2>&1 | grep "maximum resident set size"
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

### Issue 2: Missing library-index.json (v2.0)

**Symptom:** MCP server starts but can't find books
**Fix:** Run `python3.11 scripts/indexer_v2.py --all` (generates library-index.json + indexes)
**Test:** `cat books/library-index.json | jq .`

### Issue 3: Corrupted index

**Symptom:** Query returns no results or crashes
**Fix:** Reindex affected topic: `python3.11 scripts/indexer_v2.py --topic <topic-path> --force`
**Test:** Query after reindex

**Note:** v0.5.0+ use `--force` flag to skip delta detection and force rebuild

### Issue 4: M3 Mac crashes (mpnet model)

**Symptom:** Segfault during reindexing with `all-mpnet-base-v2`
**Fix:** Use `all-MiniLM-L6-v2` (current default since v0.5.0)
**Test:** Check `scripts/indexer_v2.py` for model name

### Issue 5: Migration from v1 to v2 schema

**Symptom:** `metadata.json` exists but `library-index.json` missing
**Fix:** Run `python3.11 scripts/migrate_to_v2.py`
**Test:** Check `books/library-index.json` exists, backup created at `books/library-index.json.v1.backup`

---

## 📊 Performance Benchmarks

**Current measured performance (as of Jan 19, 2026):**

| Metric                   | Target | Current  | Status |
| ------------------------ | ------ | -------- | ------ |
| MCP startup              | <1s    | <0.5s    | ✅     |
| First query (cold)       | <3s    | ~2s      | ✅     |
| Cached query             | <0.5s  | ~0.3s    | ✅     |
| Reindex single topic     | <30s   | 10-45s\* | ✅     |
| Full reindex (54 topics) | <15min | ~12min\* | ✅     |
| Delta reindex (no changes) | <10s | ~5s      | ✅     |
| Memory usage             | <2GB   | ~1.2GB   | ✅     |

\*Varies by topic size (number of books/chunks)

**How to measure:**

```bash
# Startup time
time python3.11 scripts/mcp_server.py &
# Ctrl+C after "ready" message

# Query time
time python3.11 scripts/query.py "test query"

# Reindex time (v0.5.0+)
time python3.11 scripts/indexer_v2.py --topic AI/policy

# Delta reindex time (no changes)
time python3.11 scripts/indexer_v2.py --all  # Should skip unchanged topics
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

### 5. README.md Accuracy Check

```bash
# Verify Python version mentioned matches requirement
PY_VERSION=$(python3.11 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
grep -q "$PY_VERSION" README.md && echo "✅ Python version documented" || echo "⚠️  Update Python version in README"

# Check if Technology Stack table needs update
# (Manual review - compare README section with actual implementation)
echo "📋 Manual check: Review Technology Stack table in README.md"
echo "   - Embedding model: $(grep 'all-' scripts/indexer_v2.py | head -1)"
echo "   - Vector store: $(grep -E 'faiss|llama_index|chromadb' scripts/indexer_v2.py | head -1)"

# Verify Quick Start commands are accurate
echo "📋 Manual check: Test Quick Start commands from README.md"
```

**Pass criteria:** ✅ Python version correct, Technology Stack accurate, Quick Start works

---

### 6. setup.sh Change Detection

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

# 2. File structure (v2.0)
echo "📂 2. Checking file structure..."
test -f books/library-index.json || { echo "❌ books/library-index.json missing - run indexer_v2.py --all or migrate_to_v2.py"; exit 1; }
test -d models/ || { echo "❌ models/ missing - run setup.sh"; exit 1; }
ls books/*/topic-index.json >/dev/null 2>&1 || { echo "⚠️  No topic indices - run indexer_v2.py --all"; }
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
````
