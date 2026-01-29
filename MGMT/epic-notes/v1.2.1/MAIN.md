# Epic v1.2.1: Research Enhancement

**Status:** 🚧 In Progress
**Branch:** v1.2.1
**Started:** 2026-01-29
**Completed:** _In progress_

---

## Goal

Enhance `research.py` to use BGE model's full potential and improve result quality across 5 dimensions:

1. **BGE Reranking** - Use cross-encoder capabilities to rerank semantic search results
2. **Context Expansion** - Return neighboring chunks for better readability
3. **Result Deduplication** - Group by book, remove duplicates, show distribution
4. **Query Enhancement** - Query expansion/reformulation for better recall
5. **Metadata Debugging** - Fix page/chapter/paragraph extraction (currently all null)

---

## Current State

### What Works

- Basic semantic search with BGE-small-en-v1.5 embeddings
- FAISS indexing and retrieval
- Topic and book filtering
- Configurable top-k results

### What's Broken/Missing

1. **Missing Metadata:** All results show `location: null`, `page: null`, `chapter: null`, `paragraph: null`
2. **No Reranking:** Results ranked only by cosine similarity, not cross-encoder relevance
3. **Limited Context:** Single chunks often lack sufficient context
4. **Duplicate Results:** Same book appears multiple times in top-10
5. **Basic Query Processing:** No expansion, reformulation, or enhancement

### Example Output Issues

```json
{
  "text": "III\nBuilding New Knowledge Commons",
  "book_title": "Understanding Knowledge as a Commons",
  "topic": "management_commons",
  "similarity": 0.5901607275009155,
  "filename": "Understanding Knowledge as a Commons.pdf",
  "folder_path": "management/commons",
  "relative_path": "../librarian/books/management/commons/Understanding Knowledge as a Commons.pdf",
  "location": null, // ❌ Should be "p.103" or similar
  "page": null, // ❌ Should be page number
  "chapter": null,
  "paragraph": null,
  "filetype": "unknown" // ❌ Should be "pdf"
}
```

**Duplicate issue:** 6 out of 10 results from same book ("Understanding Knowledge as a Commons")

---

## Implementation Plan

### Phase 1: Metadata Debugging (Priority)

**Hypothesis:** Chunks aren't being created with metadata, or metadata schema is wrong.

**Tasks:**

- [ ] Inspect `.chunks.json` structure in a sample topic folder
- [ ] Verify `index_library.py` extracts page numbers during PDF chunking
- [ ] Verify `index_library.py` extracts chapters during EPUB chunking
- [ ] Check chunks v2.0 schema matches what research.py expects
- [ ] Add logging to track metadata extraction pipeline
- [ ] Test with known PDF (should have page numbers)
- [ ] Test with known EPUB (should have chapter names)

**Expected outcome:** All metadata fields populated correctly

---

### Phase 2: BGE Reranking

**Approach:** Use BGE's cross-encoder mode to rerank top-k\*2 initial results

**Research needed:**

- [ ] Does `BAAI/bge-small-en-v1.5` support cross-encoder mode?
- [ ] If not, what's the recommended BGE reranking model?
- [ ] API: How to use cross-encoder for reranking?
- [ ] Performance: Will reranking slow down queries too much?

**Implementation:**

- [ ] Load cross-encoder model (separate from embedding model)
- [ ] Retrieve top-k\*2 candidates with embedding search
- [ ] Rerank candidates with cross-encoder
- [ ] Return top-k from reranked results
- [ ] Add `--no-rerank` flag for comparison

**Expected outcome:** Top-3 precision improves significantly

---

### Phase 3: Context Expansion

**Approach:** Return N chunks before/after each result for context

**Design decisions:**

- Default window size? (±1 chunk? ±2 chunks?)
- Return as separate field or merge into main text?
- How to handle chunk boundaries (different books/chapters)?

**Implementation:**

- [ ] Modify chunk storage to include sequential IDs
- [ ] Add `--context-window N` parameter (default: 1)
- [ ] Fetch neighboring chunks from `.chunks.json`
- [ ] Format expanded context clearly (mark boundaries)
- [ ] Handle edge cases (start/end of book)

