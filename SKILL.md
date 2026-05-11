---
title: "Librarian - Semantic Research Skill"
name: librarian
description: Conversational interface for semantic book search
version: 3.1.0
author: Nicholas Frota
homepage: https://github.com/nonlinear/librarian
requires:
  - librarian (parent project)
  - python3 (>=3.11)
dependencies:
  python:
    - sentence-transformers
    - torch
    - faiss-cpu
triggers:
  - "pesquisa"
  - "pesquisar"
  - "research"
  - "consult"
  - "Librarian"
  - "Consulte"
status: production
type:
  - research
  - MCP
---

# Librarian: Semantic Book Search

Search 290+ indexed books using natural language. Returns citations with chapter/page locations.

**Architecture:** Skill → MCP Tool (`search_library`) → FAISS Search

---

## Protocol Flow

### Query Flow (Question → Answer)

```mermaid
flowchart TB
 USER["🧑 User asks question"]:::user
 TRIGGER["🎯 Skill detects trigger"]:::skill
 MCP["🔌 Call MCP search_library"]:::mcp
 FAISS["🔍 FAISS searches 167K chunks"]:::search
 RESULTS{"📊 Results found?"}:::check
 
 SYNTHESIZE["✍️ Synthesize answer"]:::format
 CITATIONS["📎 Add emoji citations"]:::format
 SOURCES["📚 Format blockquote sources"]:::format
 
 NO_RESULTS["🤚 Hard stop: No results"]:::stop
 
 RESPONSE["💬 Librarian response"]:::output
 
 USER --> TRIGGER
 TRIGGER --> MCP
 MCP --> FAISS
 FAISS --> RESULTS
 
 RESULTS -->|Yes| SYNTHESIZE
 RESULTS -->|No| NO_RESULTS
 
 SYNTHESIZE --> CITATIONS
 CITATIONS --> SOURCES
 SOURCES --> RESPONSE
 
 NO_RESULTS --> RESPONSE
 
 classDef user fill:#e3f2fd,stroke:#2196f3,color:#1565c0
 classDef skill fill:#f3e5f5,stroke:#9c27b0,color:#6a1b9a
 classDef mcp fill:#fff3e0,stroke:#ff9800,color:#e65100
 classDef search fill:#e8f5e9,stroke:#4caf50,color:#2e7d32
 classDef check fill:#fff9c4,stroke:#fbc02d,color:#f57f17
 classDef format fill:#fce4ec,stroke:#e91e63,color:#c2185b
 classDef stop fill:#ffebee,stroke:#f44336,color:#c62828
 classDef output fill:#e0f2f1,stroke:#009688,color:#00695c
```

**Timing:** ~1-2s total (sub-second search + synthesis)

---

### Indexing Flow (New Book → Ready)

```mermaid
flowchart TB
 DROP["📥 Drop book in vault"]:::user
 WATCHER["👁️ Watcher detects file"]:::watcher
 WAIT["⏱️ 5s debounce"]:::watcher
 
 FINGERPRINT["🔍 Check fingerprint"]:::indexer
 CACHED{"📦 In cache?"}:::check
 
 EXTRACT["📖 Extract paragraphs"]:::indexer
 CHUNK["✂️ Chunk text (~1024 chars)"]:::indexer
 EMBED["🧮 Generate embeddings"]:::indexer
 
 APPEND["➕ Append to FAISS"]:::faiss
 STATE["💾 Update .index_state.json"]:::faiss
 
 RELOAD["🔄 MCP hot-reload (SIGHUP)"]:::mcp
 READY["✅ Ready to query"]:::ready
 
 SKIP["⚡ Skip (already indexed)"]:::skip
 
 DROP --> WATCHER
 WATCHER --> WAIT
 WAIT --> FINGERPRINT
 FINGERPRINT --> CACHED
 
 CACHED -->|No| EXTRACT
 CACHED -->|Yes| SKIP
 
 EXTRACT --> CHUNK
 CHUNK --> EMBED
 EMBED --> APPEND
 APPEND --> STATE
 STATE --> RELOAD
 RELOAD --> READY
 
 SKIP --> READY
 
 classDef user fill:#e3f2fd,stroke:#2196f3,color:#1565c0
 classDef watcher fill:#fff3e0,stroke:#ff9800,color:#e65100
 classDef check fill:#fff9c4,stroke:#fbc02d,color:#f57f17
 classDef indexer fill:#f3e5f5,stroke:#9c27b0,color:#6a1b9a
 classDef faiss fill:#e8f5e9,stroke:#4caf50,color:#2e7d32
 classDef mcp fill:#ffe0b2,stroke:#ff6f00,color:#e65100
 classDef ready fill:#c8e6c9,stroke:#81c784,color:#2e7d32
 classDef skip fill:#e0e0e0,stroke:#9e9e9e,color:#424242
```

**Timing:** 
- Cached (moved file): <1s
- New book: 5-10s (extract + embed + append)
- No restart needed ✅

---

## Trigger Detection

Activate when user query matches:

**Explicit:**
- "pesquisa [QUERY]" / "search [QUERY]"
- "consult books about [TOPIC]"
- "Librarian: [QUERY]"
- "Consulte livros sobre [CONCEPT]"

**Implicit:**
- "What does [AUTHOR] say about [TOPIC]?"
- "Find references to [CONCEPT]"
- "O que [LIVRO] diz sobre [ASSUNTO]?"

---

## Call MCP

```python
search_library(
    query: str,          # Natural language query
    k: int = 10,        # Number of results
    min_score: float    # Optional threshold (e.g., 0.7)
)
```

