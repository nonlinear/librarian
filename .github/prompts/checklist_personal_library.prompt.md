# Pre-Commit Checklist: Personal Library MCP

**Purpose:** Ensure code stability and documentation accuracy before pushing changes.

---

## 🔍 Core Questions

### 1. Is the project stable? Is it working?

**Tests to run:**

```bash
# Test MCP server startup
python3.11 scripts/mcp_server.py
# Should start in <0.5s and show "Personal Library MCP Server ready"
# Ctrl+C to stop

# Test indexer (if books changed)
python3.11 scripts/indexer.py
# Should complete without errors

# Test metadata generation (if books changed)
python3.11 scripts/generate_metadata.py
# Should update metadata.json

# Test VS Code integration
# Open VS Code, check if MCP loads in status bar
# Try /library prompt - should respond without errors
```

**Current State Check:**

- [ ] MCP server starts successfully
- [ ] No Python errors or tracebacks
- [ ] .env file exists with valid GOOGLE_API_KEY
- [ ] storage/ directory has index files
- [ ] metadata.json exists and is valid JSON

---

### 2. Did we change setup? If yes, update setup.sh

**Compare current vs committed:**

```bash
git diff scripts/setup.sh
```

**If changed, verify:**

- [ ] setup.sh reflects current dependencies
- [ ] setup.sh matches requirements.txt
- [ ] setup.sh has correct Python version check (3.11+)
- [ ] setup.sh checks for .env file (if using Gemini API)
- [ ] Removed obsolete steps (e.g., download_model.py if not using local embeddings)

**Test setup.sh on clean state:**

```bash
# Backup current env
mv .env .env.backup

# Run setup
./scripts/setup.sh

# Restore
mv .env.backup .env
```

---

### 3. Read README.md - does it still hold true?

**Section-by-section check:**

- [ ] **Technology Stack table** - matches current implementation?
  - Embedding model correct?
  - Vector store correct (FAISS vs LlamaIndex)?
  - Dependencies accurate?

- [ ] **Benchmark table** - numbers still valid?
  - Startup time measured recently?
  - Query latency accurate?

- [ ] **Prerequisites** - complete and accurate?
  - Python version requirement?
  - API keys if needed?
  - Platform-specific instructions?

- [ ] **Dependencies** - matches requirements.txt?

  ```bash
  # Compare README deps with actual requirements
  diff <(grep "pip install" README.md | sort) <(cat requirements.txt | sort)
  ```

- [ ] **Quick Start** - instructions work from scratch?
  - Can a new user follow them?
  - Are file paths correct?
  - Are commands accurate?

- [ ] **Project Status links** - point to roadmap.md and release-notes.md?
  - Check links work
  - No broken references

**Quick validation:**

```bash
# Check for obvious inconsistencies
grep -i "faiss" README.md  # Should not mention FAISS if using LlamaIndex
grep -i "local.*model" README.md  # Should not mention local model if using API
```

---

### 4. Check TODO - what's been done?

**Review current state:**

```bash
# Check for TODO comments in code
grep -r "TODO\|FIXME\|XXX" scripts/ --exclude-dir=deprecated

# Check roadmap.md - what's in progress?
# Check release-notes.md - what's been deployed?
```

**Update documentation:**

- [ ] Create/update commit message with what changed
- [ ] Update roadmap.md if starting new work or completing tasks
- [ ] Move completed groups from roadmap.md to release-notes.md
- [ ] Update README.md if user-facing features changed

**Example release notes entry (add to release-notes.md):**

```markdown
## Phase X: Feature Name ✅ (Jan 17, 2026)

**Problem:** Brief description of what was broken or missing

**Solution Implemented:** What we built

- [x] Key accomplishment 1
- [x] Key accomplishment 2
- [x] Key accomplishment 3

**Impact:** What changed for users (performance, features, etc)
```

**Move completed items:** When a roadmap.md group is 100% done, move it to top of release-notes.md

---

## 🧹 Hygiene Checks

### Code Quality

- [ ] No debug print() statements left in code
- [ ] No commented-out code blocks (move to deprecated/ or delete)
- [ ] No hardcoded paths (use relative paths or environment variables)
- [ ] No API keys in code (should be in .env only)
- [ ] .gitignore covers sensitive files (.env, storage/, etc.)

### File Organization

- [ ] Obsolete files moved to deprecated/ with timestamp
- [ ] No duplicate files (e.g., script.py and script_new.py)
- [ ] requirements.txt matches actual imports
- [ ] No unused dependencies in requirements.txt

### Documentation

- [ ] All new scripts have docstrings
- [ ] README.md has no broken links
- [ ] Code comments explain WHY, not WHAT
- [ ] No lorem ipsum or placeholder text

---

## 📋 Pre-Push Command Sequence

**Run this before every commit:**

```bash
# 1. Check git status
git status

# 2. Review changes
git diff

# 3. Test core functionality
python3.11 scripts/mcp_server.py  # Should start quickly
# Ctrl+C

# 4. Verify README accuracy
grep -i "$(python3.11 --version | cut -d' ' -f2 | cut -d'.' -f1,2)" README.md
# Should find Python version mentioned

# 5. Check for TODOs
grep -r "TODO" scripts/ --exclude-dir=deprecated | wc -l

# 6. Validate requirements
python3.11 -m pip freeze > requirements-actual.txt
diff requirements.txt requirements-actual.txt
rm requirements-actual.txt

# 7. Stage and commit
git add .
git commit -m "descriptive message"

# 8. Push
git push
```

---

## 🚨 Current State Assessment (2026-01-18)

**⚠️ BRANCH STATUS:**

- **main** (stable): Commit 081296f - version BEFORE engine/ refactor
- **dev/mcp-fixes**: WIP branch with MCP fixes (chunking, runtime filtering, VS Code integration)
  - ⚠️ DO NOT MERGE until tested and stable
  - Contains: improved chunking (SentenceSplitter), runtime filtering, integration scripts

**Recent Changes (on main):**

- ✅ Using stable version without engine/ refactor
- ✅ Extension points to correct paths (scripts/, not engine/scripts/)

**Check project status:**

```bash
# What's in progress?
cat roadmap.md | grep "🔶\|❌" -A 5

# What was just completed?
head -30 release-notes.md
```

**Before starting work:**

- [ ] Read roadmap.md to understand current priorities
- [ ] Check if your work fits an existing group or needs new one
- [ ] Update roadmap.md when starting new tasks

**Before pushing:**

- [ ] Run full test sequence above
- [ ] Update roadmap.md with progress
- [ ] If group is 100% done, move to release-notes.md with date
- [ ] Update README.md if user-facing changfore full reindex

4. Use `git stash` to save work-in-progress
5. Create a feature branch for big changes

**Common mistakes:**

- Forgetting to update requirements.txt after pip install
- Changing code but not updating README benchmarks
- Leaving debug code in production
- Not testing .env-template (copy it to .env-test and validate)

**Good commit messages:**

```
✅ Good: "refactor: migrate from FAISS to LlamaIndex, reduce startup time to <0.5s"
❌ Bad: "fix stuff"
```
