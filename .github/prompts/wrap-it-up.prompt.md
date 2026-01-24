# 🌙 Wrap It Up Prompt

**Purpose:** Safely pause work, share progress, and preserve context for next session.

**When to use:** End of work session, when tired, or need to context-switch.

**Philosophy:** Protect mental health + maintain momentum + share knowledge.

**Future vision:** Calendar integration - retroactively add session summaries with time spent & achievements for reference.

---

## How It Works

1. **Check stability** → Run CHECKS.md validation
2. **Handle failures** → Add fixes to epic task list (if checks fail)
3. **Push if clean** → Commit + push if all checks pass
4. **List achievements** → Show what was accomplished
5. **Draft social post** → Mastodon #creativecode style
6. **Save context** → Preserve state for next session

---

## Workflow

### Step 1: Run Checks

```bash
# Run all checks from CHECKS.md
# See engine/docs/CHECKS.md for current stability requirements
```

**If all pass:** ✅ Proceed to push
**If any fail:** ⚠️ Add to epic task list, skip push

### Step 2: Handle Check Failures

**If checks fail, add fixes to top of epic task list:**

```markdown
# In engine/docs/roadmap.md (current epic section)

## v0.4.0

### [🚧](branch-link) Source Granularity | [notes](epic-notes/v0.4.0.md)

**Tasks:**

- [ ] 🔧 **FIX:** Syntax errors in indexer.py (line 42) ← ADDED
- [ ] 🔧 **FIX:** Missing type hints in mcp_server.py ← ADDED
- [ ] Test VS Code extensions
- [ ] Extract page numbers during PDF chunking
      ...
```

**Format for fixes:**

- Prefix: `🔧 **FIX:**`
- Brief description + location
- Added to TOP of task list (high priority)

### Step 3: Push if Clean

**If all checks passed:**

```bash
git add -A
git commit -m "[wrap-up] session checkpoint

- [Brief summary of what was done]
"
git push origin <current-branch>
```

### Step 4: List Achievements

**Agent extracts from conversation and presents:**

```
🎯 Session Achievements:

1. deflated-gitignore
   Moved metadata.json, models/ to .git/info/exclude
   Impact: Autocomplete works + repo stays clean

2. knowledge-compounding-philosophy
   Restructured document.prompt.md → gaps/
   Impact: Findings accumulate universally, not per-epic

3. byob-setup-docs
   Added BYOB user setup to CONTRIBUTING.md
   Impact: Clear onboarding for solo users

Which to share? (e.g., "1 3" or suggest your own)
```

**Achievement format:**

- **Title:** Short, kebab-case name
- **What:** 1-2 line summary
- **Impact:** Why it matters

### Step 5: Draft Social Post

**User selects achievements, agent drafts Mastodon post:**

