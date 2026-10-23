#!/bin/sh
# pre-push hook — publish the installed librarian skill into skills/ before pushing.
#
# Source of truth for content: ~/.openclaw/skills/librarian/ (installed, canonical).
# This repo carries a read-only COPY so anyone who clones it gets the protocol
# without an OpenClaw environment. Direction is always installed -> repo.
#
# Install: cp scripts/git-hooks-pre-push.sh .git/hooks/pre-push

set -e

SKILLS_SRC="$HOME/.openclaw/skills"
SKILLS_DEST="$(git rev-parse --show-toplevel)/skills"
RELEVANT_SKILLS="librarian"

mkdir -p "$SKILLS_DEST"

for name in $RELEVANT_SKILLS; do
  if [ -d "$SKILLS_SRC/$name" ]; then
    rm -rf "$SKILLS_DEST/$name"
    cp -r "$SKILLS_SRC/$name" "$SKILLS_DEST/$name"
    # Do not publish macOS artifacts into the repo.
    find "$SKILLS_DEST/$name" -name '.DS_Store' -delete 2>/dev/null || true
    echo "pre-push: synced skill '$name' -> skills/$name"
  else
    echo "pre-push: WARNING — skill '$name' not found at $SKILLS_SRC/$name, skipping"
  fi
done

cd "$(git rev-parse --show-toplevel)"
if ! git diff --quiet -- skills/ 2>/dev/null || [ -n "$(git status --porcelain -- skills/)" ]; then
  git add skills/
  git commit -m "chore(skills): sync latest skill snapshot (pre-push automation)" -- skills/ >/dev/null 2>&1 || true
  echo "pre-push: committed skill snapshot update"
fi
