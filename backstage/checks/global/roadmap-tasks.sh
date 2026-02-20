#!/bin/bash
# DESCRIPTION: Completed work marked in ROADMAP. Triggers merge-to-main when all tasks done.
# TYPE: deterministic
# SCOPE: global

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Only check epic branches (v*.*.* or epic/*)
if [[ ! "$BRANCH" =~ ^v[0-9]+\.[0-9]+\.[0-9]+ ]] && [[ ! "$BRANCH" =~ ^epic/ ]]; then
    echo "⏭️  Not an epic branch (skipped)"
    exit 0
fi

# Extract version from branch name
if [[ "$BRANCH" =~ ^v([0-9]+\.[0-9]+\.[0-9]+) ]]; then
    VERSION="${BASH_REMATCH[1]}"
elif [[ "$BRANCH" =~ ^epic/v([0-9]+\.[0-9]+\.[0-9]+) ]]; then
    VERSION="${BASH_REMATCH[1]}"
else
    echo "⚠️  Epic branch but can't extract version from name: $BRANCH"
    exit 0
fi

# Check if ROADMAP has this epic
if [[ ! -f backstage/ROADMAP.md ]]; then
    echo "⚠️  No ROADMAP.md found"
    exit 0
fi

# Find epic section in ROADMAP
if ! grep -q "^## v$VERSION" backstage/ROADMAP.md; then
    echo "⚠️  Epic v$VERSION not found in ROADMAP"
    exit 0
fi

# Extract epic section (from ## vX.Y.Z to next ## or ---)
START_LINE=$(grep -n "^## v$VERSION\$" backstage/ROADMAP.md | cut -d: -f1)
END_LINE=$(tail -n +$((START_LINE + 1)) backstage/ROADMAP.md | grep -n "^## \|^---" | head -1 | cut -d: -f1)

if [[ -z "$END_LINE" ]]; then
    # No next section, read to EOF
    EPIC_SECTION=$(tail -n +$START_LINE backstage/ROADMAP.md)
else
    # Read until next section
    EPIC_SECTION=$(sed -n "${START_LINE},$((START_LINE + END_LINE - 1))p" backstage/ROADMAP.md)
fi

# Count tasks
TOTAL_TASKS=$(echo "$EPIC_SECTION" | grep -c "^- \[")
DONE_TASKS=$(echo "$EPIC_SECTION" | grep -c "^- \[x\]")
TODO_TASKS=$(echo "$EPIC_SECTION" | grep -c "^- \[ \]")

# If no tasks defined, skip
if [[ $TOTAL_TASKS -eq 0 ]]; then
    echo "✅ Epic v$VERSION has no tasks defined"
    exit 0
fi

# Report status
if [[ $TODO_TASKS -eq 0 ]]; then
    echo "✅ All tasks complete in epic v$VERSION ($DONE_TASKS/$TOTAL_TASKS)"
    echo "🚦 Ready for merge-to-main workflow"
    exit 0
else
    echo "📋 Epic v$VERSION progress: $DONE_TASKS/$TOTAL_TASKS tasks done ($TODO_TASKS remaining)"
    exit 0
fi
