#!/bin/bash
# DESCRIPTION: Work is committed. Prevents uncommitted changes drift.
# TYPE: deterministic
# SCOPE: global
# Documentation Sync Check - Changes in code must be reflected in docs

if git diff --quiet; then
  echo '✅ No uncommitted changes'
else
  echo '⚠️ Uncommitted changes - run backstage to sync docs (see https://github.com/nonlinear/backstage#installation--usage)'
fi
