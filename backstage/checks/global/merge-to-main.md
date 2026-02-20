# Merge to Main Workflow

**DESCRIPTION:** Merges to main follow protocol. Prevents unvetted code on main branch.  
**TYPE:** interpretive  
**SCOPE:** global

**Applies to:** All projects using backstage protocol

---

## Trigger Logic

**This check is ACTIVATED BY `roadmap-tasks.sh` when:**
- Epic branch detected (`v*.*.*` or `epic/*`)
- All tasks in epic marked done (`- [x]`)

**roadmap-tasks.sh output triggers this:**
```
✅ All tasks complete in epic v0.5.0
🚦 Ready for merge-to-main workflow
```

---

## Pre-Merge Checklist

**AI verifies ALL before allowing merge:**

1. ✅ **All tasks done** (already verified by roadmap-tasks.sh)
2. ✅ **All checks pass** (run all deterministic checks)
3. ✅ **Move epic from ROADMAP → CHANGELOG**
4. ✅ **Merge to main** with milestone commit message
5. ✅ **Mark branch deprecated** (keep branch, don't delete)

---

## Workflow Steps

### Step 0: Rebase Main (Keep Branch Current)

**Before merging, sync with latest main:**

```bash
# From epic branch
git fetch origin
git rebase origin/main

# If conflicts:
git status                    # See conflicts
# Fix conflicts in editor
git add <resolved-files>
git rebase --continue

# If rebase gets messy:
git rebase --abort           # Start over, ask for help
```

**Why rebase first?**
- Ensures epic includes latest main changes
- Reduces chance of merge conflicts
- Makes merge cleaner (linear history)
- Catches integration issues BEFORE merge

**After rebase: re-run checks!** (code changed, verify still passes)

---

### Step 1: Verify All Checks Pass (On Branch)

```bash
# Run all checks on epic branch
backstage start

# Expected: all ✅
```

**If ANY check fails → STOP, fix issues first.**

---

### Step 2: Move Epic ROADMAP → CHANGELOG

**Extract from ROADMAP.md:**
```markdown
## v0.5.0

### Epic Title

**Tasks:**
- [x] Task 1
- [x] Task 2

**Success:** All done
```

**Move to CHANGELOG.md (top of file):**
```markdown
## v0.5.0 - 2026-02-20

### Epic Title

**Completed:**
- Task 1
- Task 2

**Success criteria met:** All done
```

**Remove from ROADMAP.md** (or move to "Completed Epics" section if exists)

---

### Step 3: Commit CHANGELOG Changes

```bash
git add CHANGELOG.md ROADMAP.md
git commit -m "Move v0.5.0 to CHANGELOG"
```

---

### Step 4: Merge to Main with Milestone Message

**Merge commit format:**
```
milestone: v0.5.0 - Epic Title
```

**Example:**
```
milestone: v0.5.0 - Home Assistant Voice Integration
```

**Commands:**
```bash
git checkout main
git merge --no-ff v0.5.0 -m "milestone: v0.5.0 - Epic Title"
git tag v0.5.0
```

**DON'T PUSH YET!** (verify main checks pass first)

---

### Step 5: Verify Main Checks Pass (Post-Merge)

**After merge, verify main is still clean:**

```bash
# Still on main branch
backstage start

# Expected: all ✅
```

**Why check main after merge?**
- Rebase might have missed integration issues
- Merge commit might introduce problems
- Main must ALWAYS be clean (never push broken main)

**If checks fail on main:**
```bash
git reset --hard HEAD~1       # Undo merge
git checkout v0.5.0           # Back to epic branch
# Fix issues, then retry merge workflow
```

---

### Step 6: Push Main + Tags

**Only push if Step 5 passed:**

```bash
git push origin main --tags
```

---

### Step 7: Mark Branch Deprecated (Keep, Don't Delete)

**How to deprecate branch:**

**Option A: Commit deprecation notice**
```bash
git checkout v0.5.0
echo "# DEPRECATED\n\nThis epic is complete and merged to main at v0.5.0.\n\nDo not base new work on this branch." > DEPRECATED.md
git add DEPRECATED.md
git commit -m "Mark branch deprecated (merged to main)"
git push origin v0.5.0
```

**Option B: Branch description (GitHub/GitLab)**
```bash
# GitHub CLI
gh api repos/:owner/:repo/git/refs/heads/v0.5.0 \
  --field description="[DEPRECATED] Merged to main at v0.5.0"
```

**Option C: Protected branch tag**
```bash
git tag -a "v0.5.0-deprecated" -m "Branch deprecated, merged to main"
git push origin v0.5.0-deprecated
```

**Why keep branch?**
- Historical reference
- Epic notes preserved
- Can cherry-pick specific commits later
- Audit trail

---

## What AI Should Do

**When roadmap-tasks.sh reports "all tasks done":**

1. **Ask user:** "Epic v0.5.0 complete. Ready to merge to main?"
2. **If yes:**
   - **Step 0:** Rebase main (sync with latest)
   - **Step 1:** Run checks on branch (verify still passes after rebase)
   - **Step 2:** Move ROADMAP → CHANGELOG
   - **Step 3:** Commit changes
   - **Step 4:** Merge to main with milestone message + tag
   - **Step 5:** Run checks on main (verify merge didn't break anything)
   - **Step 6:** Push main + tags (only if Step 5 passes)
   - **Step 7:** Deprecate epic branch
   - Report success
3. **If no:** "Noted. Run `backstage merge` when ready."

---

## Output Format

```
🚦 Merge to Main: v0.5.0 → main

✅ Step 0: Rebased main (branch current)
✅ Step 1: All checks passed (branch)
✅ Step 2: ROADMAP moved to CHANGELOG
✅ Step 3: Changes committed
✅ Step 4: Merged with milestone commit + tagged v0.5.0
✅ Step 5: All checks passed (main)
✅ Step 6: Pushed main + tags
✅ Step 7: Branch marked deprecated

Status: MERGED ✅
Next: Epic v0.6.0 ready to start
```

---

## Enforcement

**Hard fail if:**
- Any check fails
- Tasks incomplete (roadmap-tasks.sh should prevent this)
- CHANGELOG entry malformed

**Merge blocked until all ✅**

---

## Future Automation

One command: `backstage merge`
- Auto-run checks
- Auto-move ROADMAP → CHANGELOG
- Auto-commit + merge + tag
- Auto-deprecate branch

For now: **AI guides manual workflow.**
