#!/bin/bash
# gitignore-local.sh - Verify .git/info/exclude has BYOB entries

EXCLUDE_FILE=".git/info/exclude"

if [ ! -f "$EXCLUDE_FILE" ]; then
    echo "❌ Missing .git/info/exclude"
    exit 1
fi

# Check for BYOB entries
if ! grep -q "books/\*\*/\*.epub" "$EXCLUDE_FILE" || \
   ! grep -q "engine/models/" "$EXCLUDE_FILE"; then
    echo "❌ .git/info/exclude missing BYOB entries"
    echo "Expected: books/**/*.epub, books/**/*.pkl, etc."
    exit 1
fi

echo "✅ .git/info/exclude configured (BYOB entries present)"
exit 0
