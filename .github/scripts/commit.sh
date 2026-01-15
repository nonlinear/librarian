#!/bin/bash

MSG="$1"

OUTPUT=$(git add -A 2>&1 && git commit -m "$MSG" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    git pull && git push
    osascript -e 'display notification "Changes committed and pushed" with title "📚 Personal Library - Success"'
elif echo "$OUTPUT" | grep -q 'nothing to commit'; then
    osascript -e 'display notification "No changes to commit" with title "📚 Personal Library - Nothing to commit"'
else
    osascript -e 'display notification "Check terminal for details" with title "❌ Personal Library - Error"'
    echo "$OUTPUT"
    exit 1
fi
