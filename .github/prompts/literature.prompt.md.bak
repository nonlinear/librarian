# Literature Research

Purpose:
Answer questions by searching indexed books using RAG via MCP tools.
All factual claims must be grounded in book contents.

---

## Operating Rules (Critical)

- MCP is the only source of book content.
- Do NOT answer from general knowledge when book search is required.
- Do NOT invent citations, quotes, or sources.
- If MCP returns no relevant material, say so explicitly.

---

## Step 1 — Scope Detection (Reason First)

Before calling any MCP tool, silently determine scope:

1. Check whether the user explicitly specifies:

   - A folder (e.g. “from urbanism”, “use oracles”)
   - A book title
   - A clear domain constraint

2. If explicit scope is present:

   - Search ONLY within that folder or book.
   - Do NOT auto-detect topics.

3. If no scope is specified:
   - Treat the input as a general question.
   - Proceed to topic analysis.

---

## Step 2 — Topic Analysis (Only if No Scope)

If no folder or book was specified:

1. Read all `.rag-topics` files under:
   `~/Documents/literature/books/*/`

2. Match question keywords and concepts against topic lists.

3. Select only folders with clear semantic relevance.
   Avoid broad or speculative matches.

---

## Step 3 — RAG Consultation via MCP

- Use MCP tools to query the selected books or folders.
- Prefer precision over recall.
- Default to 3–5 sources unless otherwise requested.

You may pass the following arguments to MCP:

- `question`: main query string
- `book_context`: specific book or folder (if applicable)
- `auto_detect`: false if scope was explicitly provided
- `max_sources`: limit sources (default 3–5)
- `return_snippets`: include text excerpts when helpful
- `return_metadata`: include author/year if available

Example MCP request:

```json
{
  "method": "tools/call",
  "arguments": {
    "question": "What is legibility?",
    "book_context": "urbanism",
    "return_snippets": true,
    "return_metadata": true
  }
}
```
