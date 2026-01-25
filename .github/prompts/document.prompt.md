# 📝 Document Findings Prompt

**Purpose:** Extract technical findings from conversation and document them in the appropriate epic notes.

**When to use:** After debugging sessions, experiments, or discovering unexpected behaviors that should be preserved for future reference.

---

## Knowledge Validation Philosophy

**Core principle:** Only document what doesn't already exist in the collective knowledge pool.

**Research-first validation:**

```
1. Search personal library (MCP) → Not found
2. Search web documentation → Not found
3. Test/experiment → Document findings
4. Result: Primary source created
```

**Why this matters:**

- ✅ **Zero redundancy** - Only documents real knowledge gaps
- ✅ **Absolute confidence** - If documented, it's because nothing existed
- ✅ **Primary source** - You become the first reference
- ✅ **Public value** - Not just project-specific, benefits everyone
- ✅ **Technical portfolio** - Proof of solving unique problems

**First time in history:**

AI + semantic search can confirm knowledge gaps with certainty. The **delta is REAL** because:

1. Machines searched all accumulated knowledge (library + web)
2. Human validated gap through testing
3. New knowledge documented for future reference
4. Next search will find it (knowledge compounds)

**Epic notes = publishable material:**

Each finding is a potential:

- Blog post / technical article
- GitHub issue report
- StackOverflow canonical answer
- Conference talk material
- Proof of expertise in domain

**Example (v0.4.0 pill validation):**

- Searched: VS Code docs, GitHub, web → ❌ Nothing about pill + fragments
- Tested: 6 different syntaxes, all failed
- Documented: First known comprehensive test results
- Value: Anyone with this problem now has a reference
- Outcome: You're the authority on VS Code pill validation behavior

**What to document vs what to skip:**

✅ **Document:**

- Technical discoveries (root causes, workarounds)
- Failed hypotheses (save others from same path)
- Tool limitations (undocumented behavior)
- Configuration patterns (non-obvious solutions)

❌ **Skip:**

- Project decisions (already in commits/ROADMAP)
- User preferences (not knowledge, just choices)
- Normal development progress (not discoveries)
- Already-documented patterns (no gap to fill)

---

## How It Works

1. **Read conversation** → Extract technical findings, root causes, solutions
2. **Identify epic** → Check current git branch to determine version
3. **Validate knowledge gap** → Verify books + web + tests were checked
4. **Check duplication** → Read existing epic notes to avoid re-documenting
5. **Document findings** → Append new section with validation status & related sources
6. **Confirm** → Brief summary of what was documented

---

## Epic Notes Location

**Current structure (v0.4.0 and earlier):**

```
engine/docs/epic-notes/v0.X.0.md
```

**Future structure (v0.5.0+):**

```
engine/docs/epic-notes/v0.X.0/
  ├── MAIN.md          # Primary epic documentation
  ├── PILL-TEST.md     # Specific experiment/finding
  └── AUTOCOMPLETE.md  # Another finding
```

**Migration plan:**

- v0.4.0 and earlier: Continue using single `.md` file
- v0.5.0+: Create directory structure for better organization
- When converting: rename `v0.X.0.md` → `v0.X.0/MAIN.md`

---

## Document Structure

Each finding should follow this format:

```markdown
### YYYY-MM-DD: [Clear Title of Finding]

**Problem:** [Brief description of what wasn't working]

**Hypothesis Chain:** [What we thought the issue was, in order tested]

1. ❌ **First hypothesis** → Why it failed
2. ❌ **Second hypothesis** → Why it failed
3. ✅ **Actual root cause** → What we discovered

**Root Cause:**

[Detailed explanation of the actual problem]

**Related Material (if any):**

Books that have partial coverage:

- [Book Title] - Covers X but not Y (no pill link needed)

Web resources checked:

- https://example.com/page - What it covers vs what's missing
- https://github.com/org/repo/issues/123 - Related but different angle

**Failed Attempts:**

[Code/config snippets that didn't work, with explanations]

**Debugging Discovery:**

[Commands/tools used to find the root cause]

**Solution:**

[Final working code/config with explanations]

**Verification:**

[How to confirm the fix worked]

**Key Lessons:**

1. [Lesson learned]
2. [Another lesson]
3. [Pattern to remember]

**Status:** ✅ RESOLVED | ⏳ IN PROGRESS | ❌ BLOCKED
```

