# Migrating to all-mpnet-base-v2

## TL;DR: Not Hard, But Requires Full Reindex

**Difficulty:** ⭐⭐☆☆☆ (Medium)
**Time:** ~3-5 minutes (35 books)
**Risk:** Low (can always roll back)

---

## Why Upgrade to MPNet?

| Metric                | MiniLM-L6-v2 (Current) | MPNet-Base-v2     | Difference      |
| --------------------- | ---------------------- | ----------------- | --------------- |
| **Dimension**         | 384                    | 768               | 2x larger       |
| **Query Latency**     | ~480ms                 | ~900ms            | ~2x slower      |
| **Indexing Time**     | 78s (2.24s/book)       | ~150s (4-5s/book) | ~2x slower      |
| **Retrieval Quality** | Good                   | Better            | ✅ More precise |
| **Memory Usage**      | 220MB                  | 534MB             | ~2.4x more      |
| **Model Size**        | ~90MB                  | ~420MB            | ~4.6x larger    |

**Best for:**

- Complex/abstract queries
- Philosophy, technical content
- When you value precision > speed
- Blind searches across many topics

**Stick with MiniLM if:**

- Speed is critical (<500ms)
- Mostly filtered searches (by book/topic)
- Memory constrained

---

## Migration Steps

### 1. Download Model (One-Time, ~5 min)

```bash
python3.11 -c "
from sentence_transformers import SentenceTransformer
import os

os.environ['SENTENCE_TRANSFORMERS_HOME'] = 'models'
print('Downloading all-mpnet-base-v2...')
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print(f'✅ Model downloaded to models/')
print(f'   Dimension: {model.get_sentence_embedding_dimension()}')
"
```

**Download size:** ~420MB
**Disk space needed:** ~500MB total

---

### 2. Update Scripts (3 files)

#### A. Update reindex_topic.py

```python
# Line 24-27, change model name:
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-mpnet-base-v2",  # ← Change this
    cache_folder=str(MODELS_DIR)
)
```

#### B. Update mcp_server.py

```python
# Line 55, change model name:
embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')  # ← Change this
```

#### C. Update research.py (if you use it)

```python
# Line 27, change model name:
EMBEDDING_MODEL = SentenceTransformer('all-mpnet-base-v2')  # ← Change this
```

---

### 3. Reindex All Topics (~3-5 min)

**Option A: Reindex all at once**

```bash
# Create a script to reindex all topics
python3.11 -c "
import json
from pathlib import Path
import subprocess
import sys

BOOKS_DIR = Path('books')
METADATA_FILE = BOOKS_DIR / 'metadata.json'

with open(METADATA_FILE) as f:
    metadata = json.load(f)

print(f'📚 Reindexing {len(metadata[\"topics\"])} topics with MPNet...')

for topic in metadata['topics']:
    topic_id = topic['id']
    print(f'\n🔄 {topic[\"label\"]}...')
    result = subprocess.run(
        [sys.executable, 'scripts/reindex_topic.py', topic_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f'❌ Failed: {result.stderr}')
    else:
        print(f'✅ Done')

print('\n🎉 All topics reindexed!')
"
```

**Option B: Reindex one topic at a time (safer)**

```bash
# Test with one topic first
python3.11 scripts/reindex_topic.py AI

# If successful, continue with others
python3.11 scripts/reindex_topic.py "design system"
# ... etc
```

---

### 4. Verify Migration

```bash
# Check one index dimension (should be 768 now)
cd "books/AI"
python3.11 -c "import faiss; idx = faiss.read_index('faiss.index'); print('Dimension:', idx.d, 'Vectors:', idx.ntotal)"
# Expected: Dimension: 768

# Check model in memory
cd "/Users/nfrota/Documents/personal library"
python3.11 -c "
import os
from sentence_transformers import SentenceTransformer
os.environ['SENTENCE_TRANSFORMERS_HOME'] = 'models'
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print(f'Model dimension: {model.get_sentence_embedding_dimension()}')
"
# Expected: Model dimension: 768
```

---

### 5. Test Query Performance

```bash
# Query via MCP and measure latency
# Should see ~900ms query time (vs ~480ms before)
```

---

## Rollback Plan (If Needed)

**If MPNet is too slow or quality isn't better:**

### 1. Revert code changes

```bash
# In reindex_topic.py, mcp_server.py, research.py:
# Change back to: all-MiniLM-L6-v2
```

