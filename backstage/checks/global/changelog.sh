#!/bin/bash
# DESCRIPTION: Recent commits exist in CHANGELOG. Prevents undocumented changes drift.
# TYPE: deterministic
# SCOPE: global

# Get last CHANGELOG entry date
LAST_ENTRY_DATE=$(grep -E '^## v[0-9]+\.[0-9]+\.[0-9]+ - ' backstage/CHANGELOG.md 2>/dev/null | head -1 | sed 's/.*- //')

if [[ -z "$LAST_ENTRY_DATE" ]]; then
    echo "⚠️  No CHANGELOG entries found"
    exit 0
fi

# Convert to git-compatible date
LAST_DATE=$(date -j -f "%Y-%m-%d" "$LAST_ENTRY_DATE" "+%Y-%m-%d" 2>/dev/null || echo "")

if [[ -z "$LAST_DATE" ]]; then
    echo "⚠️  Could not parse CHANGELOG date"
    exit 0
fi

# Get commits since last CHANGELOG entry
RECENT_COMMITS=$(git log --since="$LAST_DATE" --oneline --no-merges 2>/dev/null | wc -l | tr -d ' ')

if [[ "$RECENT_COMMITS" -gt 0 ]]; then
    echo "⚠️  $RECENT_COMMITS commits since last CHANGELOG entry ($LAST_DATE)"
    echo "   Add entry to backstage/CHANGELOG.md"
    exit 0
else
    echo "✅ CHANGELOG up-to-date (no commits since $LAST_DATE)"
fi