---

## Workflow

### Step 1: Identify Epic

```bash
# Get current branch
git branch --show-current
# Example output: v0.4.0

# Check if epic notes exist
ls -la engine/docs/epic-notes/v0.4.0*
# Could be: v0.4.0.md (current) or v0.4.0/ (future)
```

**Branch naming rules:**

- Epic branches: `v0.X.0` (version only)
- Feature branches: Would need different documentation strategy
- Main branch: No epic-specific notes (findings go to general docs)

### Step 2: Read Existing Epic Notes

**For single-file structure (current):**

```bash
# Read entire epic notes file
cat engine/docs/epic-notes/v0.4.0.md
```

**For directory structure (future):**

```bash
# List all finding files
ls engine/docs/epic-notes/v0.4.0/

# Read main epic file
cat engine/docs/epic-notes/v0.4.0/MAIN.md

# Read specific finding if exists
cat engine/docs/epic-notes/v0.4.0/AUTOCOMPLETE.md
```

**What to check:**

- Is this finding already documented?
- Which section does it belong to? (Experiments, Technical Notes, etc.)
- Should it be a new section or added to existing?

### Step 4: Extract & Present Findings for Grooming

### Step 5: Extract Findings Details

**Extract findings from conversation and present to user:**

```
📋 Found these potential findings to document:

1. vs-code-pill-validation
   Problem: Pills break with # anchors
   Validation: ✅ Books checked, ✅ Web checked, ✅ Tested (6 syntaxes)
   Status: PRIMARY SOURCE

2. autocomplete-git-ignore
   Problem: books/ folders not in autocomplete
   Validation: ✅ Tested 4 hypotheses
   Status: VALIDATED SOLUTION

Which should I document? Reply with:
- Numbers only (e.g., "1 3") to create new files
- "number6 newname" to create with custom name
- "number. filename.md (update with X)" to append to existing file
- Empty to skip all
```

**Include validation status for each finding:**

- ✅ PRIMARY SOURCE - Books + web checked, nothing found, tests done
- ✅ VALIDATED SOLUTION - Tested hypotheses, root cause found
- ⚠️ NEEDS VALIDATION - Missing research/web checks (suggest doing them first)

### Step 5: Extract Findings Details

**What counts as a finding:**

- ✅ Root cause of unexpected behavior (e.g., pill validation, autocomplete)
- ✅ Failed hypotheses that might help future debugging
- ✅ Configuration discoveries (gitignore patterns, VS Code settings)
- ✅ Tool limitations or workarounds
- ✅ Performance implications (file watcher exclude)
- ❌ Normal development progress (those go in session log)
- ❌ User preferences (those are just execution)

**Information to extract:**

- **Problem statement:** What wasn't working?
- **Hypotheses tested:** What did we think it was?
- **Root cause:** What was it actually?
- **Solution:** How did we fix it?
- **Verification:** How did we confirm?
- **Lessons:** What patterns should we remember?

### Step 5: Check for Duplication

**For each selected finding:**

**Exact match:** Finding already documented with same root cause → Skip (inform user)
**Partial match:** Similar finding but different nuance → Ask if should merge or create new
**No match:** New finding → Proceed with documentation

**If duplication detected:**
7

```
⚠️ Finding "autocomplete-git-ignore" appears to overlap with existing:
   engine/docs/epic-notes/v0.4.0/git-patterns.md

Should I:
1. Skip (already documented)
2. Merge into existing file
3. Create new file anyway (different angle)
```

