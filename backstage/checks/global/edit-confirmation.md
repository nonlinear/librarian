#!/bin/bash
# ---
# DESCRIPTION: Prevent AI from editing README or memory files without checking
# TYPE: interpretive
# SCOPE: global
# ---

# This is a POLICY check (interpretive) - AI must read and enforce.
# NO automated validation. AI judgment required.

cat << 'EOF'

❌ EDIT CONFIRMATION POLICY (AI ENFORCEMENT REQUIRED)

## README.md

NEVER edit README.md without EXPLICIT user confirmation.

Before any README change:
1. ASK: "Want me to edit README? Here's what I'll change: [show diff preview]"
2. WAIT for YES/NO
3. Only edit if YES

README is public-facing. Changes must be deliberate, not automatic.

Exception: Navigation block updates (automated by navigation-syntax.sh)

## memory/YYYY-MM-DD.md

BEFORE editing today's memory file:
1. CHECK if Nicholas already wrote to it
2. If YES → APPEND ONLY (add new section at end)
3. If NO → Safe to create/write

NEVER overwrite Nicholas's memory entries.
NEVER edit existing sections.
ONLY append new findings.

Memory files = append-only log, not editable document.

---

AI MUST enforce this policy during every session.

EOF

exit 0
