# Embedding Model Evaluation Criteria

## Performance Metrics for RAG Systems

When choosing an embedding model for a local RAG system, evaluate across multiple dimensions:

---

## 1. Indexing Time

**What:** Time to generate embeddings for entire corpus during initial setup.

**Measured:** Seconds per book, total indexing time.

**Our benchmark (M3, 35 books, 11,764 chunks):**

- all-MiniLM-L6-v2: **78s total** (2.24s/book)
- all-mpnet-base-v2: ~150s estimated (4-5s/book)
- jina-embeddings-v2: ~180s estimated (5-6s/book)

**Impact:** Low. Indexing is one-time operation. Speed matters less than query latency.

---

## 2. Query Latency ⭐ (Most Important)

**What:** Time from question to retrieved chunks.

**Components:**

1. **Embedding generation** (question → vector)
2. **FAISS search** (vector → nearest neighbors)

**Our benchmark (query: "What are gradients..."):**

```
Total latency: 481.3ms
├─ Embedding: 477.0ms  (99%)
└─ Search: 4.3ms       (1%)
```

**Key insight:** Embedding dominates latency. FAISS is negligible.

**Comparison (estimated for same query):**

- all-MiniLM-L6-v2: ~480ms
- all-mpnet-base-v2: ~900ms (larger model = slower)
- jina-embeddings-v2: ~1000ms

**Why it matters:** User waits for every query. 500ms feels instant, 2s feels slow.

---

## 3. Retrieval Quality

**What:** Do the top-k chunks actually answer the question?

**Metrics:**

- **Relevance:** Are chunks semantically related?
- **Coverage:** Do we get different aspects/examples?
- **Precision:** Are irrelevant chunks filtered out?

**Example evaluation (Philosophy and Simulation query):**

| Rank | Chunk Content                      | Relevant?  | Notes                                         |
| ---- | ---------------------------------- | ---------- | --------------------------------------------- |
| 1    | "acids... protons"                 | ⚠️ Partial | About chemical gradients, not general concept |
| 2    | "problems for learning..."         | ❌ No      | Off-topic                                     |
| 3    | "gradient cancels itself"          | ✅ Yes     | Describes gradient dynamics                   |
| 4    | "gradient of electrical potential" | ✅ Yes     | Concrete example (neurons)                    |
| 5    | "trading... prices"                | ❌ No      | Economic context, not gradients               |

**Quality score:** 2/5 highly relevant, 1/5 partial = **40% precision**

**How to improve:**

- Use larger model (mpnet-768) for better semantic understanding
- Increase top-k to get more candidates
- Add reranking step

---

## 4. Filter Performance

**What:** Does quality change when filtering by book/topic vs. blind search?

**Test cases:**

### A) Filtered by book

```bash
query.py --book "philosophy" "What are gradients?"
```

- Search space: ~364 chunks (1 book)
- Expected: Higher precision (context-aware)

### B) Filtered by topic

```bash
query.py --topic "system-theory" "What are gradients?"
```

- Search space: ~364 chunks (1 book in this topic)
- Expected: Similar to book filter

### C) Blind search (no filter)

```bash
query.py "What are gradients?"
```

- Search space: 11,764 chunks (all books)
- Expected: Lower precision, may get irrelevant matches from other domains

**Hypothesis:** 384-dim models struggle with blind search across diverse topics.

---

## 5. Semantic Understanding

**What:** Can the model understand conceptual questions vs. keyword matching?

**Test:**

| Question Type   | Example                                 | Expected Behavior              |
| --------------- | --------------------------------------- | ------------------------------ |
| **Keyword**     | "Find mention of 'gradient'"            | Simple lexical match           |
| **Conceptual**  | "What are gradients?"                   | Understanding requires context |
| **Comparative** | "Gradient vs. slope?"                   | Needs relational understanding |
| **Abstract**    | "How do gradients relate to potential?" | Complex semantic inference     |

**Model comparison:**

- **MiniLM-384:** Good for keywords + simple concepts
- **MPNet-768:** Better for abstract/comparative queries
- **Specialized models:** Best for domain-specific (e.g., scientific papers)

---

## 6. Domain Adaptability

**What:** Does performance vary across different types of books?

**Categories in our library:**

| Domain                        | Books | Vocabulary            | Expected Difficulty |
| ----------------------------- | ----- | --------------------- | ------------------- |
| Fiction                       | 3     | Narrative, characters | Easy                |
| Philosophy                    | 2     | Abstract concepts     | Hard                |
| Technical (code/architecture) | 4     | Jargon, APIs          | Medium              |
| Oracles (I Ching, Tarot)      | 7     | Symbolic, esoteric    | Hard                |

**Hypothesis:** 384-dim models perform worse on philosophy/oracles due to abstract language.

---

## 7. Memory Footprint

**What:** RAM usage during query.

**Our setup:**

- Model in memory: ~200MB (MiniLM)
- FAISS index in memory: 17MB
- **Total: ~220MB**

**Comparison:**

- MPNet-768: ~500MB model + 34MB index = 534MB
- Jina-v2: ~600MB model + 34MB index = 634MB

**Impact:** On M3 with 16GB RAM, negligible. Matters for lower-end devices.

---

## Trade-offs Summary

| Criterion             | MiniLM-384 | MPNet-768  | Winner |
| --------------------- | ---------- | ---------- | ------ |
| **Indexing speed**    | 2.24s/book | ~4.5s/book | MiniLM |
| **Query latency**     | 480ms      | ~900ms     | MiniLM |
| **Retrieval quality** | Good       | Better     | MPNet  |
| **Memory**            | 220MB      | 534MB      | MiniLM |
| **Blind search**      | Struggles  | Better     | MPNet  |
| **Filtered search**   | Good       | Good       | Tie    |

---

## Decision Matrix

**Choose MiniLM-384 if:**

- ✅ Latency is critical (<500ms target)
- ✅ Most queries are filtered (by book/topic)
- ✅ Memory constrained (<1GB available)
- ✅ Books are relatively similar domain

**Choose MPNet-768 if:**

- ✅ Quality > speed
- ✅ Many blind searches across diverse topics
- ✅ Complex/abstract questions
- ✅ Willing to wait ~1s per query

---

## Next Steps for Evaluation

1. **Build test suite:**

   - 20 questions × 3 filter types (book/topic/blind)
   - Manual relevance scoring

2. **A/B test models:**

   - Reindex with MPNet-768
   - Compare precision@5 on test suite

3. **Measure real usage:**

   - Log queries and user satisfaction
   - Identify failure patterns

4. **Consider hybrid approach:**
   - MiniLM for fast first-pass
   - MPNet for reranking top-20 → top-5
