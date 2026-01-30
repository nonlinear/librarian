# Prompt Merging Philosophy

**Discovered during:** v0.4.0 (Source Granularity epic)
**Date:** 2026-01-24
**Status:** ✅ DESIGN DECISION

---

## Problem

When building AI prompt systems, unclear when to merge prompts into one file vs keep them separate. Risk of:

- Prompts becoming too long (harder to maintain)
- Prompts being too fragmented (harder to execute workflow)
- Duplication of concepts across files

## Hypothesis Chain

1. ❌ **Keep all prompts separate** → Too much context-switching, user has to remember which prompt to run when
2. ❌ **Merge everything into mega-prompts** → Files become 1000+ lines, hard to navigate
3. ✅ **Merge based on workflow timing** → If prompt B is ALWAYS part of prompt A's workflow, merge them

## Decision Criteria

**Merge prompts when:**

- Prompt B is executed AS PART OF prompt A's workflow (not standalone)
- Timing relationship is fixed (e.g., "solidify findings" always happens during session wrap-up)
- User would have to remember to run both (cognitive load)

**Keep prompts separate when:**

- Can be run independently at any time
- Serve different purposes/contexts
- Would make parent prompt too long (>1000 lines)

## Example: gaps.prompt.md → wrap-it-up.prompt.md

**Original structure:**

```
/gaps - Document technical findings (standalone)
/wrap-it-up - End session ritual (standalone)
```

**Problem identified:**

- User: "gaps should be INSIDE wrap-it-up, not separate"
- Reasoning: Solidifying findings happens DURING session closing, not randomly
- Timing relationship: wrap-it-up ALWAYS asks "got findings?" → if yes, run gaps workflow

**Solution:**

- Merged gaps workflow into wrap-it-up Step 8
- Kept it optional (user can skip)
- Natural flow: Victory → Share → Document → Ground → Close

## Verification

**Test:** Does the merged workflow feel natural?

- ✅ Yes. Findings documented before body check = mental closure before physical
- ✅ Optional step = doesn't block if no findings
- ✅ All session-ending actions in one ritual

**Test:** Is the file too long?

- Current: ~740 lines
- Acceptable: <1000 lines for workflow prompts
- ✅ Still maintainable

## Key Lessons

1. **Workflow timing > Conceptual separation** - If B always happens after A, merge them
2. **Cognitive load matters** - Fewer prompts to remember = better UX
3. **Optional steps work** - Can merge without forcing execution
4. **Natural psychological flow** - Match prompt structure to mental process (celebrate → solidify → ground)

## Related Patterns

- `/whatsup` has branch detection (run first = different modes, keep separate)
- `/research` is always standalone (any time query, keep separate)
- `/wrap-it-up` is ritual (fixed sequence, merge substeps)

## Updates

_None yet._
