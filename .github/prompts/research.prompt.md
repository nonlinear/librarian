# Personal Library Research Prompt

**Purpose:** Answer questions by searching your indexed personal book library.
All factual claims must be grounded in retrieved book chunks.

---

## Metadata Structure (Read This First!)

**Location:** `books/metadata.json` in the library

**Structure:**

```json
{
  "library_path": "/Users/nfrota/Documents/personal library",
  "topics": [
    {
      "id": "ai_theory",
      "label": "AI",
      "description": "...",
      "books": [{"id": "...", "title": "...", "author": "...", "tags": [...]}]
    }
  ]
}
```

**Key points:**

- `library_path` (string) → absolute path to library root
- `topics` (list) → array of topic objects
- Each topic has `id`, `label`, `description`, `books`

**Get library path (use this exact command):**

```bash
python3.11 -c "import json; print(json.load(open('books/metadata.json'))['library_path'])"
```

**List all topic IDs (use this exact command):**

```bash
python3.11 -c "import json; topics = json.load(open('books/metadata.json'))['topics']; print('\n'.join(t['id'] for t in topics))"
```

---

## When to Use This Prompt

✅ **USE when:**

- Question mentions books, authors, or topics from library
- Philosophical/theoretical concepts (urbanism, AI, oracles, chaos magick, etc.)
- User says "from my library", "in my books", "what do I have about..."
- Explicitly triggered with `/research` prefix

❌ **DO NOT USE for:**

- Code debugging or implementation
- Terminal commands or system configuration
- General programming questions
- Questions unrelated to indexed books

---

## Operating Rules (Critical)

- **research.py is the ONLY source** of book content
- **Do NOT answer from general knowledge** when book search is required
- **Do NOT invent** citations, quotes, or sources
- **If search returns no relevant material**, say so explicitly
- **If unsure about scope**, ask user for clarification first

---

## 🚨 CRITICAL: Library Validation (MUST RUN FIRST)

**Before answering ANY research question, verify library accessibility:**

**🚧 1 of 6: Check if metadata.json exists**

Execute this exact command:

```bash
test -f books/metadata.json && echo "LIBRARY_FOUND" || echo "LIBRARY_NOT_FOUND"
```

**Decision logic:**

- ✅ **Output = "LIBRARY_FOUND"**: Proceed to 🚧 2 of 6
- ❌ **Output = "LIBRARY_NOT_FOUND"**: STOP IMMEDIATELY

**If library not found, respond EXACTLY:**

```
❌ Personal Library not accessible in this workspace.

This prompt requires access to `books/metadata.json`.

Available options:
1. Switch to the Personal Library workspace
2. Ask your question without `/research` for general knowledge
3. Rephrase as a non-library question

I cannot answer research questions without library access.
```

**DO NOT:**

- Answer from general knowledge
- Provide architectural suggestions
- Give alternative solutions
- Continue with the research workflow

---

## Research Workflow (Follow in Order)

```mermaid
graph TD
    START([User asks /research question]) --> STEP1[🚧 1 of 6: Library Validation]
    STEP1 -->|Found| STEP2[🚧 2 of 6: Get Library Path]
    STEP1 -->|Not Found| STOP[❌ STOP - Refuse to answer]

    STEP2 --> STEP3[🚧 3 of 6: Check Topics & Match Query]
    STEP3 --> DECISION{Topic specified?}

    DECISION -->|Yes| STEP4[🚧 4 of 6: Execute Search]
    DECISION -->|No| INFER[Infer Topic from Metadata]

    INFER -->|Confident match| STEP4
    INFER -->|Unclear| ASK[Ask user to choose]
    ASK --> STEP4

    STEP4 --> STEP5[🚧 5 of 6: Parse JSON Results]
    STEP5 --> STEP6[🚧 Final: Format Answer with Citations]
    STEP6 --> END([Deliver grounded answer])
```

---

### 🚧 2 of 6: Get Library Path

**Get library path from metadata**

Execute this exact command:

