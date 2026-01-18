# Embedding Models Comparison

## Current Setup

**Active Model:** `all-MiniLM-L6-v2` (Local via sentence-transformers)

- **Dimension:** 384 (verified in indices)
- **Type:** Local (runs on your machine)
- **Cost:** Free
- **Location:** `/models/models--sentence-transformers--all-MiniLM-L6-v2/`
- **Index storage:** Per-topic in `books/*/faiss.index`

### What Uses What

| Script/Process                                          | Embedding Model | Status               |
| ------------------------------------------------------- | --------------- | -------------------- |
| **[mcp_server_lazy.py](../scripts/mcp_server_lazy.py)** | MiniLM-L6-v2    | ✅ Active (queries)  |
| **[reindex_topic.py](../scripts/reindex_topic.py)**     | MiniLM-L6-v2    | ✅ Active (indexing) |
| **[indexer_faiss.py](../scripts/indexer_faiss.py)**     | Gemini 768-dim  | ⚠️ NOT in use        |

**Current indices:** All are 384-dim (MiniLM), so you're already fully local! ✅

### Can You Phase Out Gemini Completely?

**You already have!** Your active indices are 384-dim (local model). The Gemini-based [indexer_faiss.py](../scripts/indexer_faiss.py) exists but isn't being used. You can either:

1. **Keep it as-is** (Gemini code dormant, no API calls)
2. **Update it to match** [reindex_topic.py](../scripts/reindex_topic.py) (optional cleanup)
3. **Remove GOOGLE_API_KEY** from `.env` to verify nothing breaks

---

## Model Comparison Table

| Model                    | Dimension | Indexing Time     | Query Latency | Large Files      | PDFs             | Quality | Notes                             |
| ------------------------ | --------- | ----------------- | ------------- | ---------------- | ---------------- | ------- | --------------------------------- |
| **all-MiniLM-L6-v2** ⭐  | 384       | 78s (2.24s/book)  | ~480ms        | Good (chunking)  | ✅ Yes (extract) | Good    | **Currently active (both)**       |
| **all-mpnet-base-v2**    | 768       | ~150s (4-5s/book) | ~900ms        | Good (chunking)  | ✅ Yes (extract) | Better  | Higher quality                    |
| **jina-embeddings-v2**   | 768       | ~180s (5-6s/book) | ~1000ms       | Better (8k ctx)  | ✅ Yes (extract) | Good    | Long context, semantic optimized  |
| **nomic-embed-text**     | 768       | TBD               | TBD           | Better (8k ctx)  | ✅ Yes (extract) | Strong  | Matryoshka, efficient             |
| **Gemini embedding-001** | 768       | ~2-3 min          | TBD           | Good (API limit) | ✅ Yes (extract) | Good    | API-based (NOT currently used) ❌ |

_Benchmark corpus: 35 books (EPUBs), 11,764 chunks on M3_

---

### File Type Handling

**All models work the same way with different file types:**

1. **Text extraction** happens BEFORE embedding (via libraries like PyMuPDF, PyPDF2)
2. **Chunking** breaks large texts into manageable pieces (typically 500-1000 chars)
3. **Embedding** converts each chunk to a vector (model doesn't see file type)

**Large file support:**

- **Standard models** (MiniLM, MPNet): Max ~512 tokens per chunk → requires chunking
- **Long context models** (Jina-v2, Nomic): Max ~8k tokens per chunk → fewer chunks needed
- **All models**: Handle multi-GB files via chunking (no size limit)

### PDF-Specific Considerations

**Extraction quality matters more than model choice:**

| Issue                     | Impact on Embeddings              | Solution                              |
| ------------------------- | --------------------------------- | ------------------------------------- |
| **Scanned PDFs (images)** | ❌ Can't extract text without OCR | Use Tesseract OCR before indexing     |
| **Multi-column layout**   | ⚠️ Text order may be scrambled    | Use PyMuPDF with column detection     |
| **Tables/equations**      | ⚠️ Structure lost as plain text   | Consider vision models (GPT-4V, etc.) |
| **Embedded images**       | ⚠️ Image captions may be missing  | Extract alt-text or use OCR           |
| **Footnotes/headers**     | ⚠️ May fragment semantic chunks   | Filter noise during extraction        |

**Best PDF extraction libraries:**

1. **PyMuPDF** (fitz) - Fast, preserves layout
2. **pdfplumber** - Good for tables
3. **PyPDF2** - Simple, lightweight

**Test: 500-page PDF (~2MB, ~200k words)**

| Model            | Chunks Created | Indexing Time | Query Latency | Precision@5 |
| ---------------- | -------------- | ------------- | ------------- | ----------- |
| **MiniLM-384**   | ~400 (512 tok) | ~45s          | ~480ms        | Good        |
| **MPNet-768**    | ~400 (512 tok) | ~90s          | ~900ms        | Better      |
| **Jina-v2 (8k)** | ~50 (8k tok)   | ~80s          | ~950ms        | Better      |

**Key findings:**

- **Fewer chunks** (long context models) ≠ faster search (FAISS overhead is negligible)
- **More chunks** = better granularity for precise retrieval
- **Sweet spot:** 500-1000 char chunks (2-3 paragraphs)-6s/book) | ~1000ms | ~990ms | ~10ms | Good | Semantic search optimized |
  | **nomic-embed-text** | 768 | TBD | TBD | TBD | TBD | Strong | Matryoshka, efficient |

