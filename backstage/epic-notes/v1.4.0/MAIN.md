# v1.4.0 - Reader Integration & Granularity

## Epic Overview

**Goal:** Deep-link citations to exact reading position in EPUB/PDF reader (Kavita or alternative) + add paragraph/page/chapter granularity.

**Current State:**
- User reads books in Kavita (http://192.168.1.152:5000)
- Librarian indexes same folder
- Citations are file-level only: `[Molecular Red.epub](path)`
- No deep-link to reader app
- No paragraph/page/chapter info

**Vision:** Click citation → Opens book in reader at exact paragraph where quote lives

---

## Files in This Epic

- **[MAIN.md](MAIN.md)** — You're here! Overview & session notes
- **[reader-comparison.md](reader-comparison.md)** — Kavita vs Calibre vs Readium vs others
- **[kavita-research.md](kavita-research.md)** — Kavita API/URL scheme investigation
- **[granularity-extraction.md](granularity-extraction.md)** — How to extract paragraph/page/chapter from EPUB/PDF
- **[citation-formats.md](citation-formats.md)** — UX design for citation links
- **[risks.md](risks.md)** — Reading interruption, fallbacks, edge cases

---

## Session Notes

### 2026-01-30: Epic Created

**Context:** User idea during braindump session
- Uses Kavita to read books (same folder Librarian indexes)
- Example: Molecular Red = http://192.168.1.152:5000/library/1/series/522#specials-tab
- Wants citations to deep-link to reading position
- Concerns: Reading interruption risk, granularity accuracy

**Decision Points Needed:**
1. Which reader to target? (Kavita, Calibre, Readium, Apple Books?)
2. What granularity is achievable? (paragraph ideal, page acceptable, chapter minimum)
3. How to handle reading interruption UX?

**Next Steps:**
- Research Kavita URL scheme
- Compare alternative readers
- Test EPUB paragraph ID extraction