```bash
python3.11 -c "import json; print(json.load(open('books/metadata.json'))['library_path'])"
```

Store result as `LIBRARY_PATH` variable.

---

### 🚧 3 of 6: Check Topics & Match Query

**List all topic IDs**

Execute this exact command:

```bash
python3.11 -c "import json; topics = json.load(open('books/metadata.json'))['topics']; print('\n'.join(t['id'] for t in topics))"
```

---

### 🚧 4 of 6: Execute Search

**If topic unclear, infer from metadata:**

- Read `books/metadata.json` for topic tags
- Match query keywords against topic IDs, book titles, tags
- Weighted scoring: tags 50%, topic ID 30%, labels 20%
- ✅ Confidence ≥ 60%: Auto-select topic
- ⚠️ Confidence < 60%: Ask user to clarify from top 3 candidates
- ❌ No matches: List all available topics

**Execute the search command (use LIBRARY_PATH from 🚧 2 of 6):**

```bash
python3.11 "{LIBRARY_PATH}/scripts/research.py" "{query}" --topic {topic_id} --top-k {k}
```

**Example:**

```bash
python3.11 "/Users/nfrota/Documents/personal library/scripts/research.py" "security risks in contact apps" --topic cybersecurity_applied --top-k 5
```

**Parameters:**

- `{query}`: User's question (required, in quotes)
- `{topic}`: Topic ID like `ai`, `anthropocene`, `cybersecurity_applied` (required)
- `{k}`: Number of results, default 5 (optional)

**How to execute (platform-specific):**

- **VS Code Copilot**: Use `run_in_terminal` tool
- **Claude Desktop**: Use MCP stdio server or shell tool
- **OpenAI API**: Use function calling with subprocess
- **Terminal-only**: User runs manually, pastes output

**Expected JSON response:**

```json
{
  "results": [
    {
      "text": "...chunk text...",
      "book_title": "Book Title",
      "topic": "topic_id",
      "similarity": 0.85
    }
  ]
}
```

**If execution fails:**

- Check if Python 3.11+ is installed
- Verify `library_path` from metadata.json exists
- Confirm `{library_path}/scripts/research.py` exists
- Confirm topic exists in `books/metadata.json`
- Ask user to run setup: `bash {library_path}/scripts/setup.sh`

---

### 🚧 5 of 6: Parse Results

**From the JSON response, extract:**

- `results[].text` - Book chunk content
- `results[].book_title` - Source book
- `results[].topic` - Topic ID
- `results[].similarity` - Relevance score

**Generate answer by:**

1. **Synthesize** information from results
2. **Ground** every claim in specific chunks
3. **Cite** sources inline with emoji numbers: 1️⃣ 2️⃣ 3️⃣ etc.
4. **Show topic** above citations
5. **Acknowledge gaps** if incomplete

**Example answer format:**

```
According to DeLanda 1️⃣, gradients drive morphogenesis. This connects to Deleuze's concept 2️⃣.

**Topic:** anthropocene

---

1️⃣ [Molecular Red.epub](../personal%20library/books/anthropocene/Molecular%20Red.epub)

    gradients drive morphogenesis matter

2️⃣ [A Thousand Plateaus.epub](../personal%20library/books/anthropocene/A%20Thousand%20Plateaus.epub)

    intensive differences create forms
```

---

### 🚧 Final: Citation Format (CRITICAL)

- **MUST get exact filename from `metadata.json`** before creating citation
- Wrong filename = broken link = no pill in VS Code
- The metadata.json MUST contain exact filenames or absolute paths

**Path calculation:**

- VS Code's link pill validation is VERY strict to prevent spoofing
- **Step 1:** Read `metadata.json` (from MCP server) to get:
  1.  Exact `filename` for each book (e.g., `"Debt - David Graeber.epub"`)
  2.  `library_path` field (e.g., `"/Users/nfrota/Documents/personal library"`)
  3.  Topic folder name (e.g., `"system_theory"`)
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

## Step 5 — Citation Format (CRITICAL)

