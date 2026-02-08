#!/bin/bash
# Retroactive screenshot generator for diagram evolution

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EPIC_FILE="backstage/epic-notes/v0.15.0-skill-protocol.md"
SCREENSHOT_DIR="backstage/epic-notes/screenshots"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Commits to screenshot (oldest to newest)
COMMITS=(
  "d08ae78"
  "d8094af"
  "8c976c1"
  "36635dd"
  "8fb2176"
  "90ff226"
  "097a512"
)

cd "$REPO_ROOT"

echo "📸 Generating retroactive screenshots..."
echo "📁 Epic file: $EPIC_FILE"
echo "💾 Saving to: $SCREENSHOT_DIR"
echo ""

mkdir -p "$SCREENSHOT_DIR"

for COMMIT in "${COMMITS[@]}"; do
  echo "🔄 Checking out $COMMIT..."
  git checkout "$COMMIT" --quiet
  
  # Extract commit timestamp
  TIMESTAMP=$(git show -s --format=%ct "$COMMIT")
  
  # Screenshot filename
  OUTPUT="$SCREENSHOT_DIR/15-arch-v${TIMESTAMP}.png"
  
  echo "📸 Screenshotting: $OUTPUT"
  
  # Use mmdc (mermaid-cli) to render
  if command -v mmdc &> /dev/null; then
    mmdc -i "$EPIC_FILE" -o "$OUTPUT" -t dark -b transparent 2>&1 | grep -v "Warning:"
    echo "✅ Saved: $OUTPUT"
  else
    echo "❌ mmdc not found - install @mermaid-js/mermaid-cli globally"
    exit 1
  fi
  
  echo ""
done

echo "🔙 Returning to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH" --quiet

echo ""
echo "✅ Done! Generated ${#COMMITS[@]} screenshots"
echo "📂 Location: $SCREENSHOT_DIR"
