#!/bin/bash
# DESCRIPTION: Required files exist. Prevents missing structure drift.
# TYPE: deterministic
# SCOPE: global
# Required files/folders syntax - Backstage structure must exist

# Project files
test -f README.md && \
test -f backstage/ROADMAP.md && \
test -f backstage/CHANGELOG.md && \
test -d backstage/checks && \
# Global folders
test -d backstage/checks/global && \
echo '✅ Required structure exists' || echo '❌ Missing files/folders'
