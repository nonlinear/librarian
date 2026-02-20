#!/bin/bash
# DESCRIPTION: Epics follow standard format. Prevents roadmap structure drift.
# TYPE: deterministic
# SCOPE: global
# Epic Format Validation - Verify ROADMAP epics follow required structure

# Check if ROADMAP exists
if [[ ! -f "backstage/ROADMAP.md" ]]; then
    exit 0  # No ROADMAP = nothing to validate
fi

# Extract epics (lines starting with ## v)
EPICS=$(grep -n "^## v[0-9]" backstage/ROADMAP.md)

if [[ -z "$EPICS" ]]; then
    exit 0  # No epics = nothing to validate
fi

# Validate each epic
FAILED=0

while IFS= read -r epic_line; do
    LINE_NUM=$(echo "$epic_line" | cut -d: -f1)
    VERSION=$(echo "$epic_line" | sed 's/.*## \(v[0-9.]*\).*/\1/')
    
    # Check: Version format must be vX.Y.Z (not "## vX.Y.Z - Title")
    if echo "$epic_line" | grep -q "^## v[0-9.]* -"; then
        echo "❌ Epic $VERSION: Version header includes title (should be '## vX.Y.Z' only)"
        FAILED=1
    fi
    
    # Check: Must have ### title (skip blank lines)
    NEXT_LINE=$((LINE_NUM + 1))
    TITLE_LINE=""
    
    # Find next non-empty line
    for i in {1..5}; do
        TEST_LINE=$(sed -n "$((LINE_NUM + i))p" backstage/ROADMAP.md)
        if [[ -n "$TEST_LINE" ]]; then
            TITLE_LINE="$TEST_LINE"
            break
        fi
    done
    
    if [[ ! "$TITLE_LINE" =~ ^###\  ]]; then
        echo "❌ Epic $VERSION: Missing '### Title' after version header"
        FAILED=1
    fi
    
    # Extract epic section (until next ## or end of file)
    EPIC_SECTION=$(awk "/^## $VERSION/,/^## v[0-9]/" backstage/ROADMAP.md)
    
    # Check: Must have **Tasks:** or **Problem:**
    if ! echo "$EPIC_SECTION" | grep -q "\*\*Tasks:\*\*\|\*\*Problem:\*\*"; then
        echo "❌ Epic $VERSION: Missing **Tasks:** or **Problem:** section"
        FAILED=1
    fi
    
    # Check: Must have **Success:**
    if ! echo "$EPIC_SECTION" | grep -q "\*\*Success:\*\*"; then
        echo "❌ Epic $VERSION: Missing **Success:** section"
        FAILED=1
    fi
    
done <<< "$EPICS"

if [[ $FAILED -eq 0 ]]; then
    echo "✅ All epics follow format rules"
else
    echo "⚠️  Some epics have format warnings (see above)"
fi

exit 0  # Warning mode - don't block
