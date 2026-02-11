# Librarian SKILL.md Translation

**Epic:** v0.15.0-skill-enforcement  
**Created:** 2026-02-08  
**Goal:** Translate EXISTING librarian/SKILL.md to official skill format

---

## Current Problems

**Current SKILL.md is:**
- ❌ Protocol enforcement (checklists, warnings, threats)
- ❌ Verbose (Nicholas said "esvaziar skill")
- ❌ Mixes documentation + enforcement
- ❌ Not aligned with official skill patterns

**Should be:**
- ✅ Pure documentation (examples, syntax, workflows)
- ✅ Dense but scannable
- ✅ Enforcement lives in librarian.sh (not text)

---

## Translation Plan

### Keep (Documentation)
- Syntax examples
- Available topics list
- Troubleshooting
- Kavita integration
- Response format examples

### Remove (Enforcement)
- "ZERO TOLERANCE" warnings
- Mandatory checklists
- "READ THIS FIRST" threats
- Protocol repetition

### Move to librarian.sh
- Empty results → "não achei"
- Syntax validation
- Output formatting

---

## Proposed New SKILL.md

```markdown
---
name: librarian
description: Search Nicholas's book library (EPUBs/PDFs) via semantic search. Use when user asks to research books, find quotes, or search library by topic.
homepage: ~/Documents/librarian/README.md
metadata:
  openclaw:
    emoji: 📚
    os: ["darwin"]
    requires:
      bins: ["python3", "jq"]
---

# Librarian

Semantic search across Nicholas's book library (EPUBs, PDFs).

**Location:** `~/Documents/librarian/`  
**MacBook only** (not on NAS)

---

## When to use

Use this skill when the user asks:
- "pesquisa [topic] nos livros"
- "search books for [query]"
- "what do my books say about [topic]?"
- "find quotes about [subject]"

---

## Quick start

**Via wrapper (recommended):**
```bash
~/.openclaw/skills/librarian/librarian.sh "query text" topic-name
```

**Direct (advanced):**
```bash
cd ~/Documents/librarian && \
python3 engine/scripts/research.py "query text" --topics topic1,topic2
```

---

## Available topics

**List all:**
```bash
ls -1 ~/Documents/librarian/books/
```

**Common topics:**
- `chaos-magick`, `occult`, `witchcraft`, `tarot`
- `anarchism`, `politics`, `philosophy`
- `finance`, `business`, `economics`
- `sci-fi`, `fiction`, `short-stories`
- `tech`, `programming`, `systems`

**Note:** Folder names = topic IDs (use exact names: lowercase, hyphens)

---

## Wrapper (librarian.sh)

**The wrapper handles:**
- Syntax validation
- Empty results ("não achei")
- Output formatting (numbered citations)
- Error messages (missing index, invalid topic)

**Example:**
```bash
~/.openclaw/skills/librarian/librarian.sh "servitors in chaos magick" chaos-magick
```

**Output (if found):**
```
📚 **RESEARCH:** servitors in chaos magick

Achei **2 resultado(s)**.

1️⃣ **Servitor Creation**
**Fonte:** *Condensed Chaos* by Phil Hine

> A servitor is a semi-autonomous entity created for a specific purpose...

---

2️⃣ **Programming Servitors**
**Fonte:** *The Chaos Protocols*

> Once created, a servitor must be programmed with clear intent...
```

**Output (if empty):**
```
❌ Não achei resultados sobre "servitors" no topic "chaos-magick".
```

---

## Direct usage (research.py)

**Syntax:**
```bash
cd ~/Documents/librarian && \
python3 engine/scripts/research.py "QUERY" --topics topic1,topic2
```

**Parameters:**
- `"QUERY"` - Exact search query (always quoted)
- `--topics topic1,topic2` - Comma-separated (NO SPACES)
- `--max-results N` - Limit results (default: 10)
- `--context-size N` - Characters around match (default: 500)

**Output:** JSON with `results` array

```json
{
  "results": [
    {
      "title": "Match title",
      "source_file": "path/to/book.epub",
      "text": "...matched text with context...",
      "score": 0.89
    }
  ]
}
```

**Empty results:** `{"results": []}`

---

## Indexing

**After adding new books:**
```bash
cd ~/Documents/librarian && \
python3 engine/scripts/index_library.py --smart
```

**`--smart`:** Only indexes new/modified files (fast)  
**`--force`:** Full rebuild (slow)

---

## Kavita integration

**Some books have Kavita links in metadata:**

```json
{
  "kavita_url": "http://192.168.1.152:5000/library/1/series/42"
}
```

**When presenting results:** Include link if available:
> **📖 Read in Kavita:** [Open book](http://192.168.1.152:5000/library/1/series/42)

---

## Troubleshooting

**"No module named 'sentence_transformers'"**
- Install: `pip install sentence-transformers torch faiss-cpu`

**"FAISS index not found"**
- Index missing. Run: `python3 engine/scripts/index_library.py --smart`

**Empty results (expected matches)**
- Check topic name (exact folder name)
- Try broader query
- Verify book is indexed: `ls books/{topic}/`

**Missing index for topic**
- Run reindex: `python3 engine/scripts/index_library.py --smart`

---

## Notes

- Queries support any characters (underscores, spaces, special chars)
- Quotes protect the query string
- Multi-topic search: `--topics chaos-magick,occult,finance`
- Use wrapper for enforcement (empty → "não achei")
- Direct research.py for advanced control (JSON output)

---
```

---

## What Changed

**Removed:**
- ❌ "ZERO TOLERANCE" warnings (8 instances)
- ❌ "MANDATORY CHECKLIST" (enforcement → script)
- ❌ "READ THIS FIRST" threats
- ❌ Protocol repetition (4 times)
- ❌ Response format template (script handles)

**Added:**
- ✅ Frontmatter metadata (emoji, deps, os)
- ✅ "When to use" triggers
- ✅ Quick start (wrapper first)
- ✅ Wrapper documentation
- ✅ Direct usage (advanced)
- ✅ Scannable format (headings, bullets)

**Kept:**
- ✅ Syntax examples
- ✅ Topic list
- ✅ Indexing instructions
- ✅ Troubleshooting
- ✅ Kavita integration

---

## Size Comparison

**Current SKILL.md:** ~8000 chars (verbose, enforcement-heavy)  
**Proposed SKILL.md:** ~3500 chars (dense, documentation-focused)

**Reduction:** 56% smaller, 100% more useful

---

## Questions for Nicholas

Before I replace SKILL.md:

1. **Wrapper prominence:** Should wrapper be "recommended" or "primary"?
2. **Direct usage:** Keep advanced section for research.py direct use?
3. **Triggers:** List in SKILL.md or just reference AGENTS.md?
4. **Metadata:** Add python deps to frontmatter now or later?
5. **Tone:** Too casual? Too technical? Just right?

---

## Next Steps (After Approval)

1. Replace `~/.openclaw/skills/librarian/SKILL.md` with new version
2. Test: Can I still understand how to use it?
3. Test: Does wrapper work as documented?
4. Commit both (SKILL.md + librarian.sh)
5. Archive old SKILL.md (git history)

---

**Ready to discuss.**