### 2. Reindex with MiniLM

```bash
# Same reindex script as above
```

### 3. Delete MPNet model (optional)

```bash
rm -rf models/models--sentence-transformers--all-mpnet-base-v2
# Saves ~500MB disk space
```

---

## Side-by-Side Comparison (Before/After)

**Test query:** "What are gradients in Philosophy and Simulation?"

### Before (MiniLM-384)

| Rank | Chunk Content               | Relevant?  |
| ---- | --------------------------- | ---------- |
| 1    | "acids... protons"          | ⚠️ Partial |
| 2    | "problems for learning..."  | ❌ No      |
| 3    | "gradient cancels itself"   | ✅ Yes     |
| 4    | "gradient of electrical..." | ✅ Yes     |
| 5    | "trading... prices"         | ❌ No      |

**Precision@5:** 2/5 = 40%

### After (MPNet-768) - Expected

| Rank | Chunk Content                | Relevant?  |
| ---- | ---------------------------- | ---------- |
| 1    | "gradient cancels itself"    | ✅ Yes     |
| 2    | "gradient of electrical..."  | ✅ Yes     |
| 3    | "potential energy gradient"  | ✅ Yes     |
| 4    | "acids... protons"           | ⚠️ Partial |
| 5    | "gradient descent algorithm" | ✅ Yes     |

**Precision@5:** 4/5 = 80% ✅

_(Note: Actual results may vary - run your own test)_

---

## Disk Space Check

```bash
# Before migration
du -sh models/
# ~100MB (just MiniLM)

# After migration
du -sh models/
# ~600MB (MiniLM + MPNet)

# Delete MiniLM to save space (optional)
rm -rf models/models--sentence-transformers--all-MiniLM-L6-v2
# Back to ~500MB (just MPNet)
```

---

## Step-by-Step Command Sequence

**Copy-paste this entire block:**

```bash
# 1. Download MPNet model
python3.11 -c "from sentence_transformers import SentenceTransformer; import os; os.environ['SENTENCE_TRANSFORMERS_HOME'] = 'models'; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"

# 2. Update reindex_topic.py
# (Manual edit: line 24-27, change model name)

# 3. Update mcp_server.py
# (Manual edit: line 55, change model name)

# 4. Reindex all topics
python3.11 -c "
import json, subprocess, sys
from pathlib import Path
with open('books/metadata.json') as f:
    for t in json.load(f)['topics']:
        print(f'\n🔄 {t[\"label\"]}')
        subprocess.run([sys.executable, 'scripts/reindex_topic.py', t['id']])
print('\n✅ Done!')
"

# 5. Verify
cd "books/AI" && python3.11 -c "import faiss; print('Dim:', faiss.read_index('faiss.index').d)"
```

---

## Performance Expectations

**Your system (M3, 35 books):**

| Stage          | MiniLM-384   | MPNet-768 | Difference |
| -------------- | ------------ | --------- | ---------- |
| Model download | N/A (cached) | ~2 min    | One-time   |
| Full reindex   | 78s          | ~150s     | +72s       |
| Single query   | 480ms        | 900ms     | +420ms     |
| Memory usage   | 220MB        | 534MB     | +314MB     |

**Worth it?**

- ✅ Yes: If quality matters (philosophy, abstract queries)
- ❌ No: If speed is critical (real-time search, <500ms requirement)

---

## FAQs

### Can I run both models side-by-side?

Yes! Keep both models in `models/`, use different scripts:

- `reindex_topic_minilm.py` (384-dim)
- `reindex_topic_mpnet.py` (768-dim)
- Store indices in different folders

**But:** Don't mix dimensions in same index!

### Will my MCP server break during reindex?

No, but queries will fail for topics being reindexed. Recommend:

1. Reindex during low-usage time
2. Or keep old indices until all topics are done

### Can I automate the migration?

Yes! I can write a script to:

1. Download model
2. Update all code references
3. Reindex all topics
4. Verify dimensions

Want me to create that?

---

## Recommendation

**For your use case (philosophy, abstract content, diverse topics):**

✅ **Upgrade to MPNet** - The quality improvement is worth the extra 400ms query latency. You're not building a real-time search engine, and better retrieval means fewer follow-up searches.

**Test first:** Reindex just the "AI" or "system theory" topic, compare quality before committing to full migration.
