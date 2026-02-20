# Dual Track Development

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
