# Epic Notes - When to Separate Detail from ROADMAP

**Philosophy:** ROADMAP is for **decision-makers** (what/why/done?). Epic-notes are for **implementers** (how/details/research).

## When to Create epic-notes/

**Separate into `epic-notes/vX.Y.Z/` when epic has:**

1. **Size:** >80 lines in ROADMAP (>120 = mandatory)
2. **Complexity:** >3 solution paths to compare
3. **Risks:** >3 risks with mitigations
4. **Research:** API docs, comparisons, technical specs
5. **Volatility:** Growing during implementation (session notes, discoveries)

**Rule of thumb:**
- If you scroll >2 screens to see full epic → separate
- If >3 sections have >10 lines each → separate
- If you think "this is getting confusing" → separate

## What Stays in ROADMAP

**Keep concise (30-50 lines ideal):**
- ✅ Problem statement (3-5 lines)
- ✅ Solution overview (executive summary, 3-5 lines)
- ✅ Main tasks (5-15 checkboxes, feature-level)
- ✅ Success criteria (3-5 measurable goals)
- ✅ Brief notes (1-2 lines)

## What Goes to epic-notes/

**Structure:**

```
epic-notes/vX.Y.Z/
├── MAIN.md              # Overview, session notes, links to other files
├── comparison.md        # Pros/cons tables (if comparing >2 options)
├── research.md          # APIs, URLs, test results, findings
├── risks.md             # Risks + mitigations (if >3 risks)
├── technical-spec.md    # Schemas, code examples, formats
└── decisions.md         # Architecture Decision Records (ADRs)
```

**Content types for epic-notes:**
- 📝 Detailed comparisons (tables, pros/cons)
- 📝 Risks + mitigations (>3 risks)
- 📝 Research findings (URLs, API docs, tests)
- 📝 Alternative approaches (>2 options)
- 📝 Session logs (work-in-progress notes)
- 📝 Technical specs (schemas, examples, code)
- 📝 Open questions + debates
- 📝 Subtasks (<1 day granularity)

## Link Format

**🔴 MANDATORY: Epic-notes MUST be linked from epics (ROADMAP or CHANGELOG)**

**In ROADMAP:**

```markdown
### Epic Name | [notes](epic-notes/vX.Y.Z/)
```

**In CHANGELOG:**

```markdown
### Epic Name

**Details:** [epic-notes/vX.Y.Z/MAIN.md](epic-notes/vX.Y.Z/MAIN.md)
```

**Why this rule:**
- Epic-notes exist to document work
- Unlinked notes = invisible to future readers
- Links = discoverability + accountability
- Both active (ROADMAP) and completed (CHANGELOG) epics need links

**In epic-notes/MAIN.md:**

```markdown
## Files in This Epic

- **[MAIN.md](MAIN.md)** — Overview & session notes
- **[comparison.md](comparison.md)** — Option A vs B vs C
- **[risks.md](risks.md)** — Risk analysis & mitigations
```

## Alert Signals (Time to Separate)

🚨 **Separate when you see:**
- Epic has >5 subsections (A, B, C, D, E...)
- Table with >5 rows
- >3 code blocks or examples
- >5 risks listed
- Multiple solution approaches debated
- You think "this is getting messy"

## Migration Pattern (v0.5.0+)

**Before v0.5.0:** Single file `epic-notes/v0.X.0.md`

**v0.5.0+:** Folder structure `epic-notes/v0.X.0/MAIN.md` + separate files

**When to migrate:**
- Single file exceeds ~500 lines
- Epic has >3 distinct topics/findings
- Findings are independent enough to reference separately

**How to migrate:**
1. Create folder: `mkdir epic-notes/v0.X.0/`
2. Move file: `mv epic-notes/v0.X.0.md epic-notes/v0.X.0/MAIN.md`
3. Extract major sections to separate files
4. Update links in ROADMAP
