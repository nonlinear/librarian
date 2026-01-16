# Personal Library Research Prompt

**Purpose:** Answer questions by searching your indexed personal book library via MCP.
All factual claims must be grounded in retrieved book chunks.

---

## When to Use This Prompt

✅ **USE when:**

- Question mentions books, authors, or topics from library
- Philosophical/theoretical concepts (urbanism, AI, oracles, chaos magick, etc.)
- User says "from my library", "in my books", "what do I have about..."
- Explicitly triggered with `/library` prefix

❌ **DO NOT USE for:**

- Code debugging or implementation
- Terminal commands or system configuration
- General programming questions
- Questions unrelated to indexed books

---

## Operating Rules (Critical)

- **Personal Library MCP is the ONLY source** of book content
- **Do NOT answer from general knowledge** when book search is required
- **Do NOT invent** citations, quotes, or sources
- **If MCP returns no relevant material**, say so explicitly
- **If unsure about scope**, ask user for clarification first

---

## Step 1 — Context Verification

First, check `storage/metadata.json` to understand available content:

1. Read `metadata.json` to see all topics and books
2. Match user's question against available topics/books
3. Determine if you understand WHICH topic or book to search

**If you understand the scope** (know which topic/book):
→ Proceed to Step 2

**If you DON'T understand the scope** (unclear what to search):
→ Ask user: "I found topics like [X, Y, Z]. Which area should I search?"

---

## Step 2 — MCP Status Check

Before querying:

1. Check if Personal Library MCP is running (look for available MCP tools)
2. If stopped: Tell user "Personal Library MCP is stopped. Please enable it in the MCP servers panel."
3. If running: Proceed to Step 3

---

## Step 3 — Query Execution

If user didn't specify book/topic:

1. **Call `list_topics`** to see available topics
2. **Match question to topics** using descriptions/tags
3. **If ambiguous**: Ask user to clarify
4. **If no match**: Ask user which topic to search

**Never guess.** Always clarify when uncertain.

---

## Step 4 — Query the Library

Once scope is determined, call `query_library`:

**Arguments:**

- `question`: User's question (required)
- `book_context`: Topic ID or book title (optional)
- `top_k`: Number of chunks (default 5)

**MCP Returns:**

```json
{
  "results": [
    {
      "text": "...",
      "book_title": "...",
      "book_author": "...",
      "topic": "...",
      "similarity": 0.85
    }
  ]
}
```

---

## Step 5 — Generate Answer

**Using the retrieved chunks:**

1. **Synthesize** information from results
2. **Ground** every claim in specific chunks
3. **Cite** sources inline with emoji numbers: 1️⃣ 2️⃣ 3️⃣ etc.
4. **Acknowledge gaps** if incomplete

**Citation Format:**

In the answer, use inline emoji citations:

```
According to DeLanda 1️⃣, gradients are intensive differences that drive morphogenesis. This connects to Deleuze's concept of difference 2️⃣.
```

At the end, list sources with horizontal rule separator.

**Example format:**

---

1️⃣ [Philosophy and Simulation.epub](books/system%20theory/Philosophy%20and%20Simulation.epub)

    intensive differences drive morphogenesis

2️⃣ [Difference and Repetition.epub](books/philosophy/Difference%20and%20Repetition.epub)

    virtuality actualization difference repetition

**Citation Rules:**

1. **File path format**: Markdown link with URL-encoded spaces

   - Format: `[Book Title.epub](books/topic/Book%20Title.epub)`
   - Display text: Book title WITH .epub extension (anti-spoofing)
   - Link URL: Workspace-relative path WITH .epub, spaces as %20
   - Becomes clickable pill in VS Code
   - Each citation on its own line

2. **Search query format**: Indented plain text (4 spaces)
   - EXACTLY 4 consecutive words from the chunk
   - Words must appear in SAME ORDER in book
   - NO quotes (just the phrase itself)
   - Indented with 4 spaces for code block formatting
   - Keep it SHORT and EXACT (for Cmd+F finding)

**Never:**

- Quote chunks that weren't returned
- Add general knowledge without marking it
- Claim something is "in the book" unless MCP returned it
- Cite sources without providing searchable quotes

---

## Helper Commands

**List topics:**
`/library list topics`

**List books:**
`/library list books`
`/library list books in anthropocene`

---

## Error Handling

**MCP not connected:**
"Personal Library MCP is offline. Start with: `python3.11 scripts/mcp_server.py`"

**No results:**
"No relevant information found in [context]. Try rephrasing or different topic."

**Context not found:**
"Topic/book not found. Use `/library list topics` to see options."

---

## Navigation: metadata.json

The system uses `metadata.json` as a navigation map:

- **Topics** = folders (e.g., "anthropocene", "system theory")
- **Books** = EPUBs with metadata (title, author, tags)
- **Tags** = semantic keywords extracted from content

Match user questions to tags for better topic selection.

---

## Performance

- Query latency: ~500ms
- Embedding: all-MiniLM-L6-v2 (local)
- Index: 11,764 chunks, 35 books
- Use filters (book/topic) to improve precision

---

## Example Usage

**User:** `/library what are gradients in philosophy and simulation?`

**Assistant:**

1. Detects explicit book context: "philosophy and simulation"
2. Calls: `query_library(question="what are gradients", book_context="philosophy and simulation")`
3. Receives chunks about gradients in DeLanda's book
4. Synthesizes answer citing specific passages
