# Epic: Remove Reranking from Research.py

**Created:** 2026-02-08  
**Status:** Planning  
**Priority:** High (blocking OOM fix)

---

## Context

**Problem:** `bge-reranker-base` (1.1 GB) causes OOM when indexing/researching.

**Root cause:** Reranking is unnecessary because:
- Librarian skill pre-filters queries (--topic, --book)
- Corpus already tiny (single topic/book)
- FAISS L2 distance sufficient for focused searches
- Reranking only helps with noisy/ambiguous results (we don't have that)

**Nicholas's insight:**
> "o librarian skill ja faz triagem... ele SO RODA research.py quando tem CERTEZA pra onde deve ir, pelo library-index (topics) e cada topic-index (livros). o -index age como subway map. nao TEM ambiguidade."

---

## Current State

**Files affected:**
- `engine/scripts/research.py` (has reranking code)
- `engine/models/models--BAAI--bge-reranker-base/` (1.1 GB, already deleted)

**What needs removal:**
1. Import: `CrossEncoder` from `sentence_transformers`
2. Function: `get_reranker()` (lazy loads reranker model)
3. Function: `rerank_results()` (reranks search results)
4. Parameter: `rerank: bool = True` (default flag)
5. Logic: All calls to reranking functions

---

## Plan

### Step 1: Sandbox Testing
- [ ] Copy `research.py` to `backstage/sandbox/research_no_rerank.py`
- [ ] Remove all reranking code (imports, functions, logic)
- [ ] Test with existing FAISS indexes (no need to reindex - same embeddings)
- [ ] Verify results quality (compare with/without reranking on sample queries)

### Step 2: Code Changes

**Remove these lines:**

```python
# Line 19
from sentence_transformers import SentenceTransformer, CrossEncoder  # Remove CrossEncoder

# Lines 41-49 (get_reranker function)
def get_reranker():
    """Lazy load reranker model"""
    global RERANKER_MODEL
    if RERANKER_MODEL is None:
        try:
            # BGE reranker models: bge-reranker-base, bge-reranker-large
            RERANKER_MODEL = CrossEncoder('BAAI/bge-reranker-base', max_length=512)
            print("✓ Loaded BGE reranker", file=sys.stderr)

# Lines 182-212 (rerank_results function)
def rerank_results(query: str, results: List[Tuple[int, float, Dict]]) -> List[Tuple[int, float, Dict]]:
    # ... entire function ...

# Line 245 (parameter)
rerank: bool = True,  # Remove parameter entirely

# Line 257 (docstring)
rerank: Use BGE reranker (default: True)  # Remove from docs

# Lines 300-305 (logic that calls reranking)
# Retrieve more candidates if reranking or deduplicating
if deduplicate:
    initial_k = k * 3
elif rerank:
    initial_k = k * 2
```

**Simplify to:**
```python
# Just use k directly, no inflation
initial_k = k
```

### Step 3: Testing Checklist

**Test cases:**
- [ ] Query with --topic only
- [ ] Query with --book only
- [ ] Query with --topic + --book
- [ ] Multi-result queries (k=5, k=10)
- [ ] Edge cases (no results, single result)

**Verify:**
- [ ] No errors/warnings about missing models
- [ ] Results still relevant (FAISS L2 distance works)
- [ ] Performance OK (no slower without reranking)
- [ ] Memory usage down (no 1.1 GB load)

### Step 4: Deployment

- [ ] Copy tested version from backstage to `engine/scripts/research.py`
- [ ] Commit with clear message: "refactor: remove reranking (unnecessary with pre-filtered queries)"
- [ ] Update ROADMAP.md (mark this epic complete)
- [ ] Test in production (real librarian queries)

---

## Success Criteria

✅ **research.py runs without errors**  
✅ **No reranker model loading attempts**  
✅ **Results quality same or better** (focused corpus = good L2 distance)  
✅ **Memory usage down ~1.1 GB**  
✅ **Indexing completes without OOM**

---

## Risks

⚠️ **Quality degradation?**  
- Mitigation: Test on sample queries, compare results before/after
- Fallback: Keep old version in backstage/archive/

⚠️ **Breaking existing workflows?**  
- Mitigation: Check if anything calls research.py with --rerank flag
- Unlikely: Librarian skill doesn't use --rerank

---

## Notes

- **No reindexing needed** - embeddings model (bge-small-en-v1.5) unchanged
- **Model already deleted** - can't accidentally use it
- **Architecture validated** - Nicholas confirmed subway map logic

---

**Next step:** Copy research.py to sandbox and start removing code.
