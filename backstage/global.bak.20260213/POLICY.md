# Global Policy

> Universal workflow rules that apply across all projects using this backstage system.

**Inspired by:** Elinor Ostrom's polycentric governance framework—multiple centers of power (global/project) with overlapping, not hierarchical, jurisdictions.

---

## Purpose

This file contains **universal, project-agnostic** workflow rules and conventions.

**POLICY.md** (project-specific) extends or overrides these global rules for specific projects.

---

## Formatting Standard

All backstage files (CHECKS, ROADMAP, CHANGELOG, POLICY) must be both **human-readable** (clear, prompt-like, easy to follow) and **machine-readable** (easy for scripts or AI to parse and execute).

**How to format tests and checklists:**

1. **Each test/check should be a short, copy-pasteable code block** (one-liner or small block), with a plain-text explanation and pass/fail criteria immediately after.
2. **No large, monolithic scripts**—keep each check atomic and self-contained.
3. **No markdown formatting or prose inside code blocks.**
4. **All explanations, expected output, and pass criteria must be outside code blocks.**
5. **Backstage files should be easy for both humans and automation to read, extract, and run.**

_Example:_

```bash
python3.11 -c "import llama_index.core; import sentence_transformers"
```

Expected: No error, prints nothing.
Pass: ✅ Dependencies OK

---

## Backstage Update System

**backstage-update.py serves dual purpose:**

### 1. Initial Scaffolding (First Install)

**Run from project root:**

```bash
python backstage/global/backstage-update.py
```

**Creates complete structure:**

- `backstage/ROADMAP.md` (from templates/ROADMAP-template.md)
- `backstage/CHANGELOG.md` (from templates/CHANGELOG-template.md)
- `backstage/POLICY.md` (from templates/POLICY-template.md)
- `backstage/HEALTH.md` (from templates/HEALTH-template.md)
- `backstage/global/*` (already in place from clone)
- `.github/prompts/backstage-*.prompt.md` (all 3 workflow prompts)

**Result:** Complete backstage framework ready to use. User then grooms ROADMAP, customizes POLICY/CHECKS.

### 2. Framework Updates (Existing Projects)

**Run from existing installation:**

```bash
python backstage/global/backstage-update.py
```

**Updates 6 files:**

- `backstage/global/POLICY.md`
- `backstage/global/HEALTH.md`
- `backstage/global/backstage-update.py` (self-update)
- `.github/prompts/backstage-start.prompt.md`
- `.github/prompts/backstage-close.prompt.md`
- `.github/prompts/backstage-update.prompt.md`

**Preserves:**

- `backstage/ROADMAP.md` (your epics)
- `backstage/CHANGELOG.md` (your history)
- `backstage/POLICY.md` (your rules)
- `backstage/HEALTH.md` (your tests)

**Workflow:** Use `/backstage-update` prompt → shows changes → user confirms → script runs → suggests `/backstage-start`

---

## Navigation Block & Backstage Files Index

**Every backstage file must have a navigation block** (`> 🤖 ... 🤖`) with links to all backstage files.

**Purpose:** Provides consistent navigation and makes backstage-start workflow aware of file locations.

**Precedence:** When global and project rules conflict:

- **Project POLICY.md** > global/POLICY.md
- **Project HEALTH.md** > global/HEALTH.md
- Local knowledge always wins (polycentric governance)

### README Protection

**README is special** — it's the "spine" of your project:

- **Public-facing:** Outsiders read this to understand your project
- **Vision statement:** Who you are AND who you aim to be
- **People are watching:** Changes are visible to community

**Global rule:** backstage-start can append navigation block but **NOT rewrite README content** without explicit confirmation.

**What needs confirmation:**

- What will change (specific sections/lines)
- How it will change (show before/after)
- Where it will change (exact line numbers)

Only **surgical, pointed changes** allowed—no wholesale rewrites.

**Project can override:** Add to your project POLICY.md if you want to allow automatic README edits (e.g., "allow auto-update of version badges").

### Placement Rules

**AI: The backstage-start prompt enforces these rules by appending/updating the navigation block automatically:**

**README.md:**

- Navigation block at **END** (before final line)
- Includes mermaid roadmap diagram (source of truth from ROADMAP.md)

**ROADMAP.md, CHANGELOG.md, HEALTH.md, POLICY.md:**

- Navigation block at **TOP** (right after `# Title`)
- Includes same mermaid roadmap diagram (copied from ROADMAP.md)

### Why 🤖 Markers Exist: Future-Proof Format Changes

**The markers are format-agnostic boundaries.**

