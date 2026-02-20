# Branch Workflow

**Semantic Versioning Governance:**

**Format:** vA.B.C

- **A (major):** Breaking changes, structural redesign → REQUIRES epic + branch + ROADMAP
- **B (minor):** New features, incremental improvements → REQUIRES epic + branch + ROADMAP
- **C (patch):** Bug fixes, quick fixes, typos → FAST TRACK (no branch, no ROADMAP, straight to CHANGELOG)

**Fast Track (Patch) Rule:**
- Create entry directly in CHANGELOG (no ROADMAP epic needed)
- Commit to main (no feature branch)
- Must still answer: "What type of change is this?" (patch = bug/quick fix)
- Use for: typos, broken links, dependency updates, small corrections

**Example:**
```
v0.3.1 → v0.3.2 (patch) - Fix diagram in global POLICY, update version number
```

**Traditional Epic Flow (Major/Minor):**

**One branch per epic:**

```
main (stable releases only)
  ↓
v0.3.0 (minor - feature branch)
v0.4.0 (minor - feature branch)
v1.0.0 (major - breaking changes)
```

## Branch Naming

**Format:** `vA.B.C` (version number only, no descriptive names)

**Examples:**

- `v0.3.0` (minor feature)
- `v0.4.0` (minor feature)
- `v1.0.0` (major rewrite)

## Workflow

**Major/Minor (Traditional):**
1. **Create branch from main** (`vX.Y.Z`)
2. **Work on epic in branch** (commits, tests, documentation)
3. **Rebase regularly from main** (keep up to date)
4. **Before merge: backstage-start** (pre-commit validation)
5. **Merge to main** (when ready)
6. **After merge: backstage-start** (post-merge validation, catch integration issues)
7. **Tag release** (if applicable)
8. **Publish** (if applicable: npm, skill registry, etc.)
9. **Delete feature branch** (recommended)

**Patch (Fast Track):**
1. **Work directly on main** (or short-lived branch if nervous)
2. **Add entry to CHANGELOG** (skip ROADMAP)
3. **Commit with patch description**
4. **Tag release** (vA.B.C+1)

## Epic Dance

### 🔀 Dual Track Development

**Pattern:** Two epics in different projects that retroalimentam (feedback loop)

**Structure:**
- **Epic A (Project 1):** Builds infrastructure/tool
- **Epic B (Project 2):** Uses infrastructure, discovers issues
- **Epic A:** Fixes issues, improves tool
- **Both close together** when integration complete

**Example (2026-02-15):**
- **skills v1.1.0 (arch):** Build localhost wrapper engine (MD → HTML + mermaid + CSS)
- **librarian v0.15.0:** Use wrapper for diagrams, test in real use
- **Feedback loop:** librarian discovers issues → skills fixes → both merge when stable

**Why it works:**
- Real-world testing (not theoretical)
- Continuous improvement (iterative)
- Clear integration point (both epics close together)

**How to document:**
- Add "Dual Track Development" to ROADMAP active epic section
- Reference partner epic: "Works in parallel with [project] [epic] (feedback loop)"
- Close both epics together (not sequential)

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

### Step 2: Name Conversation

**AI conversation title:** `v0.X.0: Epic Title`

Example: `v0.4.0: Source Granularity`

### Step 3: Create Branch

```bash
git checkout main
git pull origin main
git checkout -b vX.Y.Z  # Just version number, no descriptive name
```

**Branch naming:** `vX.Y.Z` (no epic name, just version)

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
git add backstage/ROADMAP.md  # Updated with links
git commit -m "docs: add v0.X.0 epic to roadmap"
git push origin main
```

**Typical main changes when starting epic:**

- ROADMAP.md (epic + renumbering + links)
- Sometimes: prompts (if epic requires new prompt)

### Step 7: Work on Epic (in branch)

```bash
git checkout vX.Y.Z
git add .
git commit -m "feat: implement feature"
git push origin vX.Y.Z
```

### Step 8: Stay Current - Rebase Regularly

```bash
git checkout main
git pull origin main
git checkout vX.Y.Z
git rebase main
git push --force-with-lease origin vX.Y.Z
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
git merge vX.Y.Z --no-ff

# Tag the release
git tag vX.Y.Z -m "Epic vX.Y complete"

git push origin main
git push origin vX.Y.Z
```

### Step 11: Delete Feature Branch (Recommended)

```bash
# Local
git branch -d vX.Y.Z

# Remote (optional - keeps history clean)
git push origin --delete vX.Y.Z
```

**Branch deletion policy:**

- ✅ **DO delete** after successful merge (keeps branch list clean)
- ✅ Git history preserved via tags
- ✅ Can recreate from tag if needed: `git checkout -b vX.Y.Z vX.Y.Z`
- ❌ **DON'T delete** if you plan to make hotfixes on that version

### Step 12: Announce Release

- Update README.md status section (links to new CHANGELOG entry)
- Post in project communication channels
- Tweet/share if public release

## Retrospective Epic Protocol

**When to use:** Work happened on main without epic branch (many commits, forgot to branch)

**Problem:**
- Made 30+ commits directly to main
- Should have been on epic branch
- Main is now ahead of origin/main
- Need to preserve work but restore main

**Solution: Create retrospective epic**

**Steps:**

1. **Create epic in ROADMAP** (on current main):
   ```bash
   # Document what was done (past tense, [x] checkboxes)
   # Epic describes completed work retrospectively
   ```

2. **Create branch from current main:**
   ```bash
   git branch vX.Y.Z
   git checkout vX.Y.Z
   ```

3. **Reset main to origin/main:**
   ```bash
   git checkout main
   git reset --hard origin/main
   ```

4. **Now you have:**
   - `main` = clean (matches origin/main)
   - `vX.Y.Z` = all your work (ready to merge properly)

5. **Follow normal merge protocol:**
   - Check all tasks in ROADMAP epic
   - Run backstage-start (HEALTH checks)
   - Merge epic → main (manual merge protocol)
   - Move epic ROADMAP → CHANGELOG
   - Tag release
   - Delete branch

**Why this works:**
- Preserves all work (nothing lost)
- Restores main to clean state
- Forces proper epic review before merge
- Documents what was accomplished
- Follows normal workflow from here

**Philosophy:**
- Mistakes happen (forgot to branch, hyperfocus mode)
- Retrospective epic = accountability without punishment
- Work gets reviewed, docs get updated, main stays clean