**Example comparison:**

```markdown
# Existing in epic notes

### VS Code Pill Validation with URL Fragments

- Pills break with `#` anchors
- Tested 6 syntaxes

# New finding from conversation

### VS Code Path Autocomplete Investigation

- Git ignore patterns block autocomplete
- files.exclude ≠ autocomplete visibility
```

→ These are **different findings**, both should be documented.

### Step 6: Create or Update Documentation Files

**For single-file structure (v0.4.0 and earlier):**

Add new sections under "Experiments" heading.

**For directory structure (v0.5.0+):**

Create OR update files based on user grooming:

```bash
# User response:
# 1
# 2. pill-validation.md (update with fragment tests)
# 3. git-patterns-block-autocomplete

v0.4.0/
  ├── MAIN.md                              # Already exists
  ├── pill-validation.md                   # EXISTS - APPEND finding #2
  ├── vs-code-pill-validation.md           # NEW: Finding #1
  └── git-patterns-block-autocomplete.md   # NEW: Finding #3
```

**Update vs Create logic:**

- **Create new:** Number or "number. newname"
- **Update existing:** "number. filename.md (update with X)"
  - Check file exists in `engine/docs/epic-notes/v0.X.0/`
  - If not exists: Ask user if should create instead
  - If exists: Append with `---` separator

**Update format:**

````markdown
# In pill-validation.md (existing content)

### 2026-01-20: Original Discovery

[...existing content...]

---

### 2026-01-24: Fragment Tests ← APPENDED

[...new finding content...]

```8

### Step 7: Confirm Documentation

Add new section under appropriate heading (usually "Experiments" or "Technical Notes").

**For directory structure:**

Determine if finding deserves its own file:

- Major experiment with multiple sections → New file (e.g., `AUTOCOMPLETE.md`)
- Small finding or addendum → Add to `MAIN.md` or related file

**Naming convention for finding files:**

- UPPERCASE with hyphens: `PILL-TEST.md`, `AUTOCOMPLETE.md`
- Descriptive but concise (1-3 words)
- Focus on the topic, not the outcome

### Step 7: Confirm Documentation

**Brief response format (single-file structure):**
```
````

✅ Documented in engine/docs/epic-notes/v0.4.0.md:

- VS Code Path Autocomplete Investigation
- Root cause: Git ignore patterns block autocomplete
- Solution: Fixed .git/info/exclude pattern
- Key lesson: Git patterns > VS Code settings for autocomplete

```

**Brief response format (directory structure):**

```

✅ Created 2 finding files in engine/docs/epic-notes/v0.4.0/:

1. vs-code-pill-validation.md
   - Pills break with # anchors
   - 6 syntaxes tested, all failed
   - Recommendation: Text-only granularity

2. git-patterns-block-autocomplete.md
   - Root cause: books/\*\*/ in .git/info/exclude
   - Solution: Remove trailing slash pattern
   - Lesson: Git patterns > VS Code settings

```

**Brief response format (directory structure):**

```

✅ Created 2 finding files in engine/docs/epic-notes/v0.4.0/:

1. vs-code-pill-validation.md
   - Pills break with # anchors
   - 6 syntaxes tested, all failed
   - Recommendation: Text-only granularity

2. git-patterns-block-autocomplete.md
   - Root cause: books/\*\*/ in .git/info/exclude
   - Solution: Remove trailing slash pattern
   - Lesson: Git patterns > VS Code settings

```

---

## Special Cases

### No Epic Branch

If current branch is `main` or a feature branch (not `v0.X.0`):

**Ask user:**

```

📋 Current branch: main

This finding doesn't belong to a specific epic. Where should I document it?

Options:

1. Create general troubleshooting doc (engine/docs/TROUBLESHOOTING.md)
2. Add to CONTRIBUTING.md (if it's a workflow finding)
3. Defer documentation (will lose the finding)

```

### Finding Already Documented

**Response:**

