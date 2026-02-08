#!/bin/bash
# Auto-commit epic notes on save + screenshot full screen

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EPIC_DIR="$REPO_ROOT/backstage/epic-notes"
SCREENSHOT_DIR="$EPIC_DIR/screenshots"

echo "🔍 Watching: $EPIC_DIR/*.md"
echo "📸 Screenshots: $SCREENSHOT_DIR"
echo "🔄 Auto-commit enabled"
echo ""

mkdir -p "$SCREENSHOT_DIR"

cd "$REPO_ROOT"

# Watch for .md file changes in epic-notes/
fswatch -0 --event Updated "$EPIC_DIR"/*.md | while read -d "" file; do
    BASENAME=$(basename "$file" .md)
    TIMESTAMP=$(date +%s)
    OUTPUT="$SCREENSHOT_DIR/${BASENAME}-v${TIMESTAMP}.png"
    
    echo "📝 [$(date +%H:%M:%S)] Detected change: $file"
    
    # Screenshot full screen (Cmd+Shift+3)
    echo "📸 Capturing full screen..."
    screencapture -x "$OUTPUT"
    
    echo "✅ Screenshot saved: $(basename "$OUTPUT")"
    
    # Git commit
    echo "🔄 Committing changes..."
    git add "$file" "$OUTPUT" 2>/dev/null || true
    
    # Get first line of change for commit message
    FIRST_LINE=$(git diff --cached "$file" | grep "^+[^+]" | head -1 | sed 's/^+//' | cut -c1-60)
    if [ -z "$FIRST_LINE" ]; then
        FIRST_LINE="Update diagram"
    fi
    
    git commit -m "arch: $(basename "$file" .md) - $FIRST_LINE" \
               -m "Auto-commit on save @ $(date +%Y-%m-%d\ %H:%M:%S)" 2>&1 | head -1
    
    echo "✅ Committed!"
    echo ""
done
