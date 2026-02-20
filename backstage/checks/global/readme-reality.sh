#!/bin/bash
# DESCRIPTION: README reflects actual project state. Prevents documentation staleness drift.
# TYPE: deterministic
# SCOPE: global

# Check if README exists
if [[ ! -f README.md ]]; then
    echo "❌ README.md not found"
    exit 1
fi

WARNINGS=0

# Check 1: README mentions actual scripts in repo
SCRIPTS=$(find . -maxdepth 2 -name "*.sh" -not -path "./.*" -not -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$SCRIPTS" -gt 0 ]]; then
    if ! grep -qi "script" README.md; then
        echo "⚠️  Project has scripts but README doesn't mention them"
        WARNINGS=1
    fi
fi

# Check 2: README mentions actual folder structure
if [[ -d "backstage" ]] && ! grep -q "backstage" README.md; then
    echo "⚠️  backstage/ folder exists but not mentioned in README"
    WARNINGS=1
fi

# Check 3: README mentions dependencies (if package.json exists)
if [[ -f "package.json" ]] && ! grep -qi "npm\|install\|dependencies" README.md; then
    echo "⚠️  package.json exists but README doesn't mention dependencies"
    WARNINGS=1
fi

if [[ $WARNINGS -eq 0 ]]; then
    echo "✅ README reflects project reality"
fi

exit 0
