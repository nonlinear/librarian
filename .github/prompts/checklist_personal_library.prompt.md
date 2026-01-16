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

- [ ] **Roadmap** - checkboxes updated?
  - Mark completed features with [x]
  - Add new planned features
  - Remove obsolete items

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

# Check GitHub issues (if using)
# Check project board (if using)
```

**Update documentation:**

- [ ] Create/update CHANGELOG.md or commit message with what changed
- [ ] Update Roadmap in README.md
- [ ] Move completed items from TODO to DONE

**Example changelog entry:**

```markdown
## [Unreleased] - 2026-01-15

### Changed

- Migrated from FAISS to LlamaIndex native vector store
- Switched from local embeddings (all-MiniLM-L6-v2) to Gemini API (embedding-001)
- Updated setup.sh to remove model download step
- Improved startup time from 4s to <0.5s

### Added

- .env-template with API key instructions
- Gemini API key requirement in setup

### Deprecated

- scripts/deprecated/mcp_server_faiss.py
- scripts/deprecated/indexer_faiss.py

### Removed

- Local embedding model dependency
- Manual FAISS index management
```

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

## 🚨 Current State Assessment (2026-01-15)

**Recent Changes:**

- ✅ Migrated FAISS → LlamaIndex
- ✅ Updated README.md (6 sections)
- ✅ Updated setup.sh (removed model download)
- ✅ Updated .env-template

**Not Yet Done:**

- ⏳ Test new mcp_server.py with LlamaIndex
- ⏳ Reindex books with new indexer.py
- ⏳ Update requirements.txt (remove sentence-transformers, faiss-cpu)
- ⏳ Test VS Code MCP integration end-to-end
- ⏳ Measure actual startup time (<0.5s claim)
- ⏳ Remove obsolete scripts (download_model.py, reindex_gemini.py)

**Before Next Push:**

- [ ] Run full test sequence above
- [ ] Update requirements.txt
- [ ] Test indexer.py on sample book
- [ ] Measure and document performance
- [ ] Clean up obsolete files

---

## � Final Report

After completing all checks, review the [README.md roadmap](../../README.md#project-progress-roadmap) and provide:

### 1. What I Did

- Summary of changes made in this session
- Files modified/created/deleted
- Tests run and results

### 2. Last Completed Feature

- Find the most recent `[x]` item in the roadmap
- Brief context: what was it? (1-2 sentences max)
- When: "2 weeks ago", "3 months ago", "2 days ago" (check git log if needed)
- Jog memory with brief conversation context if relevant

### 3. Next Steps

- List upcoming `[ ]` features from roadmap
- Ask: "Which feature should we tackle next?"

---

## �💡 Tips

**When in doubt:**

1. Read the copilot-instructions.md
2. Check deprecated/ for old working versions
3. Test on a single book before full reindex
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