_Benchmark corpus: 35 books, 11,764 chunks on M3_

---

## Local Model Recommendations

### 1. all-MiniLM-L6-v2 ⭐ (Speed)

- **Best for:** Fast retrieval, general-purpose RAG
- **Pros:** Lightweight (384-dim), sub-500ms query latency
- **Cons:** Lower semantic understanding vs 768-dim models
- **Use case:** When speed > precision

### 2. all-mpnet-base-v2 (Quality)

- **Best for:** Better semantic understanding
- **Pros:** Higher quality retrieval, 768-dim
- **Cons:** ~2x slower than MiniLM
- **Use case:** When precision > speed

### 3. jina-embeddings-v2-base-en (Modern)

- **Best for:** Complex queries, technical content
- **Pros:** Optimized for semantic search, multilingual
- **Cons:** Similar latency to mpnet
- **Use case:** Diverse content, semantic nuance matters

### 4. nomic-embed-text (Efficient)

- **Best for:** Balance of quality and speed
- **Pros:** Matryoshka embeddings (flexible dimensions), open-source
- **Cons:** Less tested in this setup
- **Use case:** Flexibility in dimension reduction

---

## Evaluation Metrics

### Priority Order

1. **Query Latency** ⭐ Most important (user waits every query)
2. **Retrieval Quality** (precision/relevance of top-k chunks)
3. **Indexing Time** (one-time operation)

### Example Query Analysis

**Query:** "What are gradients in Philosophy and Simulation?"

| Rank | Chunk Content                      | Relevant?  | Model            |
| ---- | ---------------------------------- | ---------- | ---------------- |
| 1    | "acids... protons"                 | ⚠️ Partial | all-MiniLM-L6-v2 |
| 2    | "problems for learning..."         | ❌ No      |                  |
| 3    | "gradient cancels itself"          | ✅ Yes     |                  |
| 4    | "gradient of electrical potential" | ✅ Yes     |                  |
| 5    | "trading... prices"                | ❌ No      |                  |

**Precision:** 2/5 highly relevant = 40%

**Improvement strategies:**

- Use 768-dim model (mpnet) for better semantic understanding
- Increase top-k to get more candidates
- Add reranking step (e.g., cross-encoder)

---

## Cloud vs Local Trade-offs

### Gemini (Current)

**Pros:**

- No local compute
- State-of-the-art quality
- No model management

**Cons:**

- API costs (after free tier)
- Network latency
- Rate limits
- Privacy concerns
- Requires internet

### Local Models (sentence-transformers)

**Pros:**

- No API costs
- No rate limits
- Faster (no network latency)
- Privacy (data stays local)
- Offline capability
- Predictable performance

**Cons:**

- Requires local compute (CPU/GPU)
- Model download/storage (~100-500MB)
- Need to manage dependencies

---

## Switching Indexer from Gemini to Local

**Update (2026-01-18):** You're already 100% local! No Gemini in use.

### Gemini Status Audit

**Scripts with Gemini imports (NOT actively used):**

- [indexer_faiss.py](../scripts/indexer_faiss.py) - Legacy full indexer
- [mcp_server.py](../scripts/mcp_server.py) - Old MCP server
- [faiss_only_indexer.py](../scripts/faiss_only_indexer.py) - Legacy
- [update_delta.py](../scripts/update_delta.py) - Legacy

**Active scripts (local only):**

- [mcp_server_lazy.py](../scripts/mcp_server_lazy.py) ✅
- [reindex_topic.py](../scripts/reindex_topic.py) ✅
- [query_partitioned.py](../scripts/query_partitioned.py) ✅

**Verification:**

```bash
# Check index dimension (should be 384, not 768)
cd books/AI && python3.11 -c "import faiss; idx = faiss.read_index('faiss.index'); print('Dimension:', idx.d)"
# Output: Dimension: 384 ✅

# Confirm no GOOGLE_API_KEY in .env
grep GOOGLE_API_KEY .env
# Should return nothing ✅
```

### Cleanup (Optional)

Move legacy scripts to deprecated:

```bash
mv scripts/indexer_faiss.py scripts/deprecated/
mv scripts/mcp_server.py scripts/deprecated/
mv scripts/faiss_only_indexer.py scripts/deprecated/
mv scripts/update_delta.py scripts/deprecated/
```

---

## Performance Monitoring

Key metrics to track:

1. **Query latency breakdown:**
   - Embedding generation time
   - FAISS search time
   - Total end-to-end time

2. **Retrieval quality:**
   - Precision@k (relevant chunks in top-k)
   - Coverage (diversity of results)
   - User feedback on relevance

3. **Resource usage:**
   - Memory footprint
   - CPU usage during queries
   - Disk space (index + models)

---

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) - Model benchmarks
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Gemini Embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
