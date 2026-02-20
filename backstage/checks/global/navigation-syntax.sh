#!/bin/bash
# DESCRIPTION: Navigation blocks stay current. Prevents stale metadata drift.
# TYPE: deterministic
# SCOPE: global
#
# Unified navigation block management:
# 0. Validates README has navigation block (readable)
# 1. Updates blocks (counts files, generates links)
# 2. Validates README has block
# 3. Validates status files have blocks

set -e

# ============================================================================
# STEP 0: Validate README readable (navigation block exists)
# ============================================================================

if [[ ! -f README.md ]]; then
    echo "❌ No README.md found"
    exit 1
fi

if ! grep -q '> 🤖' README.md; then
    echo "❌ README.md missing navigation block"
    exit 1
fi

# ============================================================================
# STEP 1: Update navigation blocks
# ============================================================================

# Detect version (from branch or VERSION file)
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [[ "$BRANCH" == "main" ]]; then
    VERSION=$(cat backstage/VERSION 2>/dev/null || echo "0.3.4")
elif [[ "$BRANCH" =~ ^v([0-9]+\.[0-9]+\.[0-9]+) ]]; then
    VERSION="${BASH_REMATCH[1]}"
else
    VERSION=$(cat backstage/VERSION 2>/dev/null || echo "0.3.4")
fi

# Count ALL files in checks/ folders (.sh AND .md, exclude README.md)
CHECKS_LOCAL=$(find backstage/checks/local \( -name "*.sh" -o -name "*.md" \) ! -name "README.md" 2>/dev/null | wc -l | tr -d ' ')
CHECKS_GLOBAL=$(find backstage/checks/global \( -name "*.sh" -o -name "*.md" \) ! -name "README.md" 2>/dev/null | wc -l | tr -d ' ')

# Update README.md navigation block
if [[ -f README.md ]] && grep -q "> 🤖" README.md; then
    awk -v ver="$VERSION" -v cl="$CHECKS_LOCAL" -v cg="$CHECKS_GLOBAL" '
        BEGIN { in_nav=0; done=0 }
        /^> 🤖$/ {
            if (in_nav == 0) {
                in_nav = 1
                next
            } else {
                in_nav = 0
                if (done == 0) {
                    print ""
                    print "> 🤖"
                    print ">"
                    print "> This project follows [backstage protocol](https://github.com/nonlinear/backstage) v" ver
                    print ">"
                    print "> [README](README.md) 👏 [ROADMAP](backstage/ROADMAP.md) 👏 [CHANGELOG](backstage/CHANGELOG.md) 👏 checks: [local](backstage/checks/local/) <sup>" cl "</sup>, [global](backstage/checks/global/) <sup>" cg "</sup>"
                    print ">"
                    print "> 🤖"
                    print ""
                    done = 1
                }
                next
            }
        }
        in_nav == 0 { print }
    ' README.md > /tmp/readme_updated.md && mv /tmp/readme_updated.md README.md
fi

# Update backstage files navigation blocks
for file in backstage/ROADMAP.md backstage/CHANGELOG.md; do
    if [[ -f "$file" ]] && grep -q "> 🤖" "$file"; then
        awk -v ver="$VERSION" -v cl="$CHECKS_LOCAL" -v cg="$CHECKS_GLOBAL" '
            BEGIN { in_nav=0; done=0 }
            /^> 🤖$/ {
                if (in_nav == 0) {
                    in_nav = 1
                    next
                } else {
                    in_nav = 0
                    if (done == 0) {
                        print ""
                        print "> 🤖"
                        print "> This project follows [backstage protocol](https://github.com/nonlinear/backstage) v" ver
                        print ">"
                        print "> - [README](../README.md) 👏 [ROADMAP](ROADMAP.md) 👏 [CHANGELOG](CHANGELOG.md) 👏 checks: [local](checks/local/) <sup>" cl "</sup>, [global](checks/global/) <sup>" cg "</sup>"
                        print ">"
                        print "> 🤖"
                        print ""
                        done = 1
                    }
                    next
                }
            }
            in_nav == 0 { print }
        ' "$file" > /tmp/file_updated.md && mv /tmp/file_updated.md "$file"
    fi
done

# ============================================================================
# STEP 2: Validate README has block
# ============================================================================

if ! grep -q '> 🤖' README.md 2>/dev/null; then
    echo "❌ README.md missing navigation block"
    exit 1
fi

# ============================================================================
# STEP 3: Validate status files have blocks
# ============================================================================

MISSING=0
for file in backstage/CHANGELOG.md backstage/ROADMAP.md; do
    if [[ -f "$file" ]] && ! grep -q '> 🤖' "$file"; then
        echo "❌ Missing navigation block in $file"
        MISSING=1
    fi
done

if [[ $MISSING -eq 1 ]]; then
    exit 1
fi

# ============================================================================
# Success
# ============================================================================

echo "✅ Navigation blocks OK (v$VERSION, checks: ${CHECKS_LOCAL}+${CHECKS_GLOBAL})"
exit 0
