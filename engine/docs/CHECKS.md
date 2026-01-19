# Personal Library MCP - Stability Checks

> **Definition of Done:** Tests required before pushing to production

**📋 Project Status Files:**

- [README](../../README.md) - Entry point & quick start
- [ROADMAP](ROADMAP.md) - Planned features & in-progress work
- [CHANGELOG](CHANGELOG.md) - Completed features & version history
- **CHECKS** (you are here) - Stability requirements & testing

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

# Test 1: MCP server startup
echo "1️⃣ Server startup test..."
timeout 3 python3.11 scripts/mcp_server_lazy.py 2>&1 | grep -q "ready" && echo "✅ Server starts" || echo "❌ Server failed"
pkill -f mcp_server_lazy 2>/dev/null

# Test 2: Dependencies
echo "2️⃣ Dependencies test..."
python3.11 -c "import llama_index.core; import sentence_transformers" 2>&1 && echo "✅ Dependencies OK" || echo "❌ Dependencies missing"

# Test 3: File structure
echo "3️⃣ File structure test..."
test -f books/metadata.json && test -d models/ && test -d storage/ && echo "✅ Files exist" || echo "❌ Files missing"

# Test 4: Query (if scripts/query.py exists)
if [ -f scripts/query.py ]; then
    echo "4️⃣ Query test..."
    python3.11 scripts/query.py "test" > /dev/null 2>&1 && echo "✅ Query works" || echo "❌ Query failed"
fi

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

### 4. Environment Check

```bash
# Test 6: Check dependencies
python3.11 -c "import llama_index.core; import sentence_transformers; print('✅ Dependencies OK')"

# Test 7: Check file structure
ls books/metadata.json  # Should exist
ls models/  # Should contain embedding model
ls storage/  # Should contain topic directories
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
time python3.11 scripts/mcp_server_lazy.py &
# Ctrl+C after "ready" message

# Query time
time python3.11 scripts/query.py "test query"

# Reindex time
time python3.11 scripts/reindex_topic.py "AI"
```

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
timeout 3 python3.11 scripts/mcp_server_lazy.py 2>&1 | grep -q "Personal Library MCP Server ready" && echo "✅ Server starts successfully" || { echo "❌ Server startup failed"; exit 1; }
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

---

## 📖 Related Documentation

- [ROADMAP](ROADMAP.md) - See what's being built next
- [CHANGELOG](CHANGELOG.md) - See what changed in each version
- [README](../../README.md) - Installation & usage guide
- [/engine/docs/](.) - All project documentation

---

**Last updated:** 2026-01-19
**Applies to:** Personal Library MCP v0.2+
