#!/bin/bash
# Watch epic notes and screenshot Typora window on save

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EPIC_DIR="$REPO_ROOT/backstage/epic-notes"
SCREENSHOT_DIR="$EPIC_DIR/screenshots"

echo "🔍 Watching diagrams in: $EPIC_DIR"

mkdir -p "$SCREENSHOT_DIR"

# Check if fswatch is installed
if ! command -v fswatch &> /dev/null; then
    echo "⚠️  fswatch not installed. Install with: brew install fswatch"
    echo "📸 For now, use manual mode: $0 manual <file>"
    exit 1
fi

# Watch for .md file changes in epic-notes/
fswatch -0 --event Updated "$EPIC_DIR"/*.md | while read -d "" file; do
    BASENAME=$(basename "$file" .md)
    TIMESTAMP=$(date +%s)
    OUTPUT="$SCREENSHOT_DIR/${BASENAME}-v${TIMESTAMP}.png"
    
    echo "📝 Detected change: $file"
    echo "📸 Capturing Typora window..."
    
    # Capture Typora window (assumes Typora is frontmost or has the file open)
    # -l option captures specific window by window ID
    # For now, capture frontmost Typora window
    screencapture -o -w "$OUTPUT" 2>/dev/null
    
    if [ -f "$OUTPUT" ]; then
        echo "✅ Saved: $OUTPUT"
    else
        echo "❌ Failed to capture. Is Typora open with the file?"
    fi
    
    echo ""
done
