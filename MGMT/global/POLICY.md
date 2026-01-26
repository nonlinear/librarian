# Global Policy

> Universal workflow rules that apply across all projects using this MGMT system.

**Inspired by:** Elinor Ostrom's polycentric governance framework—multiple centers of power (global/project) with overlapping, not hierarchical, jurisdictions.

---

## Purpose

This file contains **universal, project-agnostic** workflow rules and conventions.

**POLICY.md** (project-specific) extends or overrides these global rules for specific projects.

---

## Formatting Standard

All status files (CHECKS, ROADMAP, CHANGELOG, POLICY) must be both **human-readable** (clear, prompt-like, easy to follow) and **machine-readable** (easy for scripts or AI to parse and execute).

**How to format tests and checklists:**

1. **Each test/check should be a short, copy-pasteable code block** (one-liner or small block), with a plain-text explanation and pass/fail criteria immediately after.
2. **No large, monolithic scripts**—keep each check atomic and self-contained.
3. **No markdown formatting or prose inside code blocks.**
4. **All explanations, expected output, and pass criteria must be outside code blocks.**
5. **Status files should be easy for both humans and automation to read, extract, and run.**

_Example:_

```bash
python3.11 -c "import llama_index.core; import sentence_transformers"
```

Expected: No error, prints nothing.
Pass: ✅ Dependencies OK

---

## Branch Strategy

**One branch per epic:**

```
main (stable releases only)
  ↓
v0.3-feature-name (feature branch)
v0.4-another-feature (feature branch)
v0.5-third-feature (feature branch)
```

### Branch Naming

**Examples:**

- `v0.3-delta-indexing`
- `v0.4-provider-integration`
- `v1.0-breaking-changes`

### Workflow

1. **Create branch from main**
2. **Work on epic in branch**
3. **Rebase regularly from main**
4. **Merge to main when complete**
5. **Tag release**
6. **Delete feature branch (recommended)**

---

## Epic/Branch Workflow ("Epic Dance")

### 🔍 Before Starting New Work: Review Epic Notes

**CRITICAL:** Always check existing epic notes before starting similar work to avoid reinventing the wheel.

```bash
# List all epic notes
ls MGMT/epic-notes/

# Search for relevant keywords
grep -r "keyword" MGMT/epic-notes/
```

**Why epic notes matter:**

- **Discovered blockers:** Previous epics may have hit technical limitations
- **Tested solutions:** Multiple approaches already tried and documented
- **Documented workarounds:** Pragmatic solutions when ideal ones don't work
- **Deferred features:** Features intentionally postponed with reasoning

**When to check:**

- Starting any new epic (especially similar features)
- Encountering unexpected behavior
- Considering a feature that "feels like it was tried before"
- Planning technical approaches

**Epic notes = knowledge base** - Treat them as first-class documentation, not just session logs.

---

### Step 1: Groom Epic in ROADMAP (on main)

**Before creating branch:**

1. **Add epic to ROADMAP.md** as next v0.X.0 (top of list)
2. **Renumber all existing epics** (+1 each)
3. **Update mermaid subway map** at top of ROADMAP.md:
   - Add new node for epic
   - Place in correct subgraph (Ready/Blocked/Future)
   - Add dependency arrows if needed
   - Update node styles (colors) based on status
4. **Write epic with:**
   - ⏳ Status indicator (planned, no branch yet)
   - Problem statement
   - Solution approach
   - Task checklist
5. **Review and refine** tasks (can spend time here)

> 🤖 **AI: Always update mermaid graph when adding/moving/completing epics**

**Example:**

```markdown
## v0.4.0

### Source Granularity

⏳ Add page/chapter granularity to citations

**Problem:** Citations require manual Ctrl+F
**Solution:** PDF `#page=N`, EPUB chapter links

**Tasks:**

- [ ] Test VS Code extensions
- [ ] Extract page numbers during PDF chunking
      ...
```

### Step 2: Name Conversation

**AI conversation title:** `v0.X.0: Epic Title`

Example: `v0.4.0: Source Granularity`

### Step 3: Create Branch

```bash
git checkout main
git pull origin main
git checkout -b v0.X.0  # Just version number, no descriptive name
```

**Branch naming:** `v0.X.0` (no epic name, just version)

### Step 4: Update ROADMAP with Branch Link

Replace ⏳ with 🚧 and add branch link:

```markdown
## v0.4.0

### [🚧](https://github.com/user/repo/tree/v0.4.0) Source Granularity
```

**Format:** `### [🚧](branch-url) Epic Title`

### Step 5: Create Epic Notes

**Structure (v0.4.0 and earlier):**

```
MGMT/epic-notes/v0.X.0.md  # Single file for all notes
```

**Structure (v0.5.0+):**

```
MGMT/epic-notes/v0.X.0/
  ├── MAIN.md                      # Primary epic documentation
  ├── specific-finding.md          # Specific finding/experiment
  └── another-finding.md           # Another finding
```

Add notes link to ROADMAP on same line as branch:

```markdown
### [🚧](branch-link) Source Granularity | [notes](epic-notes/v0.4.0.md)

# OR for folder structure:

### [🚧](branch-link) Source Granularity | [notes](epic-notes/v0.4.0/)
```

**Notes purpose:**

- Session summaries (in MAIN.md)
- Experiments and discoveries (separate files in v0.5.0+)
- Testing results and root cause analysis
- Implementation blockers and workarounds

**When to use folder structure:**

- Epic has multiple distinct findings (>3)
- Single file exceeds ~500 lines
- Findings are independent enough to reference separately

**Migration:** When converting v0.X.0.md → v0.X.0/, rename to MAIN.md and extract major findings to separate files.