```

ℹ️ Finding "autocomplete-git-ignore" is already documented in:
engine/docs/epic-notes/v0.4.0.md (line 180)

Existing documentation covers:

- Root cause: books/\*\*/ pattern in .git/info/exclude
- Solution: Remove trailing slash
- Verification: git check-ignore confirms fix

Should I:

1. Skip (already complete)
2. Add your new details to existing section
3. Create separate file with additional angle

```

### User Skips All Findings

**User response: (empty)**

**Agent response:**

```

ℹ️ No findings selected for documentation.

Findings identified but not documented:

1. vs-code-pill-validation
2. autocomplete-git-ignore
3. files-exclude-vs-gitignore

You can run /document again later if needed.

````

### Multiple Findings in One Conversation

Document each as a separate section with consistent formatting:

```markdown
---
### 2026-01-24: Finding A Title

[Full documentation]
---

### 2026-01-24: Finding B Title

[Full documentation]

---
````

---

## Examples

### Example 1: Interactive Grooming (v0.5.0+)

**Agent extracts findings and presents:**

```
📋 Found these potential findings to document:

1. pill-validation-url-fragments
   Problem: Pills break with # anchors
   Solution: Text-only granularity approach

2. autocomplete-git-ignore
   Problem: books/ folders not in autocomplete
   Solution: Fixed .git/info/exclude pattern

3. config-precedence
   Problem: files.exclude doesn't override git ignore
   Solution: Understand VS Code config layers

Which should I document? Reply with numbers or "number. newname"
```

**User responds:**

```
1
2. git-patterns-autocomplete
```

**Agent creates files:**

```bash
v0.5.0/
  ├── MAIN.md  # Already exists
  ├── pill-validation-url-fragments.md      # Finding #1 (original name)
  └── git-patterns-autocomplete.md          # Finding #2 (renamed)
# Finding #3 skipped (not in user response)
```

**Confirmation:**

```
✅ Created 2 finding files in engine/docs/epic-notes/v0.5.0/:

1. pill-validation-url-fragments.md
   - Pills break with # anchors
   - 6 syntaxes tested, all failed

2. git-patterns-autocomplete.md (renamed from autocomplete-git-ignore)
   - Root cause: books/**/ in .git/info/exclude
   - Solution: Remove trailing slash pattern
```

### Example 2: Single File Structure (v0.4.0)

**Same findings, but epic uses single-file structure:**

**Agent presents:**

```
📋 Found 3 findings to document in v0.4.0.md
(See list from Example 1)
```

**User responds:**

```
1 2
```

**Agent appends to existing file:**

Adds two new sections to `engine/docs/epic-notes/v0.4.0.md`:

```markdown
---
### 2026-01-24: Pill Validation URL Fragments

[Full documentation]
---

### 2026-01-24: Autocomplete Git Ignore

[Full documentation]
```

**Confirmation:**

```
✅ Added 2 sections to engine/docs/epic-notes/v0.4.0.md:
- Pill Validation URL Fragments
- Autocomplete Git Ignore
```

### Example 3: Renaming During Grooming

**User response:**

```
1. vscode-pills-fail-with-anchors
3. why-gitignore-blocks-autocomplete
```

**Interpretation:**

- Finding #1 → `vscode-pills-fail-with-anchors.md` (renamed)
- Finding #2 → Skipped
- Finding #3 → `why-gitignore-blocks-autocomplete.md` (renamed)

**Result:**

```bash
v0.5.0/
  ├── MAIN.md
  ├── vscode-pills-fail-with-anchors.md
  └── why-gitignore-blocks-autocomplete.md
```

**Conversation context:**

- User reported books not appearing in autocomplete
- Tested files.exclude, search.exclude
- Discovered .git/info/exclude pattern `books/**/` was blocking folders
- Fixed by removing trailing slash pattern

**Documentation result:**

Added to `engine/docs/epic-notes/v0.4.0.md`:

