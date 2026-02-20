#!/bin/bash
# ---
# DESCRIPTION: Auto-link epic-notes to corresponding epics in ROADMAP
# TYPE: deterministic
# SCOPE: global
# ---

set -e

ROADMAP="backstage/ROADMAP.md"
EPIC_NOTES_DIR="backstage/epic-notes"

# Check if epic-notes directory exists
if [[ ! -d "$EPIC_NOTES_DIR" ]]; then
    echo "✅ No epic-notes directory, skipping"
    exit 0
fi

# Find all epic-notes (files or folders starting with v)
EPIC_NOTES=$(find "$EPIC_NOTES_DIR" -maxdepth 1 -name "v*" | sort)

if [[ -z "$EPIC_NOTES" ]]; then
    echo "✅ No epic-notes found, skipping"
    exit 0
fi

UNLINKED=()

# For each epic-note, check if linked in ROADMAP
for NOTE_PATH in $EPIC_NOTES; do
    NOTE_NAME=$(basename "$NOTE_PATH")
    VERSION=$(echo "$NOTE_NAME" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+')
    
    if [[ -z "$VERSION" ]]; then
        continue
    fi
    
    # Check if ROADMAP has epic with this version AND a link to epic-notes
    if ! grep -q "^## $VERSION" "$ROADMAP" 2>/dev/null; then
        # Epic doesn't exist in ROADMAP (probably in CHANGELOG)
        continue
    fi
    
    # Extract epic section
    EPIC_SECTION=$(awk "/^## $VERSION/,/^## v/" "$ROADMAP")
    
    # Check if section has link to epic-notes
    if ! echo "$EPIC_SECTION" | grep -q "epic-notes/$NOTE_NAME"; then
        UNLINKED+=("$VERSION")
    fi
done

# Report unlinked epic-notes
if [[ ${#UNLINKED[@]} -gt 0 ]]; then
    echo "❌ Epic-notes exist but not linked in ROADMAP:"
    for VERSION in "${UNLINKED[@]}"; do
        NOTE_PATH=$(find "$EPIC_NOTES_DIR" -maxdepth 1 -name "${VERSION}*" | head -1)
        NOTE_NAME=$(basename "$NOTE_PATH")
        
        # Determine if folder or file
        if [[ -d "$NOTE_PATH" ]]; then
            LINK="epic-notes/$NOTE_NAME/"
        else
            LINK="epic-notes/$NOTE_NAME"
        fi
        
        echo "  $VERSION → Add link: [$LINK]($LINK)"
        
        # Auto-add link to epic title
        EPIC_LINE=$(grep "^## $VERSION" "$ROADMAP")
        
        # Check if already has pipe separator (for existing notes link)
        if echo "$EPIC_LINE" | grep -q " | "; then
            # Already has link, skip
            continue
        fi
        
        # Add link to epic title: ## v1.0.1 → ## v1.0.1 | [notes](epic-notes/...)
        sed -i '' "s@^## $VERSION\$@## $VERSION | [notes]($LINK)@" "$ROADMAP"
    done
    
    echo "✅ Links added to ROADMAP"
else
    echo "✅ All epic-notes linked in ROADMAP"
fi

exit 0
