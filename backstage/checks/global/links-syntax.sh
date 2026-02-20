#!/bin/bash
# DESCRIPTION: Navigation links work. Prevents broken reference drift.
# TYPE: deterministic
# SCOPE: global
# Link Integrity Check - Navigation links must point to existing files/folders

test -f backstage/CHANGELOG.md && \
test -f backstage/ROADMAP.md && \
test -d backstage/policies && \
test -d backstage/checks && \
echo '✅ README links valid' || echo '❌ Broken links in README'
