#!/bin/bash
# Screenshot on save, commit, done.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EPIC_DIR="$REPO_ROOT/backstage/epic-notes"
SCREENSHOT_DIR="$EPIC_DIR/screenshots"

mkdir -p "$SCREENSHOT_DIR"
cd "$REPO_ROOT"

fswatch -0 --event Updated "$EPIC_DIR"/*.md | while read -d "" file; do
    BASENAME=$(basename "$file" .md)
    TIMESTAMP=$(date +%s)
    OUTPUT="$SCREENSHOT_DIR/${BASENAME}-v${TIMESTAMP}.png"
    
    # Screenshot
    screencapture -x "$OUTPUT"
    
    # Commit
    git add "$file" "$OUTPUT"
    git commit -m "arch: $(basename "$file" .md)" -m "Auto @ $(date +%H:%M:%S)"
done