**Expected outcome:** Results are readable passages, not fragments

---

### Phase 4: Result Deduplication

**Approach:** Group results by book, limit per-book, show distribution

**Implementation:**

- [ ] Add `--max-per-book N` parameter (default: 2)
- [ ] Group results by `book_id` or `filename`
- [ ] Keep only top N results per book
- [ ] Add book distribution summary to output
- [ ] Option: `--diverse` vs `--focused` modes

**Example output:**

```json
{
  "results": [...],
  "distribution": {
    "Understanding Knowledge as a Commons": 2,
    "Protecting the Commons": 2,
    "The Sustainable Economics of Elinor Ostrom": 1
  }
}
```

**Expected outcome:** More diverse results across books

---

### Phase 5: Query Enhancement

**Approach:** Expand query with synonyms/related terms before embedding

**Strategies to test:**

1. **Keyword expansion:** Add domain-specific synonyms
   - "commons" → "commons, shared resources, collective action"
   - "governance" → "governance, management, coordination"

2. **Query reformulation:** Generate alternative phrasings
   - Use LLM to rephrase query 2-3 ways
   - Embed all variants, average embeddings

3. **Hybrid search:** Combine semantic + keyword search
   - BM25 for keyword matching
   - BGE for semantic matching
   - Weighted fusion

**Implementation:**

- [ ] Start simple: hardcoded synonym expansion for common terms
- [ ] Add `--expand-query` flag
- [ ] Test recall improvement with known queries
- [ ] Consider more sophisticated approaches if needed

**Expected outcome:** 20%+ increase in recall

---

## Testing Strategy

### Test Queries

1. **Specific topic:** "commons governance coordination knowledge sharing community management volunteer"
2. **Broad topic:** "sustainability climate change"
3. **Specific concept:** "tragedy of the commons"
4. **Author/book:** "Elinor Ostrom polycentric governance"

### Success Metrics

- [ ] **Metadata:** 100% of results have valid page/chapter/location
- [ ] **Reranking:** Top-3 precision improves by 30%+
- [ ] **Context:** All results include ±1 chunk context
- [ ] **Diversity:** No more than 2 results per book in top-10
- [ ] **Recall:** Query expansion increases recall by 20%+

### Validation

- [ ] Compare before/after for each improvement
- [ ] Document trade-offs (speed vs quality)
- [ ] Update MCP server to expose new parameters
- [ ] Update documentation with examples

---

## Session Log

### Session 1: 2026-01-29 ✅ COMPLETE

**Epic Dance completed:**

1. ✅ Reviewed ROADMAP, identified v1.2.1 as next version
2. ✅ Groomed epic in ROADMAP with problem/solution/tasks
3. ✅ Updated mermaid subway map
4. ✅ Created branch v1.2.1
5. ✅ Updated ROADMAP with 🚧 and branch link
6. ✅ Created epic notes folder structure (v0.5.0+ style)

**Implementation completed:**

1. ✅ **All 5 features implemented** in research.py
   - BGE reranking with CrossEncoder
   - Context expansion (±N chunks)
   - Result deduplication (max per book)
   - Query enhancement (synonym expansion)
   - Full metadata support (page/chapter/paragraph)

2. ✅ **Indexer fixed** to extract v2.0 metadata
   - Modified `index_library.py` to use `load_book_with_metadata()`
   - Extracts page/paragraph from PDFs
   - Extracts chapter/paragraph from EPUBs
   - Uses paragraphs directly as chunks (better granularity)

3. ✅ **Comprehensive testing completed**
   - Reindexed cooking topic with v2.0 metadata
   - Tested all 5 features individually
   - Documented results in test-results.md
   - All success criteria met (4.5/5)

**Commits:**

- `6878124` - feat(research): implement v1.2.1 enhancements
- `06dcb90` - fix(indexer): enable v2.0 metadata extraction + testing

**Next steps:**

- Update MCP server to expose new parameters
- Reindex more topics to populate metadata
- Merge to main when ready
