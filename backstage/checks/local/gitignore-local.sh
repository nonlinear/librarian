#!/bin/bash
# gitignore-local.sh - Verify .git/info/exclude has BYOB entries

EXCLUDE_FILE=".git/info/exclude"

if [ ! -f "$EXCLUDE_FILE" ]; then
    echo "❌ Missing .git/info/exclude"
    exit 1
fi

# Check for BYOB entries (books + models)
if ! grep -qE "books/.*\.epub" "$EXCLUDE_FILE"; then
    echo "❌ .git/info/exclude missing books BYOB entry"
    echo "Expected: books/**/*.epub (or similar pattern)"
    exit 1
fi

if ! grep -qE "(engine/)?models/" "$EXCLUDE_FILE"; then
    echo "❌ .git/info/exclude missing models entry"
    echo "Expected: models/ or engine/models/"
    exit 1
fi

echo "✅ .git/info/exclude configured (BYOB entries present)"
exit 0