**File path format**: Markdown link with URL-encoded spaces

- Format: `[Book Title.epub](../personal%20library/books/topic/Book%20Title.epub)`
- Display text: Book title WITH .epub extension
- Link URL: Workspace-relative path WITH .epub
- **MUST use URL encoding**: spaces as `%20`, `:` as `%3A`, `'` as `%27`, etc.

**Search snippet format**: Indented plain text (4 spaces)

- EXACTLY 4 consecutive words from chunk
- Words in SAME ORDER as in book
- NO quotes (just the phrase itself)
- For Cmd+F finding in VS Code

**Path calculation:**

1. Read `books/metadata.json` to get:
   - Exact `filename` for the book
   - `folder_path` from the topic entry (e.g., `"AI/theory"` or `"product architecture"`)
2. Construct full path: `books/{folder_path}/{filename}`
3. Calculate relative path from current workspace to library
4. URL-encode spaces and special characters (`%20`, `%3A`, `%27`, etc.)

**Example:**

- Topic ID: `ai_theory`
- Folder path from metadata: `"AI/theory"`
- Filename: `"Superintelligence.epub"`
- Result: `../personal%20library/books/AI/theory/Superintelligence.epub`

**Never:**

- Quote chunks that weren't returned
- Add general knowledge without marking it
- Claim something is "in the book" unless search returned it
- Cite sources without providing searchable snippets

---

## Helper Commands

**Get library path:**

```bash
python3.11 -c "import json; print(json.load(open('books/metadata.json'))['library_path'])"
```

**List all topic IDs:**

```bash
python3.11 -c "import json; topics = json.load(open('books/metadata.json'))['topics']; print('\n'.join(t['id'] for t in topics))"
```

**List books in specific topic:**

```bash
python3.11 -c "import json; topics = json.load(open('books/metadata.json'))['topics']; topic = next(t for t in topics if t['id'] == '{topic_id}'); print('\n'.join(b['title'] for b in topic['books']))"
```

(Replace `{topic_id}` with actual topic ID like `anthropocene`)

---

## Error Messages

**Scope not specified:**
"Your library has topics: [list top 5-7 topics]. Which area should I search?"

**Ambiguous scope:**
"I found multiple cybersecurity topics: applied, history, strategy. Which one?"

**Execution failed:**
"Could not execute research.py. Verify Python 3.11+ is installed and run `bash ./scripts/setup.sh`"

**No results:**
"No relevant information in `{topic}`. Try different topic or rephrase."

**Topic not found:**
"Topic '{topic}' not in library. Available: [list topics]."

---

## Performance Notes

- Query latency: ~500ms (local embedding model)
- Embedding: all-MiniLM-L6-v2 (90MB, local)
- Topic inference confidence threshold: 60%

---

## Example Usage

**User:** `/research what does Bogdanov say about Mars in Molecular Red?`

**AI workflow:**

1. Reads metadata → gets `library_path = "/Users/nfrota/Documents/personal library"`
2. Finds "Molecular Red" in `anthropocene` topic
3. Executes: `python3.11 /Users/nfrota/Documents/personal\ library/scripts/research.py "what does Bogdanov say about Mars" --topic anthropocene --top-k 5`
4. Parses JSON response
5. Synthesizes answer with citations

**Response:**

Bogdanov envisioned Mars as a socialist utopia 1️⃣ where collective labor transforms planetary conditions 2️⃣.

**Topic:** anthropocene

---

1️⃣ [Molecular Red.epub](../personal%20library/books/anthropocene/Molecular%20Red.epub)

    Mars socialist utopia collective

2️⃣ [Molecular Red.epub](../personal%20library/books/anthropocene/Molecular%20Red.epub)

    labor transforms planetary conditions

---

**User:** `/research in tarot what spreads work for decision-making?`

**AI workflow:**

1. Reads metadata → gets `library_path`
2. Executes: `python3.11 {library_path}/scripts/research.py "spreads for decision-making" --topic tarot --top-k 5`
3. Parses results
4. Formats answer with citations

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
