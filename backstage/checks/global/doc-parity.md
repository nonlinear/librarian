# Documentation-Reality Parity Check

**DESCRIPTION:** Documentation reflects actual system behavior. Prevents doc-reality drift.  
**TYPE:** interpretive  
**SCOPE:** global

**Applies to:** All projects with documentation

---

## What This Check Does

**AI compares documentation vs actual system state and REPORTS drift.**

Does NOT auto-fix. Only reports what's out of sync.

---

## Drift Patterns to Detect

### 1. Code Changes vs README Tutorial
- README shows `import { oldFunction }` but code exports `newFunction`
- Tutorial references removed files
- Examples use deprecated syntax

### 2. API Changes vs Documentation
- Endpoints changed but docs still reference old routes
- Parameters added/removed but docs unchanged
- Response formats changed but examples outdated

### 3. Behavior Changes vs Description
- README says "does X" but code actually does Y
- Features removed but still documented
- New features exist but undocumented

### 4. Structure Changes vs Guides
- Folders reorganized but docs reference old paths
- Scripts renamed but installation guide outdated
- Dependencies changed but requirements.txt unchanged

---

## How AI Should Check

**On every backstage run:**

1. **Read README.md, CHANGELOG.md, any /docs folder**
2. **Scan actual codebase** (imports, exports, functions, structure)
3. **Compare documentation claims vs reality**
4. **Report drift** (what's out of sync, severity)

**Output format:**

```
⚠️  Documentation-Reality Drift Detected:

📄 README.md line 42:
   Claims: "Run setup.sh to install"
   Reality: setup.sh doesn't exist (renamed to install.sh)
   
📄 docs/api.md line 15:
   Claims: "POST /api/users endpoint"
   Reality: Endpoint is now /api/v2/users
   
📄 CHANGELOG.md:
   Missing: 3 commits since last entry (2024-02-15)
   Reality: Last commit 2024-02-20
```

---

## Enforcement

**On epic branches:** Warn only (soft fail)  
**On merge to main:** BLOCK merge (hard fail)

**Why block?**  
Main = stable + documented. Drift = broken trust.

**How to fix:**  
Add drift items to ROADMAP as tasks, fix before merge.

---

## Example Session

**AI:** "⚠️  Doc-parity check failed. README mentions `parse.py` (line 23) but file doesn't exist. Add fix to ROADMAP?"

**User:** "Yes, add to current epic"

**AI:** Adds task to ROADMAP: `[ ] Update README: parse.py → analyzer.py`

---

## Future Automation

When this becomes deterministic (.sh):
- Parse code structure automatically (AST, exports, functions)
- Compare with documented examples
- Generate diff report
- Suggest fixes (line-by-line)

For now: **AI reads, compares, reports manually.**
