# Deprecated Script Time-Wasting - Post-Mortem

**Date:** 2026-01-27
**Context:** User added new folder (`technology/internet of things`) and asked how to reindex

## What Went Wrong

1. **Suggested deprecated script** (`generate_metadata.py`)
   - Script was already deleted from main folder
   - Existed only in `/deprecated/` folder
   - Has hardcoded wrong path: `Path(__file__).parent.parent / "books"` (should be `.parent.parent.parent`)

2. **Didn't check active scripts first**
   - `index_library.py` already had ALL the functionality needed
   - But had missing feature: folder discovery (which I added)

3. **Time waste: ~15 minutes** trying to run wrong script

## What Was Actually Needed

**Before (broken state):**

- `library-index.json` manually maintained
- New folders not auto-discovered
- Had to run separate `generate_metadata.py` first
- Then run `index_library.py`

**After (fixed):**

```bash
# ONE command does everything:
python3.11 engine/scripts/index_library.py

# Automatically:
# 1. Scans books/ for new folders
# 2. Updates library-index.json
# 3. Smart-detects changes
# 4. Indexes only what changed
```

## Root Cause

**Fragmented logic across multiple scripts:**

- `generate_metadata.py` - scan folders → library-index.json
- `index_library.py` - read library-index.json → index books
- **Problem:** Two-step process, easy to forget first step

**User insight:** "Shouldn't ONE script do both?"
**Answer:** YES! That's exactly right.

## The Fix

Added to `index_library.py`:

1. **`scan_library_folders()`** - discovers all topic folders recursively
2. **`update_library_index()`** - updates library-index.json with new topics
3. **Auto-runs on every invocation** - no separate step needed

Now the flow is:

```python
# ALWAYS runs (fast, <100ms)
discovered_topics = scan_library_folders()
registry, new_count = update_library_index(discovered_topics)

# Then proceed with indexing based on mode (--smart, --all, etc.)
```

## Lessons Learned

### 1. Consolidate Related Logic

**❌ DON'T:**

```
generate_metadata.py  → creates metadata
index_library.py      → uses metadata
```

**✅ DO:**

```
index_library.py → scans folders + creates metadata + indexes
```

**Why:** Reduces cognitive load, fewer steps to remember, single source of truth

### 2. Flag Deprecated Scripts AGGRESSIVELY

**Added to `/deprecated/README.md`:**

```markdown
# ⚠️ DEPRECATED SCRIPTS - DO NOT USE ⚠️

**❌ DO NOT:**

- Fix bugs in these files
- Run these scripts in production
- Waste time understanding their logic

**✅ INSTEAD USE:**

- index_library.py - ONE script for everything
```

### 3. Flag Names Matter

**Changed:** `--bootstrap` → `--metadata`

**Why:**

- "bootstrap" is vague (bootstrap what?)
- "metadata" is clear (only generate metadata files)
- Matches what the flag actually does

### 4. Default to Smart Behavior

**Old:** User must know which mode to use
**New:** No flags = smart mode (auto-detect changes)

```python
# Smart mode is now the default
if not (args.smart or args.all or ...):
    args.smart = True
```

## How to Avoid This in Future

### Checklist Before Suggesting Scripts:

1. ✅ **Is script in active folder or `/deprecated/`?**
   - If deprecated → suggest alternative
   - If missing → maybe integrated into another script

2. ✅ **Can active script do this?**
   - Check `index_library.py` first
   - Check `research.py` second
   - Only then check deprecated

3. ✅ **Is this a two-step process that should be one?**
   - Scan → generate → index? → Consolidate
   - Create → update → sync? → Consolidate

### Documentation Pattern:

**Every script should have:**

```python
"""
USAGE:
    python script.py                # Default mode (smart)
    python script.py --metadata     # Only metadata
    python script.py --all          # Force all

REPLACES:
    - old_script_1.py (deprecated)
    - old_script_2.py (deprecated)
"""
```

## Current State (Correct)

**Active scripts (3 only):**

- `engine/scripts/index_library.py` - ONE script for all indexing
- `engine/scripts/research.py` - CLI queries
- `engine/scripts/mcp_server.py` - MCP wrapper (delegates to research.py)

**Deprecated folder (10+ scripts):**

- All marked with ⚠️ warnings
- README explains what to use instead
- Never referenced in docs

**Flags renamed:**

- `--metadata` (was --bootstrap) - only generate metadata
- `--smart` (default) - auto-detect changes
- `--all` - reindex everything
- `--force` - skip hash checks

## Success Metric

**Before:** User confused about which script to run, tried deprecated script, wasted time
**After:** User runs `python3.11 engine/scripts/index_library.py`, it just works

**Time saved per reindex:** ~10 minutes (no hunting for right script, no two-step process)
