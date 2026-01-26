# MGMT System

> Universal project management system for AI-assisted development.

**Version:** 1.0.0 (placeholder - will track actual MGMT repo versions)

**Source:** https://github.com/nonlinear/MGMT (not yet published)

---

## Philosophy: Polycentric Governance

**Inspired by Elinor Ostrom's work on commons management.**

MGMT uses a **polycentric structure**—not hierarchical "levels" but **overlapping jurisdictions** where global and project concerns coexist.

### What is Polycentric Governance?

Traditional hierarchical systems assume clear separation: federal → state → local, with each level having distinct authority. **Polycentric systems reject this model.**

Instead, polycentric governance recognizes:

- **Multiple simultaneous centers of authority** operating at different scales
- **Overlapping jurisdictions** rather than cleanly separated domains
- **No single hierarchy** - conflicts and negotiations are normal, not bugs
- **Self-organized innovation** at all scales, not just top-down mandates

**Key insight from Ostrom:** "There is no hierarchy of governments" in effective federal systems. Different arenas (local, regional, national) are **available simultaneously** to citizens, who choose which level to engage based on their needs.

### How MGMT Implements Polycentricity

**Two centers of authority:**

1. **Global MGMT** (universal framework) - Defines workflow patterns, epic syntax, validation rules
2. **Your project** (local implementation) - Chooses which rules to adopt, when to deviate, how to extend

**Overlapping concerns:**

- Epic format lives in `global/POLICY.md` (universal)
- Your epic *content* lives in `ROADMAP.md` (project-specific)
- Project `POLICY.md` can **extend** global rules (e.g., "requires reindexing?" for database projects)

**Self-organized correction:**

- When MGMT updates, YOU decide whether/when to adopt changes
- No forced upgrades - you evaluate if new patterns fit your context
- Can stay on older MGMT version if it works better for your project

**Bottom-up participation:**

- Global MGMT improves based on lessons from real projects
- Your discoveries in `gaps/` inform future MGMT updates
- Community learns from each other's implementations

### Why This Matters for AI-Assisted Development

Traditional project management assumes **one source of truth** controlled top-down. AI collaboration requires **distributed authority**:

- **AI agent** suggests changes following global MGMT patterns
- **Human developer** evaluates fit for project context
- **Both** can be right simultaneously - AI follows framework, human adapts to reality

Ostrom showed that commons (shared resources) thrive under polycentric governance because:

1. **Local knowledge matters** - Your project's constraints aren't in any global rulebook
2. **Flexibility beats rigidity** - Adapt patterns instead of forcing compliance
3. **Innovation happens everywhere** - Best practices emerge from experiments, not mandates

**MGMT as commons:** The workflow patterns are shared infrastructure. You benefit from others' discoveries (via MGMT updates) while contributing your own (via gaps documentation). Polycentric structure keeps this sustainable.

---

### Key Principles

1. **Multiple centers of power:** Global MGMT defines framework, projects adapt to context
2. **Overlapping not separate:** Project POLICY.md **extends** (not replaces) global/POLICY.md
3. **Self-organized correction:** When MGMT updates, projects decide whether/when to adopt
4. **No top-down mandates:** Global provides patterns, projects choose implementations

**Example:** Epic format syntax lives in global/POLICY.md, but Librarian's "requires reindexing?" column lives in project POLICY.md. Both valid simultaneously.

**Further reading:** Elinor Ostrom - "Governing the Commons", Vincent Ostrom - "The Meaning of Federalism"

---

## What is MGMT?

A meta-documentation system that provides:

1. **Workflow prompts** (MGMT-start, MGMT-end, MGMT-update)
2. **Universal policies** (epic dance, semantic versioning, branch strategy)
3. **Validation checks** (documentation sync, navigation blocks, formatting)
4. **Update mechanism** (fetch latest MGMT system from repo)

---

## How It Works

**Global files** (in this folder) define **HOW** to manage projects.
**Project files** (in parent MGMT/) are created **BY FOLLOWING** global prompts.

```
MGMT/
  # Project files (you create by following prompts)
  CHANGELOG.md       # Your version history
  ROADMAP.md         # Your planned features
  POLICY.md          # Extends global/POLICY.md
  CHECKS.md          # Includes global/CHECKS.md
  gaps/              # Your discoveries
  schemas/           # Your data structures
  epic-notes/        # Your session logs

  # Global files (imported from MGMT repo)
  global/
    README.md        # This file
    POLICY.md        # Universal workflow rules
    CHECKS.md        # Universal validation tests
    update-MGMT.py   # Update script
```

---

## Files in This Folder

### POLICY.md

Universal workflow rules that apply to ALL projects:

- Epic format syntax
- Branch strategy (epic dance)
- Semantic versioning
- Commit message format
- Rebase vs merge policies

### CHECKS.md

Universal validation tests:

- Navigation block validation
- Documentation sync checks
- Formatting standards
- Status file completeness

### update-MGMT.py

Script to update global MGMT files from repo:

```bash
python3.11 MGMT/global/update-MGMT.py
```

---

## Updating MGMT

When new MGMT versions are released:

1. Run `/MGMT-update` prompt (or `python3.11 MGMT/global/update-MGMT.py`)
2. Script fetches MGMT repo CHANGELOG
3. Shows what changed per version
4. If you confirm, overwrites files in `MGMT/global/`
5. Your project files stay untouched

**Files that update:**

- `MGMT/global/*` (all global files)
- `.github/prompts/MGMT-*.prompt.md` (workflow prompts)

**Files that stay:**

- `MGMT/CHANGELOG.md` (your version history)
- `MGMT/ROADMAP.md` (your features)
- `MGMT/POLICY.md` (your extensions)
- `MGMT/CHECKS.md` (your tests)
- `MGMT/gaps/`, `schemas/`, `epic-notes/` (your content)

---

## Philosophy

**MGMT provides structure, you provide content.**

Global files are like a framework - they define patterns and workflows.
Project files implement those patterns for your specific project.

Example:

- `global/POLICY.md` says "Use epic format: `[🚧](link) Title`"
- Your `ROADMAP.md` follows that format for YOUR epics

---

## Version History

**v1.0.0** (2026-01-26)

- Initial extraction from Librarian MCP
- Created global/ folder structure
- Decoupled MGMT from project files

---

**Last updated:** 2026-01-26
**MGMT Repo:** https://github.com/nonlinear/MGMT (coming soon)
