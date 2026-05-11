# Librarian: Semantic Book Search

Search 290+ indexed books using natural language queries.

**Architecture:** MCP Tool (`search_library`) → FAISS Search → Formatted Response

---

## Triggers

Activate when user asks:
- "pesquisa [QUERY]" / "search [QUERY]"
- "consult books about [TOPIC]"
- "What does [AUTHOR] say about [TOPIC]?"
- "Find references to [CONCEPT]"
- "O que [LIVRO] diz sobre [ASSUNTO]?"

---

## Call MCP Tool

```python
search_library(
    query: str,         # Natural language query
    k: int = 10,       # Number of results
    min_score: float   # Optional threshold (e.g., 0.7)
)
```

Returns chunks with:
- `text` - Full chunk content
- `book_title` - Book name
- `score` - Relevance (0-1)
- `source` - Chapter/page location

---

## Output Format (MANDATORY)

### Structure

1. **Synthesize answer** → Coherent paragraphs (not raw chunks)
2. **Inline emoji citations** → 1️⃣ 2️⃣ 3️⃣
3. **Blockquote sources** → With book/location
4. **Similarity stars** → ⭐⭐⭐⭐⭐ (0.9+), ⭐⭐⭐⭐ (0.8+), ⭐⭐⭐ (0.7+)

### Source Citations

**EPUB:** `Book Title, Chapter X (¶Y)`  
**PDF:** `Book Title, p.X`

### Example Output

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

## Critical Rules

✅ **Always synthesize** → Don't dump raw chunks  
✅ **Always cite** → Use 1️⃣2️⃣3️⃣ inline + blockquote sources  
✅ **Always star-rate** → Show relevance with ⭐  
✅ **Always hard-stop on failure** → No hallucination, no web fallback  

❌ **Never skip format** → MANDATORY structure  
❌ **Never show raw JSON** → User-friendly output only  
❌ **Never apologize for no results** → Just report state

---

**Index:** 290 EPUBs, 167,767 chunks  
**Search:** <1s latency (FAISS ANN)  
**Model:** BAAI/bge-small-en-v1.5 (384-dim)
