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

## Step 3 — Query Execution (SMART INFERENCE)

**System infers topic from query using:**
1. **Colloquial phrasing** (high confidence)
   - "applied cybersecurity" → `cybersecurity/applied`
   - "cybersecurity history" → `cybersecurity/history`
   - "history of AI" → `ai/history` (if exists)

2. **Tag matching** (calculated confidence)
   - Query: "cryptography best practices"
   - Tags: `cybersecurity_applied` has "cryptography-contents"
   - Confidence: High → Auto-select

3. **Keyword overlap** (weighted scoring)
   - Topic ID words: 30% weight
   - Tag matches: 50% weight
   - Label matches: 20% weight

**Decision logic:**
- ✅ **Confidence ≥ 60%**: Make the bet, proceed with query
- ⚠️ **Confidence < 60%**: Ask user to clarify from top 3 candidates
- ❌ **No matches**: List all available topics

**If user specified topic explicitly:**
- Use it directly (skip inference)

**If inference succeeds:**
- `query`: User's question (required)
- `topic`: Topic ID (optional - system infers if not provided)
- `book`: Book title filter (optional)
- `k`: Number of chunks (default 5)

**System behavior:**
- If `topic` provided: Use it directly
- If not: Call internal `infer_topic_from_query()`
  - Returns: `{topic_id, confidence, candidates, reasoning}`
  - High confidence: Proceed automatically
  - Low confidence: Ask user to pick from candidatests
- ❌ **No scope** = Never allowed
- 💡 **Multiple topics?** User creates aggregated topic

---

## Step 4 — Query the Library (SCOPED)

Once scope is determined, call `query_library`:

**Arguments:**

- `query`: User's question (required)
- `topic`: Topic ID (e.g., "cybersecurity_applied", "anthropocene") - **REQUIRED**
- `book`: Book title filter (optional, further narrows within topic)
- `k`: Number of chunks (default 5)

**Topic ID format:**
- Display to user with `/`: `ai`, `anthropocene`, `cybersecurity/applied`
- Internal IDs use `_`: `cybersecurity_applied` (MCP handles conversion)
- Check `list_topics` output for hierarchical display

**MCP Returns:**

```json
{
  "results": [
    {
      "text": "...",
      "book_title": "...",
      "topic": "...",
      "topic_path": "cybersecurity/applied",
      "score": 0.85
    }
  ],
  "topic_searched": "cybersecurity/applied",
  "related_topics": ["cybersecurity/history", "cryptography/basics"]
}
```

---

## Step 5 — Generate Answer

**Using the retrieved chunks:**

1. **Synthesize** information from results
2. **Ground** every claim in specific chunks
3. **Cite** sources inline with emoji numbers: 1️⃣ 2️⃣ 3️⃣ etc.
4. **Show topic path** above citations
5. **Suggest related topics** at the end
6. **Acknowledge gaps** if incomplete, then list sources with topic path header:

```
According to DeLanda 1️⃣, gradients drive morphogenesis. This connects to Deleuze 2️⃣.

**Topic:** cybersecurity/applied

---

1️⃣ [Applied Cryptography.epub](../personal%20library/books/cybersecurity/applied/Applied%20Cryptography.epub)

    cryptography today encyclopedic readable

2️⃣ [Hacking The Art of Exploitation.epub](../personal%20library/books/cybersecurity/applied/Hacking%20The%20Art%20of%20Exploitation.epub)

    programming assembly language exploit

---

**💡 Related topics you might want to explore:**
- `cybersecurity/history` - Historical security breaches
- `cybersecurity/strategy` - Risk management frameworks
```

**Always include "Related topics" section** if MCP returns them.

**Citation Rules:**

1. **File path format**: Markdown link with URL-encoded spaces
   - Format: `[Book Title.epub](../personal%20library/books/topic/Book%20Title.epub)`
   - Display text: Book title WITH .epub extension (anti-spoofing)
   - Link URL: Workspace-relative path WITH .epub
   - **MUST use URL encoding**: spaces as `%20`, `:` as `%3A`, `'` as `%27`, etc.
   - Becomes clickable pill in VS Code
   - Each citation on its own line

   **CRITICAL: Book Title vs Filename:**
   - MCP returns `book_title` from metadata (can be fancy/long)
   - **Actual filename may differ** (e.g., "Debt - David Graeber.epub")
   - **MUST get exact filename from `metadata.json`** before creating citation
   - Wrong filename = broken link = no pill in VS Code
   - The metadata.json MUST contain exact filenames or absolute paths

   **Path calculation:**
   - VS Code's link pill validation is VERY strict to prevent spoofing
   - **Step 1:** Read `metadata.json` (from MCP server) to get:
     1. Exact `filename` for each book (e.g., `"Debt - David Graeber.epub"`)
     2. `library_path` field (e.g., `"/Users/nfrota/Documents/personal library"`)
     3. Topic folder name (e.g., `"system_theory"`)
   - **Step 2:** Get current workspace path (e.g., `/Users/nfrota/Documents/nonlinear`)
   - **Step 3:** Calculate relative path from workspace to library:
     - If both in same parent: `../personal%20library/books/topic/filename.epub`
     - Use Python `os.path.relpath(library_path, workspace_path)` logic if needed
   - **Step 4:** Construct final link with URL encoding
   - **For nonlinear workspace:** Result is `../personal%20library/books/topic/exact-filename.epub`

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

- `cybersecurity/applied` - Cryptography, exploits
- `cybersecurity/history` - Security breaches
- `cybersecurity/strategy` - Risk management

Which area should I search
---

## Helper Commands

**List topics:**
`/research list topics`

**List books:**
`/research list books`
`/research list books in anthropocene`

---

##Scope not specified:**
"Your library has topics: [list top 5-7 topics]. Which area should I search?"

**Ambiguous scope:**
"I found multiple cybersecurity topics: applied, history, strategy. Which one?"

**MCP not connected:**
"Personal Library MCP is offline. Enable it in MCP servers panel."

**No results:**
"No relevant information in `{topic}`. Try different topic or rephrase."

**Topic not found:**
"Topic '{topic}' not in library. Available: [list topics]."

---

## Navigation: metadata.json

The system uses `metadata.json` as a navigation map:

- **Topics** = folders (e.g., "anthropocene", "cybersecurity/applied")
- **Books** = EPUBs with metadata (title, author, tags)
- **Tags** = semantic keywords for smart matching

---

## Performance

- Query latency: ~500ms
- Embedding: all-MiniLM-L6-v2 (local)
- Index: 11,764 chunks, 35 books
- Inference confidence threshold: 60%

---

## Example Usage

**User:** `/research cryptography best practices`

**Assistant (high confidence - auto-selects):**

Searched `cybersecurity/applied` (matched: cryptography, exploits)

[... answer with citations ...]

**Topic:** cybersecurity/applied

---

💡 Related topics:
- `cybersecurity/history`
- `information_theory`

---

**User:** `/research applied cybersecurity`

**Assistant (colloquial match - instant):**

[Proceeds immediately, no confirmation needed]

**Topic:** cybersecurity/applied

---

**User:** `/research security stuff`

**Assistant (low confidence - asks):**

"I'm not sure which topic. Choose from:
1. `cybersecurity/applied` (40%)
2. `cybersecurity/history` (35%)
3. `information_theory` (25%)"