### Step 6: Push Main Changes

```bash
git checkout main
git add MGMT/ROADMAP.md  # Updated with links
git commit -m "docs: add v0.X.0 epic to roadmap"
git push origin main
```

**Typical main changes when starting epic:**

- ROADMAP.md (epic + renumbering + links)
- Sometimes: prompts (if epic requires new prompt)

### Step 7: Work on Epic (in branch)

```bash
git checkout v0.X.0
git add .
git commit -m "feat: implement feature"
git push origin v0.X.0
```

### Step 8: Stay Current - Rebase Regularly

```bash
git checkout main
git pull origin main
git checkout v0.X.0
git rebase main
git push --force-with-lease origin v0.X.0
```

**Why rebase?**

- Keeps linear history
- Easier to review
- Cleaner when merging back to main

**When to rebase?**

- Daily if main is active
- Before creating PR
- After major main updates

### Step 9: Before Merging - Use MGMT-start Workflow

```bash
# Run pre-commit workflow (does steps 10-11 automatically)
# See .github/prompts/MGMT-start.prompt.md
```

**The MGMT-start workflow will:**

- ✅ Run all CHECKS (see MGMT/CHECKS.md)
- ✅ Update ROADMAP (mark completed checkboxes)
- ✅ Move epic to CHANGELOG (if complete)
- ✅ Bump version number (semantic versioning)
- ✅ Generate commit message

### Step 10: Merge to Main When Epic Complete

```bash
git checkout main
git pull origin main
git merge v0.3.0 --no-ff

# Tag the release
git tag v0.3.0 -m "Epic v0.3 complete"

git push origin main
git push origin v0.3.0
```

### Step 11: Delete Feature Branch (Recommended)

```bash
# Local
git branch -d v0.3.0

# Remote (optional - keeps history clean)
git push origin --delete v0.3.0
```

**Branch deletion policy:**

- ✅ **DO delete** after successful merge (keeps branch list clean)
- ✅ Git history preserved via tags
- ✅ Can recreate from tag if needed: `git checkout -b v0.3.0 v0.3.0`
- ❌ **DON'T delete** if you plan to make hotfixes on that version

### Step 12: Announce Release

- Update README.md status section (links to new CHANGELOG entry)
- Post in project communication channels
- Tweet/share if public release

---

## Epic Format

> 🤖 **AI: Use this syntax when writing epics in ROADMAP or CHANGELOG**

**Syntax:**

```markdown
### v0.X

#### [🚧](link-to-branch) Epic Title

Epic description (what problem does this solve?)

- [ ] Task to complete (roadmap only)
- [x] Completed task (roadmap only)
- Completed task (changelog only, in past tense)

❌ Anti-pattern (what NOT to do)
✅ Best practice (with link if applicable)
🗒️ Note

---
```

**Status indicators:**

- `🚧` with link = active branch exists (in-progress epic)
- `⏳` no link = planned, no branch yet
- `✅` completed (changelog only)

**Examples:**

```markdown
> **v0.3**
> [🚧](https://github.com/user/repo/tree/v0.3.0) **Feature Name**

Description of what this epic accomplishes

- [x] Completed task
- [ ] Pending task

✅ Use best practice approach
❌ Don't use anti-pattern
```

---

## Semantic Versioning

**For AI-assisted projects:**

| Type      | Version Change  | Breaking? |
| --------- | --------------- | --------- |
| **Patch** | v0.2.0 → v0.2.1 | No        |
| **Minor** | v0.2.x → v0.3.0 | No        |
| **Major** | v0.x → v1.0     | Yes       |

**Examples:**

- **Patch:** Bug fixes, typos, minor corrections
  - `fix: correct typo in metadata.json`
  - `fix: handle edge case in script`

- **Minor:** New features, backward compatible
  - `feat: add new capability`
  - `feat: improve existing feature`

- **Major:** Breaking changes, architecture changes
  - `feat!: migrate to new format (BREAKING)`
  - `refactor!: change folder structure`

---

## Rebase vs Merge

**Use rebase for:**

- ✅ Keeping feature branch current with main
- ✅ Cleaning up local history before pushing
- ✅ Maintaining linear git history

**Use merge for:**

- ✅ Integrating completed features into main
- ✅ Preserving complete feature development history
- ✅ Creating clear version boundaries

**Never rebase:**

- ❌ Public/shared branches after others have pulled
- ❌ Main branch itself
- ❌ After a branch has been merged

**Rebase conflicts?**

```bash
# During rebase, if conflicts occur:
git status                    # See conflicting files
# Fix conflicts in editor
git add <resolved-files>
git rebase --continue

# If rebase gets messy:
git rebase --abort           # Start over
```

---

## Commit Messages

**Format:**

```
<type>: <subject>

[optional body]
[optional footer]
```

**Types:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code restructuring (no feature change)
- `test:` Adding tests
- `chore:` Maintenance (dependencies, build, etc.)

**Examples:**

```
feat: add new capability
fix: resolve undefined error
docs: update ROADMAP with v0.3 epic
refactor: consolidate folder structure
```

---

## Pre-Commit Workflow

**ALWAYS run before merging to main:**

1. **Use MGMT-start prompt** (see `.github/prompts/MGMT-start.prompt.md`)
2. **Check CHECKS.md** for stability requirements
3. **Update ROADMAP** - mark completed checkboxes
4. **Move to CHANGELOG** - if epic complete
5. **Run all tests** - ensure nothing broke

---

**Last updated:** 2026-01-26
**Version:** 1.0 (Extracted from Librarian project)
**Source:** Elinor Ostrom's polycentric governance principles