In the future, navigation block format may change:

- Table → list
- New diagram types
- Different syntax entirely

**How backstage-start handles this:**

1. Find `> 🤖` (start marker)
2. Find `> 🤖` (end marker)
3. Delete everything between
4. Insert current format from POLICY.md

**Works regardless of old format** - the script doesn't need to know what the old syntax was. Markers are the stable contract, content between them evolves freely.

### Format

**Navigation block template (current version):**

```markdown
> 🤖
> | Backstage files | Description |
> | ---------------------------------------------------------------------------- | ------------------ |
> | [README](path/to/README.md) | Our project |
> | [CHANGELOG](path/to/CHANGELOG.md) | What we did |
> | [ROADMAP](path/to/ROADMAP.md) | What we wanna do |
> | POLICY: [project](path/to/POLICY.md), [global](path/to/global/POLICY.md) | How we go about it |
> | CHECKS: [project](path/to/HEALTH.md), [global](path/to/global/HEALTH.md) | What we accept |
> | We use **[backstage rules](https://github.com/nonlinear/backstage)**, v0.2.0 |
> 🤖
```

### Path Adjustment

**All paths in the navigation block are relative to each file's location.**

The navigation block appears in multiple files across the project. The backstage-start workflow automatically calculates correct paths when updating navigation blocks based on:

- **File's directory level** (root vs subdirectory)
- **Distance to target files** (same dir, parent dir, child dir)
- **Global file references** (POLICY/CHECKS point to both project and global versions)

No manual path calculation needed—the workflow handles this automatically.

### Mermaid Roadmap Diagram

**Source of truth:** ROADMAP.md contains the canonical mermaid roadmap diagram showing epic status.

**backstage-start workflow:**

1. Reads diagram from ROADMAP.md
2. Copies it to README.md (at end, after navigation block)
3. Copies it to all other backstage files (at top, after navigation block)

**When to update:** Any time epics are added, moved, or completed—backstage-start handles distribution automatically.

**AI Note:** backstage-start workflow maintains navigation blocks and diagrams. Don't manually copy—let the workflow enforce consistency.

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

**Format:** `v0.X.0` (version number only, no descriptive names)

**Examples:**

- `v0.3.0`
- `v0.4.0`
- `v1.0.0`

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

**CRITICAL:** Always check existing documentation before starting similar work to avoid reinventing the wheel.

**Read before starting epic:**

1. **epic-notes/** — Session logs from previous work (what we did)
2. **gaps/** — Failed experiments, hidden tricks, community discoveries (what we learned NOT to do, or what works that others don't know)

```bash
# List all epic notes
ls epic-notes/

# Search for relevant keywords in epic notes
grep -r "keyword" epic-notes/

# Check gaps for related discoveries
ls gaps/
grep -r "keyword" gaps/
```

**Why gaps/ matters:**

- **Failed experiments:** Avoid repeating fruitless tasks
- **Hidden tricks:** Apply techniques that worked but aren't documented elsewhere
- **Community contributions:** Share novel discoveries with others

**Write to gaps/ after epic:**

- Found something that didn't work? Document it (save others the pain)
- Found a trick nowhere else documents? Share it (community value)
- Researched deeply but went nowhere? Capture it (prevent wheel reinvention)

**When to check:**

- Starting any new epic (especially similar features)
- Encountering unexpected behavior
- Considering a feature that "feels like it was tried before"
- Planning technical approaches

**epic-notes/ = session logs** — Track what we did during development
**gaps/ = knowledge base** — Prevent mistakes, share discoveries

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

**AI Note:** Always update mermaid graph when adding/moving/completing epics

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
epic-notes/v0.X.0.md  # Single file for all notes
```

**Structure (v0.5.0+):**

```
epic-notes/v0.X.0/
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

### Step 9: Before Merging - Use backstage-start Workflow

```bash
# Run pre-commit workflow (does steps 10-11 automatically)
# See .github/prompts/backstage-start.prompt.md
```

**The backstage-start workflow will:**

- ✅ Run all CHECKS (see HEALTH.md)
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

**AI Note:** Use this syntax when writing epics in ROADMAP or CHANGELOG

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
2. **Check HEALTH.md** for stability requirements
3. **Update ROADMAP** - mark completed checkboxes
4. **Move to CHANGELOG** - if epic complete
5. **Run all tests** - ensure nothing broke

---

**Last updated:** 2026-01-26
**Version:** 1.0 (Extracted from Librarian project)
**Source:** Elinor Ostrom's polycentric governance principles

```

```
