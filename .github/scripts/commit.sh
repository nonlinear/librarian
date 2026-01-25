#!/bin/bash

MSG="$1"

# Check if Hugo project (has config.toml)
if [ -f "config.toml" ]; then
    echo "🔨 Building Hugo site..."
    hugo --config config.toml --destination docs
    if [ $? -ne 0 ]; then
        echo "❌ Hugo build failed!"
        exit 1
    fi
fi

OUTPUT=$(git add -A 2>&1 && git commit -m "$MSG" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    git pull && git push
    # Silent success
    exit 0
elif echo "$OUTPUT" | grep -q 'nothing to commit'; then
    # Silent nothing to commit
    exit 0
else
    # Show error in terminal
    echo "❌ Commit failed:"
    echo "$OUTPUT"
    exit 1
fi
