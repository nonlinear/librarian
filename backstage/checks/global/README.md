# Global Policy Purpose

This folder contains **universal, project-agnostic** workflow rules and conventions.

**POLICY.md** (project-specific) extends or overrides these global rules for specific projects.

**How this works:**
- **Global POLICY** = Foundation (universal rules, all projects)
- **Project POLICY** = Customization (local needs, context-specific)
- **Project wins on conflict** (polycentric governance)
- **AI reads both** (merges when compatible, prefers project when not)

**Enforced by:** [backstage-skill](https://clawhub.com/skills/backstage) (runs on "good morning" / "good night")

---

**Inspired by:** Elinor Ostrom's polycentric governance framework—multiple centers of power (global/project) with overlapping, not hierarchical, jurisdictions.

---

**Files in this folder:**

- `branch-workflow.md` - Branch naming, epic dance, merge protocol
- `commit-style.md` - Commit messages, typo checking, rigor rules
- `context-snapshot.md` - Context headers for stateless AI
- `dual-track.md` - Dual track development pattern
- `epic-format.md` - Epic syntax, tasks, success criteria, metadata links
- `epic-notes.md` - When to separate, folder structure, links
- `formatting.md` - Human/machine readable rules
- `install-update.md` - Backstage installation, framework updates
- `navigation-block.md` - Navigation format, placement, mermaid diagrams
- `pre-commit.md` - Pre-commit workflow checklist
- `rebase-merge.md` - When to rebase vs merge
- `semver.md` - Semantic versioning, auto-renumbering

**Last updated:** 2026-02-18  
**Version:** 2.0 (Exploded from monolithic POLICY.md)  
**Source:** Elinor Ostrom's polycentric governance principles