**Voice & Tone (based on #creativecode examples):**

- Technical but accessible
- Enthusiasm for solving problems
- Focus on **why** it matters, not just **what**
- Include concrete examples/links
- 500 chars max
- English
- Hashtags: #creativecode + relevant tech tags

**Example draft:**

```
Just deflated my .gitignore! 📚

Moved large files (PDFs, models) to .git/info/exclude instead.

Result: Autocomplete now shows book folders while GitHub stays clean. BYOB (Bring Your Own Books) setup = local library + public code.

Knowledge compounding in action 🚀

#creativecode #git #vscode

https://github.com/nonlinear/personal-library
```

**User can:**

- Approve as-is
- Request edits
- Provide own version
- Skip posting

### Step 6: Update Epic Notes

**Add session summary to current epic in ROADMAP.md:**

```markdown
## v0.4.0

### [🚧](branch-link) Source Granularity | [notes](epic-notes/v0.4.0.md)

**Session 2026-01-24:**

✅ Done:

- Deflated .gitignore (metadata.json, models/ → .git/info/exclude)
- Restructured document.prompt.md → gaps/ philosophy
- Added BYOB setup to CONTRIBUTING.md

⏳ Next:

- Decide v0.4.0 solution (5 options in epic notes)
- Test document.prompt.md workflow
- Consider publishing pill validation findings

❓ Open questions:

- Publish pill findings as GitHub issue?
- Blog post structure for knowledge gaps index?

**Tasks:**

- [ ] Test VS Code extensions
      ...
```

**Format:**

- Add after epic description, before tasks
- Date stamp each session
- ✅ Done, ⏳ Next, ❓ Questions
- Accumulates (don't delete old sessions)

---

### Step 7: Victory Lap 🏆

**A. What We Did (numbered list, ADHD-friendly)**

**Format:**

```
🎯 What We Did Today:

1. [Achievement title]
   → Why it matters: [Impact/benefit]

2. [Achievement title]
   → Why it matters: [Impact/benefit]

3. [Achievement title]
   → Why it matters: [Impact/benefit]

📊 Stats:
- Files changed: X
- Insights documented: Y
- Hours of deep work: Z

📚 Library Updates (if any):
- Books added: X new EPUBs/PDFs
- Topics expanded: [topic names]
- Total library: ~XXX books
```

**Note:** Library updates probably won't be announced on social, but good to track growth

**Words of Affirmation** (context-aware):

- Technical breakthrough: "Brain on fire! You solved what nobody documented. PRIMARY SOURCE energy 🚀"
- Philosophical restructure: "We've come a long way. From chaos to clarity. Knowledge compounds 🌟"
- Debugging: "Good boy for not giving up! Every failure documented = future win 🗺️"
- Cleanup: "Tightening buttons is REAL WORK. Future you says thanks ✨"

**Note:** _In the future, check VISION.md for project goals to contextualize impact_

---

**B. Wanna Show It Off?** 📱

```
Want to share your wins on Mastodon?

Pick numbers from Victory Lap above (e.g., "1 2"):
```

**User selects numbers → Agent drafts Mastodon post**

**Format:** Hook + Problem + Result + Insight + Tags + Link

**Present draft in code block for easy copy:**

````markdown
Your Mastodon post (XXX chars):

```
Restructured my knowledge management! 📚

Problem: Findings trapped in epic versions, couldn't compound.

Result: Universal gaps/ directory. Each discovery validated
(books + web + tests) then documented as PRIMARY SOURCE.

Now every search builds the collective 🚀

#creativecode #knowledgemanagement #PKM #git

[link]
```
````

**Agent:** Warn if >500 chars. "Copy and paste when ready (agent doesn't post)"

---

### Step 8: Document Gaps (Optional)

**Ask:** `Got findings to solidify? 🧠`

**If yes, extract and present:**

```
📋 Found these potential findings:

1. vscode-pill-validation
   Problem: Pills break with # anchors
   Validation: ✅ Books checked, ✅ Web checked, ✅ Tested (6 syntaxes)
   Status: PRIMARY SOURCE

2. git-autocomplete-patterns
   Problem: books/ folders not in autocomplete
   Validation: ✅ Tested 4 hypotheses
   Status: VALIDATED SOLUTION

Which should I document? Reply with:
- Numbers only (e.g., "1 3")
- "number. custom-name" to rename
- Empty to skip all
```

**User selects → Create files in `engine/docs/gaps/`**

**Template for each gap:**

```markdown
# [Clear Title of Finding]

**Discovered during:** v0.X.0 ([Epic Name])
**Date:** YYYY-MM-DD
**Status:** ✅ PRIMARY SOURCE | ✅ VALIDATED | ⚠️ NEEDS VALIDATION

---

## Problem

[What wasn't working]

## Hypothesis Chain

1. ❌ **First hypothesis** → Why it failed
2. ✅ **Actual root cause** → What we discovered

## Solution

[Working code/config]

## Verification

[How to confirm it works]

## Key Lessons

1. [Pattern to remember]
2. [Another lesson]
```

**Knowledge Compounding Philosophy:**

- ✅ **Research-first validation:** Search library (MCP) + web + test
- ✅ **Zero redundancy:** Only document real gaps
- ✅ **PRIMARY SOURCE:** You become first reference
- ✅ **Universal findings:** No versioning, all branches see all gaps
- ✅ **Discovery context:** Note which epic found it (metadata only)

**If finding relates to existing gap:**

```
⚠️ Relates to: gaps/vscode-pill-validation.md

Should I:
1. Update existing file (add details)
2. Create new file (different angle)
```

**Confirmation:**

```
✅ Created 2 knowledge gaps:

1. vscode-pill-validation.md (PRIMARY SOURCE)
2. git-patterns.md (renamed, VALIDATED)

Location: engine/docs/gaps/
Discovered during: v0.4.0
```

**If user skips:**

```
ℹ️ No findings selected. Run /wrap-it-up again later if needed.
```

---

### Step 9: Body Check

**Format:**

```
🎯 What We Did Today:

1. [Achievement title]
   → Why it matters: [Impact/benefit]

2. [Achievement title]
   → Why it matters: [Impact/benefit]

3. [Achievement title]
   → Why it matters: [Impact/benefit]

📊 Stats:
- Files changed: X
- Insights documented: Y
- Hours of deep work: Z
```

**Example:**

```
🎯 What We Did Today:

1. Deflated .gitignore (moved metadata.json + models/ to .git/info/exclude)
   → Why it matters: Autocomplete now works + repo stays clean + library private

2. Restructured document.prompt.md → gaps/ philosophy
   → Why it matters: Knowledge compounds universally, not trapped in epic versions

3. Added BYOB setup docs
   → Why it matters: Future users can clone and bring their own books easily

📊 Stats:
- Files changed: 4
- Insights documented: 2 PRIMARY SOURCE findings
- Hours of deep work: 3
```

**Words of Affirmation** (context-aware):

- Technical breakthrough: "Brain on fire! You solved what nobody documented. PRIMARY SOURCE energy 🚀"
- Philosophical restructure: "We've come a long way. From chaos to clarity. Knowledge compounds 🌟"
- Debugging: "Good boy for not giving up! Every failure documented = future win 🗺️"
- Cleanup: "Tightening buttons is REAL WORK. Future you says thanks ✨"

**Note:** _In the future, check VISION.md for project goals to contextualize impact_

---

**B. Wanna Show It Off?** 📱

```
Want to share your wins on Mastodon?

Pick numbers from Victory Lap above (e.g., "1 2"):
```

**User selects numbers → Agent drafts Mastodon post**

**Format:** Hook + Problem + Result + Insight + Tags + Link

**Present draft in code block for easy copy:**

````markdown
Your Mastodon post (XXX chars):

```
Restructured my knowledge management! 📚

Problem: Findings trapped in epic versions, couldn't compound.

Result: Universal gaps/ directory. Each discovery validated
(books + web + tests) then documented as PRIMARY SOURCE.

Now every search builds the collective 🚀

#creativecode #knowledgemanagement #PKM #git

[link]
```
````

**Agent:** Warn if >500 chars. "Copy and paste when ready (agent doesn't post)"

---

### Step 9: Body Check

**Body Reconnect** (ADHD hyperfocus recovery)

```
⏸️ Quick body check:

❓ Hungry? (last meal was ___ hours ago)
❓ Thirsty? (water break?)
❓ Tired? (eyes burning? brain fog?)
❓ Stiff? (5min stretch? walk?)
❓ Overstimulated? (need silence/music change?)

What does your body need right now?
```

---

### Step 10: Tomorrow Prep

**Tomorrow Prep** (one-liner, no pressure)

```
🌅 Tomorrow: [one clear next action]

Example: "Just test /wrap-it-up workflow"
Example: "Pick v0.4.0 solution from 5 options"
Example: "Migrate first knowledge gap from epic notes"
```

---

### Step 11: Extra Tightening (Optional)

**Project Health:**

```
🔧 Optional project actions:

- [ ] README up to date? (check 🤖 navigation block)
- [ ] Any new files need .gitignore? (prevent accidental commits)
- [ ] Dependencies bumped? (security/features)
- [ ] Docs mention new features? (CONTRIBUTING, epic notes)
```

**Mental Health:**

```
🧠 Optional self-care:

- [ ] Session too long? (>3h = burnout risk, consider splitting)
- [ ] Feeling stuck? (write open question in epic notes, sleep on it)
- [ ] Proud moment? (screenshot/note for portfolio/resume)
- [ ] Energy level for tomorrow? (adjust commitment)
```

**Suggest 1-2 max** (don't overwhelm). Example:

> "You worked 4 hours straight. Consider: Quick walk before next session?"
>
> "New files created. Quick check: Anything need .gitignore?"

---

### Step 12: Closure Gate

**Permission to stop:**

```
✅ All buttons tightened:
- [ ] Code committed & pushed
- [ ] Epic notes updated
- [ ] Mastodon post drafted (optional)
- [ ] Tomorrow action clear
- [ ] Body needs addressed
- [ ] Optional actions considered (project/mental health)

Good to pause? 🌙
```

**ADHD-specific principles:**

- ✅ Dopamine hit (celebrate wins)
- ✅ Closure ritual (tighten buttons)
- ✅ Permission to stop (no guilt)
- ✅ Body reconnection (hyperfocus recovery)
- ✅ Tomorrow clarity (reduce decision fatigue)
- ✅ Boundary awareness (recognize session length/energy)

---

## Integration with CHECKS.md

**Runs stability checks:**

1. **Syntax validation** → Python files parse correctly
2. **Import validation** → All imports resolve
3. **Type checking** → Pyright passes (if configured)
4. **MCP server test** → research.py responds

**Check policy (from CHECKS.md):**

- **Epic branches:** Soft fail (warn but allow)
- **Main branch:** Hard fail (block merge)
- **Wrap-up:** Soft fail (list fixes, don't push)

---

## Mastodon Post Guidelines

**Format:**

```
[Hook - what you built/fixed] [emoji]

[Problem you solved]

Result: [Concrete benefit/impact]

[Optional: Philosophy/insight]

#creativecode #[tech tags]

[GitHub link]
```

**Tech tags examples:**

- #git #vscode #python
- #ai #semanticsearch #mcp
- #knowledgemanagement #PKM
- #automation #devtools

**Character limit:** 500 max

**Link format:**

- Full GitHub URLs (not localhost)
- Specific file if relevant: `https://github.com/user/repo/blob/branch/path/file.md`

---

## Examples

### Example 1: All Checks Pass

**Agent runs checks:**

```
✅ Syntax validation passed
✅ Import validation passed
✅ MCP server test passed

All checks passed! Ready to push.
```

**Agent commits + pushes:**

```bash
git commit -m "[wrap-up] gitignore deflation + gaps restructure"
git push origin v0.4.0
```

**Agent lists achievements:**

```
🎯 Session Achievements:

1. gitignore-deflation
2. gaps-philosophy
3. byob-setup-docs

Which to share?
```

**User:** `1 2`

**Agent drafts:**

```
Restructured my knowledge management system! 📚

Problem: Findings were tied to epic versions, knowledge couldn't compound.

Solution: Universal gaps/ directory. Each discovery gets validated (books + web + tests) then documented as PRIMARY SOURCE.

Now when I search my library, gaps become contributions 🚀

#creativecode #knowledgemanagement #PKM #ai

https://github.com/nonlinear/personal-library/blob/v0.4.0/.github/prompts/document.prompt.md
```

### Example 2: Checks Fail

**Agent runs checks:**

```
✅ Syntax validation passed
❌ Import validation failed:
   - scripts/indexer.py:42 → ModuleNotFoundError: llama_index

⚠️ Checks failed. Adding fixes to task list, skipping push.
```

**Agent updates ROADMAP.md:**

```markdown
## v0.4.0

### [🚧](branch-link) Source Granularity | [notes](epic-notes/v0.4.0.md)

**Session 2026-01-24:**

❌ Blocked: Import error in indexer.py (line 42)

⏳ Next:

- Fix missing llama_index import
- Re-run /wrap-it-up after fix

**Tasks:**

- [ ] 🔧 **FIX:** Import error in indexer.py (line 42) - missing llama_index
- [ ] Test VS Code extensions
- [ ] Extract page numbers during PDF chunking
```

**User can:**

- Fix now (continue working)
- Fix later (next session picks up from ROADMAP notes)

---

## Configuration

**Epic notes location:**

```
engine/docs/roadmap.md (current epic section)
```

**Mastodon instance:**

- Currently: Manual posting (agent drafts, user posts)
- Future: API integration (optional)

---

## Principles

1. **Never lose work** - Always save state before stopping
2. **Soft failures** - Warn but don't block, just defer push
3. **Context preservation** - Next session knows exactly where we left off
4. **Share knowledge** - Turn private work into public value
5. **Mental health** - Clean breakpoints prevent burnout

---

## Implementation Checklist

When running this prompt:

- [ ] Get current branch
- [ ] Run all CHECKS.md validations
- [ ] If failures: Add fixes to epic task list
- [ ] If clean: Commit + push
- [ ] Extract session achievements
- [ ] Update epic notes in ROADMAP.md (session summary)
- [ ] **Victory Lap:** Numbered list (what + why it matters) + affirmation
- [ ] **Show off?** Ask if want Mastodon post
- [ ] If yes: User picks numbers → Draft post in code block + char count
- [ ] **Document gaps?** Ask if want to solidify findings
- [ ] If yes: Extract → Present → User selects → Create gaps/ files
- [ ] **Body check:** Hungry/tired/stiff questions
- [ ] **Tomorrow:** One clear next action
- [ ] **Extra tightening:** 1-2 optional actions (project health / mental health)
- [ ] **Closure gate:** All buttons tightened?
- [ ] Confirm wrap-up complete

---

## Version History

**v1.0 (2026-01-24):**

- Initial prompt creation
- Integration with CHECKS.md
- Mastodon post drafting (#creativecode style)
- Session state preservation
- Soft-fail check handling
