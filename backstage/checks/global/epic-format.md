# Epic Format

**AI Note:** Use this syntax when writing epics in ROADMAP or CHANGELOG

**Syntax:**

```markdown
## vX.Y.Z

### Epic Title

**Description:** One-line summary of what this epic accomplishes

**Tasks:**
- [ ] Task to complete (roadmap only)
- [x] Completed task (roadmap only)
- Completed task (changelog only, in past tense)

**Success:**
- Measurable outcome 1
- Measurable outcome 2

---
```

**Alternative format (with Problem/Solution):**

```markdown
## vX.Y.Z

### Epic Title

**Problem:** What problem does this solve?

**Solution:** How we're solving it (executive summary)

**Tasks:**
- [ ] Main task 1
- [ ] Main task 2

**Success:**
- Criteria 1
- Criteria 2

---
```

**Key rules:**

- **Version header:** `## vX.Y.Z` (NOT `## vX.Y.Z - Epic Title`)
- **Epic title:** `### Epic Title` (underneath version header)
- **No status field:** Status inferred from ROADMAP vs CHANGELOG presence
- **Description OR Problem+Solution:** Choose one pattern, be consistent
- **Success criteria:** Measurable outcomes (not tasks)

## Approve to Merge Workflow (Manual)

**Manual merge protocol (when auto-merge not implemented):**

2. **Run pre-merge validation:** `backstage-start` (HEALTH checks)
3. **Merge to main:**
   ```bash
   git checkout main
   git merge --no-ff vX.Y.Z -m "Merge vX.Y.Z: Epic Title"
   ```
4. **Move epic from ROADMAP to CHANGELOG:**
   - Cut epic section from ROADMAP (## vX.Y.Z + content)
   - Paste at TOP of CHANGELOG (after navigation block, before last stable version)
   - Convert tasks: `- [x] Task` → `- Task` (remove checkboxes, past tense)
   - Remove "Approve to merge" task (not relevant in CHANGELOG)
   - Add date: `## vX.Y.Z - YYYY-MM-DD`
5. **Commit ROADMAP + CHANGELOG:**
   ```bash
   git add backstage/ROADMAP.md backstage/CHANGELOG.md
   git commit -m "Release vX.Y.Z: Epic Title

   - Task 1 completed
   - Task 2 completed
   - Task 3 completed"
   ```
6. **Run post-merge validation:** `backstage-start` (integration checks)
7. **Tag release:**
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z: Epic Title"
   ```
8. **Delete branch:**
   ```bash
   git branch -d vX.Y.Z
   ```

**Commit message format:**
- **Subject:** `Release vX.Y.Z: Epic Title`
- **Body:** Bullet list of completed tasks (past tense, no checkboxes)

**CHANGELOG entry format:**
```markdown
## vX.Y.Z - YYYY-MM-DD

### Epic Title

**Description:** What was accomplished

- Task 1 completed
- Task 2 completed

**Success:**
- Outcome 1 achieved
- Outcome 2 achieved

---
```

**Auto-merge (future):**

When implemented, backstage-start will:
2. Run pre-merge validation
3. Merge to main automatically
4. Move epic ROADMAP → CHANGELOG
5. Commit with proper format
6. Tag release
7. Delete branch

**Status:** Auto-merge documented in POLICY but not yet implemented (needs BSD awk fix).

## Epic Metadata Links

**MANDATORY: Every epic in ROADMAP must link to:**

1. **Epic-notes** (if exist):
   - Single file: `[notes](epic-notes/vX.Y.Z.md)`
   - Folder: `[notes](epic-notes/vX.Y.Z/)`
   - Can have multiple notes files (list all)

2. **Branch** (if exists):
   - Format: `[branch](https://github.com/user/repo/tree/vX.Y.Z)`
   - Or short: `[🚧](branch-url)`

**Syntax:**

```markdown
### Epic Title | [notes](epic-notes/vX.Y.Z/) | [branch](branch-url)
```

**Examples:**

```markdown
### Dashboard | [notes](../dashboard/README.md) | [🚧](https://github.com/nonlinear/skills/tree/v1.11.0-dashboard)

### Pattern Research | [notes](epic-notes/v0.9.0-pattern-research.md)
```

**Why this matters:**
- Epic-notes exist to document work → unlinked = invisible
- Branch link = shows active development
- Discoverability + accountability

**Auto-enforcement:** backstage-start validates links exist when merging.
