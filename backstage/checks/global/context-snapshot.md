# Context Snapshot (Stateless AI Support)

**Every decision artifact should contain a context header** to help stateless AI reconstruct reasoning without conversation history.

**Template:**

```markdown
## Context Snapshot
- **Why this exists:** [one-line purpose]
- **Problem solved:** [one-line problem]
- **Date:** YYYY-MM-DD
- **Assumptions:** [bullet list of constraints/context]
```

**Apply to:**
- Epic-notes/MAIN.md (every epic)
- Decision files (comparisons, analysis, technical specs)
- Core workspace files (SOUL.md, VISION.md, project POLICY.md)

**Why this matters:**
- AI sessions are stateless (each session = fresh start)
- Context snapshot = "self-describing commits"
- Enables reconstruction without full conversation history
- Human benefit: clarity on "why this file exists"

**Example:**

```markdown
# Mac Studio Comparison

## Context Snapshot
- **Why this exists:** Hardware purchase decision for local AI inference + video rendering
- **Problem solved:** Choose between M2 Max vs Ultra vs M4 Max configurations
- **Date:** 2026-02-14
- **Assumptions:** Budget $3k, need 64GB minimum for embeddings, delivery timeline March 2026

[rest of file...]
```
