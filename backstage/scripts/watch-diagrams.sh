#!/bin/bash
# Watch epic-notes/*.md files and auto-generate PNG screenshots on save
# Screenshots saved in folder matching .md filename

WATCH_DIR="$HOME/Documents/librarian/backstage/epic-notes"

echo "🔍 Watching diagrams in: $WATCH_DIR"

# Monitor file changes using fswatch (macOS)
fswatch -o "$WATCH_DIR"/*.md | while read f; do
    for file in "$WATCH_DIR"/*.md; do
        filename=$(basename "$file" .md)
        screenshot_dir="$WATCH_DIR/$filename"
        mkdir -p "$screenshot_dir"
        
        timestamp=$(date +%s)
        output="$screenshot_dir/diagram-v${timestamp}.png"
        
        # Try Typora CLI export (if available)
        if command -v typora &> /dev/null; then
            typora "$file" --export "$output" 2>/dev/null
        else
            echo "⚠️  Typora CLI not found. Install with: brew install typora"
            echo "📝 Manual: Save diagram as PNG in Typora"
        fi
        
        if [ -f "$output" ]; then
            echo "✅ Screenshot: $output"
        fi
    done
done
