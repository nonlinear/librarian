# Roadmap Tasks Sync

**DESCRIPTION:** Syncs ROADMAP tasks with actual work done. Auto-marks completed tasks, adds undocumented work.  
**TYPE:** interpretive  
**SCOPE:** global

**Applies to:** All epic branches with ROADMAP tasks

---

## What This Check Does

**AI compares ROADMAP tasks vs actual git commits/changes and syncs status.**

**Conservative heuristic:** Only mark `[x]` if HIGH CONFIDENCE task is done. When in doubt, leave `[ ]`.

**User can manually mark tasks too.**

---

## Workflow

### 1. Detect Epic Branch

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
# Extract version: v1.0.1 → VERSION=1.0.1
```

### 2. Read ROADMAP Tasks

Extract tasks from `## vX.Y.Z` section in `backstage/ROADMAP.md`:

```markdown
**Tasks:**
- [ ] can we merge? what do we use?
- [ ] Frontmatter for each
- [ ] Naming
- [x] Design merged structure
```

### 3. Read Git History

**Get commits in this branch (since diverged from main):**

```bash
git log main..HEAD --oneline
```

**Example output:**
```
351c5e0 Fix roadmap-tasks.sh: extract epic section correctly
a322778 Fix navigation-syntax.sh: remove typo 'r'
517843d WIP: v1.0.1 merge policies into checks
```

### 4. Read File Changes

**Detect what actually changed:**

```bash
git diff --name-status main..HEAD
```

**Example output:**
```
M README.md
A backstage/checks/global/epic-branch.sh
D backstage/checks/global/roadmap-epic-format.sh
```

### 5. Match Tasks to Evidence

**For each task in ROADMAP:**

**High confidence patterns (mark `[x]`):**
- Task: "Naming" → Commits mention "rename", "naming convention" → `[x]`
- Task: "Design merged structure" → Files exist in new structure → `[x]`
- Task: "Frontmatter for each" → Files have frontmatter comments → `[x]`

**Low confidence (keep `[ ]`):**
- Task: "can we merge? what do we use?" → Discussion task, no direct evidence
- Task: "boa noite, precisa?" → Question, needs user decision

**Ambiguous (keep `[ ]`):**
- Task: "Test" → Some tests may exist, but not comprehensive

### 6. Add Undocumented Work

**Detect work done but NOT in task list:**

**Example:**
- Created `epic-branch.sh` (not listed) → Add: `- [x] Create epic-branch check`
- Fixed typo in `navigation-syntax.sh` (not listed) → Add: `- [x] Fix navigation-syntax typo`

**Conservative:** Only add OBVIOUS new work (new files, major features, critical fixes).

### 7. Update ROADMAP

**Edit `backstage/ROADMAP.md` in place:**

```markdown
**Tasks:**
- [ ] can we merge? what do we use? (no evidence, keep [ ])
- [x] Frontmatter for each (files have frontmatter)
- [x] Naming (commits show renaming work)
- [x] Design merged structure (new structure exists)
- [x] Create epic-branch check (NEW - discovered work)
- [x] Fix navigation-syntax typo (NEW - discovered work)
```

### 8. Report Changes

**Output:**
```
📋 Roadmap Tasks Sync (v1.0.1):

✅ Marked complete (high confidence):
  - Frontmatter for each
  - Naming
  - Design merged structure

➕ Added undocumented work:
  - Create epic-branch check
  - Fix navigation-syntax typo

📊 Progress: 5/7 tasks done (2 remaining)

⚠️  Manual review needed:
  - "can we merge? what do we use?" (discussion task)
  - "boa noite, precisa?" (needs user decision)
```

---

## AI Decision Rules

**Mark `[x]` (high confidence) when:**
- Task mentions file/folder → file/folder exists in git diff
- Task mentions "rename" → commits show rename operations
- Task mentions "create X" → X exists in new files
- Task mentions "fix Y" → commits mention "fix Y"
- Task mentions "update Z" → Z file modified in git diff

**Keep `[ ]` (low confidence) when:**
- Task is a question (needs user input)
- Task is discussion/decision (no direct code evidence)
- Task is "test" but no test files added
- Ambiguous wording (could mean many things)

**Add new task when:**
- New file created (not mentioned in any task)
- Major refactor/rename (not mentioned)
- Critical bugfix (not mentioned)

---

## Example Session

**AI reads epic v1.0.1 tasks:**
```
- [ ] can we merge? what do we use?
- [ ] Naming
- [ ] Design merged structure
```

**AI reads commits:**
```
Fix roadmap-tasks.sh: extract epic section correctly
Fix navigation-syntax.sh: remove typo 'r'
WIP: v1.0.1 merge policies into checks
```

**AI reads file changes:**
```
A backstage/checks/global/epic-branch.sh
M backstage/checks/global/navigation-syntax.sh
```

**AI updates ROADMAP:**
```
- [ ] can we merge? what do we use? (question, no evidence)
- [x] Naming (commits show file renaming)
- [x] Design merged structure (new files in checks/global/)
- [x] Fix navigation-syntax typo (NEW - commit evidence)
- [x] Create epic-branch check (NEW - file evidence)
```

**AI reports:**
```
✅ 4/5 done, 1 manual review needed
```

---

## Future Automation

When patterns stabilize, convert to deterministic (.sh):
- Regex match task → commit message
- File existence checks
- Diff analysis (added/deleted/modified)

For now: **AI reads evidence, applies conservative heuristic, updates ROADMAP.**
