# research.py - Topic/Book Required (Not Optional)

**Date:** 2026-02-10  
**Status:** 🔴 Bug identified, NOT fixed yet (Nicholas said don't fix now)

---

## Problem

**Current behavior (WRONG):**
```python
# research.py lines 275-295
if not topic_id:
    # Default to first topic with data ← VIOLATES DESIGN!
    for t in metadata['topics']:
        topic_dir = BOOKS_DIR / t['id']
        if (topic_dir / ".faiss.index").exists():
            topic_id = t['id']  # Auto-selects first indexed topic
            break
```

**What happens:**
- User runs: `research.py "DeLanda Philosophy"` (no `--topic` or `--book`)
- Script silently defaults to FIRST indexed topic (probably `cooking`)
- Returns bread recipes instead of theory/system content
- **User has NO IDEA what topic was searched!**

---

## Design Violation

**From `librarian-research-flow.md` diagram:**
```
RUN_PY[⚙️ RESEARCH.PY
FAISS search on specified topic
NEVER auto-selects        ← WE'RE VIOLATING THIS!
NEVER multiple topics]
```

**Nicholas's rule (repeated multiple times):**
- "busca SEMPRE tem que ter topics ou books"
- "`--topic` ou `--book` OBRIGATORIO"
- "topic our book OBRIGATORIO"

---

## Correct Behavior

**`--topic` OR `--book` MUST be specified:**

```bash
# ✅ CORRECT
research.py "query" --topic theory/system
research.py "query" --book "Philosophy and Simulation.epub"

# ❌ WRONG (should ERROR)
research.py "query"  # No topic/book specified
```

**Error message when neither provided:**
```
Error: Must specify --topic or --book
Usage: research.py "query" --topic TOPIC_ID
   or: research.py "query" --book FILENAME
```

---

## Fix (DON'T IMPLEMENT YET)

**Location:** `research.py` lines 275-295

**Replace:**
```python
if not topic_id:
    # Default to first topic with data
    for t in metadata['topics']:
        topic_dir = BOOKS_DIR / t['id']
        if (topic_dir / ".faiss.index").exists():
            topic_id = t['id']
            break
```

**With:**
```python
if not topic_id and not book:
    return {
        'results': [],
        'metadata': {
            'query': query,
            'error': 'Must specify --topic or --book'
        }
    }
```

---

## Why Not Fixed Yet

**Nicholas said:**
- "Dont ix it now"
- "dont fiz it no"

**Reason:** We're in backstage epic, testing/documenting first.

**When to fix:** After Nicholas reviews this note and confirms approach.

---

## Related Files

- `research.py` (lines 275-295) - needs fix
- `librarian-research-flow.md` - design diagram (source of truth)
- `memory/2026-02-10.md` - documented wrong behavior + correction lesson

---

**Next:** Wait for Nicholas to say "agora pode corrigir" before implementing fix. 🏴