```markdown
### 2026-01-24: VS Code Path Autocomplete Investigation

**Problem:** Folders and files in `books/` directory not appearing in markdown path autocomplete...

[Full finding as shown in structure above]

**Status:** ✅ RESOLVED
```

### Example 2: Multiple Related Findings

**Conversation context:**

- Discovered pill validation breaks with anchors (Finding A)
- Later discovered autocomplete issue (Finding B)
- Both in same epic (v0.4.0)

**Documentation result:**

Both documented in same file, different sections:

```markdown
### 2026-01-24: VS Code Pill Validation with URL Fragments

[...]

---

### 2026-01-24: VS Code Path Autocomplete Investigation

[...]
```

---

## Integration with Other Prompts

**Relationship to /whatsup:**

- `/whatsup` = Pre-commit check (validates, syncs, determines status)
- `/document` = Post-discovery documentation (preserves findings)

**Workflow integration:**

```
1. User encounters issue
2. Agent debugs and finds solution
3. User runs /document → Findings documented in epic notes
4. Later, user runs /whatsup → Validates epic progress
5. Before merge, /whatsup ensures epic notes complete
```

**CONTRIBUTING.md reference:**

Epic notes are now checked in Step 0 (before starting epic work) to prevent re-discovering documented findings. This prompt ensures new findings get documented so future work can reference them.

---

## Error Handling

### Git Command Fails

```
❌ Cannot determine current branch (git command failed).

Please run manually: git branch --show-current
Then tell me the branch name so I can document these findings.
```

### Epic Notes File Not Found

```
⚠️ Epic notes file not found: engine/docs/epic-notes/v0.4.0.md

This might be a new epic. Should I:
1. Create engine/docs/epic-notes/v0.4.0.md
2. Create engine/docs/epic-notes/v0.4.0/ directory
3. Cancel (user will create manually)
```

### No Findings in Conversation

```
ℹ️ No technical findings detected in conversation.

Conversation contained:
- Normal development progress
- User preferences/choices
- Already-documented patterns

Nothing to document. Continue working!
```

---

## Configuration

**Epic notes base path:**

```
/Users/nfrota/Documents/personal library/engine/docs/epic-notes/
```

**Filename patterns:**

- Single file: `v{major}.{minor}.{patch}.md` (e.g., `v0.4.0.md`)
- Directory: `v{major}.{minor}.{patch}/` (e.g., `v0.4.0/`)
  - Main file: `MAIN.md`
  - Finding files: `[A-Z-]+.md` (e.g., `AUTOCOMPLETE.md`)

**Future migration trigger:**
When epic notes file exceeds ~500 lines, suggest converting to directory structure.

---

## Principles

1. \*\*PExtract findings from conversation (problem, hypotheses, solution)

- [ ] Present findings list to user (numbered, with suggested names)
- [ ] Wait for user grooming response
- [ ] Parse user response (numbers and renames)
- [ ] Read existing epic notes completely
- [ ] Check each selected finding for duplication
- [ ] Format findings with full template
- [ ] Create files (directory structure) or append sections (single file)
- [ ] Verify filesing:\*\* Mark findings as resolved/in-progress/blocked

7. **Epic scoped:** Findings belong to the epic branch where discovered

---

## Implementation Checklist

When running this prompt:

- [ ] Get current git branch
- [ ] Locate epic notes file/directory
- [ ] Read existing epic notes completely
- [ ] Extract findings from conversation (problem, hypotheses, solution)
- [ ] Check if finding already documented
- [ ] Format finding with full template
- [ ] Append to epic notes (appropriate section)
- [ ] Verify file written successfully
- [ ] Provide brief confirmation to user

---

## Version History

**v1.0 (2026-01-24):**

- Initial prompt creation
- Support for single-file epic notes (v0.X.0.md)
- Future-proofing for directory structure (v0.X.0/)
- Integration with CONTRIBUTING.md epic notes review workflow