**Returns:**
```json
[
  {
    "text": "Full chunk text...",
    "book_title": "Design That Scales",
    "score": 0.812,
    "source": {
      "type": "epub",
      "spine_index": 11,
      "href": "xhtml/chapter1.xhtml",
      "paragraph_idx": 5
    }
  }
]
```

**Container:** `librarian` (always running on port 8088)

---

## Format Output

### Structure

1. **Synthesize answer** (coherent paragraphs, not just chunks)
2. **Inline emoji citations** (1️⃣ 2️⃣ 3️⃣)
3. **Blockquote sources** with locations
4. **Similarity stars** (⭐⭐⭐⭐⭐ 0.9+, ⭐⭐⭐⭐ 0.8+, ⭐⭐⭐ 0.7+)

### Source Format

**EPUB:** `Book Title, Chapter X (¶Y)`  
**PDF:** `Book Title, p.X`

### Example

**User:** "What does Graeber say about the origins of money?"

**Response:**

Graeber argues that money did NOT originate from barter. 1️⃣ Credit and debt systems came first — people tracked obligations before coins existed.

He traces debt to ancient Mesopotamia (~3500 BCE), where temple administrators recorded loans in cuneiform. 2️⃣ Coins appeared around 600 BCE in Lydia. 3️⃣

**Key insight:** Debt is older than money.

---

> **Fontes:**
>
> 1️⃣ Debt: The First 5000 Years (Graeber), p.21
>
> 2️⃣ Debt: The First 5000 Years (Graeber), p.40
>
> 3️⃣ Debt: The First 5000 Years (Graeber), p.89
>
> **Similarity:** ⭐⭐⭐⭐⭐ (0.95+ relevance)

**Note:** Reader not implemented (E036). Citations show location but aren't clickable.

---

## Hard Stops

When MCP fails, report exactly what happened:

- **No results** → "Não achei nada sobre [query]"
- **System error** → "Sistema quebrado"
- **MCP down** → "Serviço de busca indisponível"

**DO NOT:**
- ❌ Offer web search alternatives
- ❌ Hallucinate ("maybe the book says...")
- ❌ Apologize or frame as your failure

**Hard stop = success.** You detected system state and reported honestly.

---

## Troubleshooting

**No results but book exists:**
- Try broader terms
- Check if indexed (290 EPUBs, 303 PDFs pending)

**MCP not responding:**
```bash
docker ps | grep librarian
docker restart librarian
docker logs librarian --tail 50
```

---

## Technical Details

**Index:** 290 EPUBs, 167,767 chunks, 664MB  
**Search:** O(log n) ANN, <1s latency  
**Model:** BAAI/bge-small-en-v1.5 (384-dim)

**Files:**
- `/app/books/faiss.index` (245.8 MB)
- `/app/books/metadata.json` (418.0 MB)

---

## References

**Principle:**
```
SKILL = SOURCE OF TRUTH
Agent reads skill → follows instructions → accesses MCP
Never call MCP directly
```

**Related:**
- E027: Librarian MVP
- E034: Source Metadata
- E035: FAISS Migration

---

## Development History

```mermaid
flowchart TD
 V1["v1.0 Librarian Rebrand"]:::v1
 V2["v2.0 Topics Architecture"]:::v2
 V3["v3.0 Adaptive Clustering"]:::v3
 V4["v4.0 Folder-Agnostic"]:::v4
 V5["v5.0 Source Metadata"]:::v5
 V5_FAISS["v5.1 FAISS Migration"]:::v5
 V6["v6.0 Incremental Indexer"]:::v6
 
 V1 --> V2
 V2 --> V3
 V3 --> V4
 V4 --> V5
 V5 --> V5_FAISS
 V5_FAISS --> V6
 
 V1_DESC["Smart indexing + MCP"]
 V2_DESC["Protocol-driven, topic clustering"]
 V3_DESC["Entropy-based clustering, anti-drift"]
 V4_DESC["Content-hash identity, path-agnostic"]
 V5_DESC["EPUB paragraphs, PDF pages, CFI"]
 V5_FAISS_DESC["FAISS vector store, O(log n) search"]
 V6_DESC["Fingerprint cache, O(Δ) indexing"]
 
 V1 -.-> V1_DESC
 V2 -.-> V2_DESC
 V3 -.-> V3_DESC
 V4 -.-> V4_DESC
 V5 -.-> V5_DESC
 V5_FAISS -.-> V5_FAISS_DESC
 V6 -.-> V6_DESC
 
 classDef v1 fill:#e3f2fd,stroke:#2196f3
 classDef v2 fill:#f3e5f5,stroke:#9c27b0
 classDef v3 fill:#fff3e0,stroke:#ff9800
 classDef v4 fill:#e8f5e9,stroke:#4caf50
 classDef v5 fill:#fce4ec,stroke:#e91e63
 classDef v6 fill:#e0f2f1,stroke:#009688
```

**Key Evolution:**
- **v1-v2:** Topic-based semantic search
- **v3:** Attempted clustering (removed - premature structure)
- **v4:** Stable identity layer (move-safe)
- **v5:** Source metadata (chapter/page/¶)
- **v5.1:** FAISS production (69% size reduction)
- **v6:** Incremental indexing (epistemic anti-drift)

**Current State:** 290 EPUBs, 219K chunks, <1s search, <10s new book indexing

---

**Last updated:** 2026-05-06  
**Status:** ✅ Production (MCP v5 operational)
