# Literature Research

**Purpose:** Search indexed books using RAG to answer questions based on book contents.

---

## Instructions for AI

When this prompt is activated:

1. **Check if user specified a folder:**

   - Look for patterns like: "use oracles:", "from AI folder:", "search in urbanism:"
   - If folder specified, search ONLY in that folder
   - Check `~/Documents/literature/books/` for available folders

2. **If NO folder specified, analyze the question** to identify relevant topics:

   - Read all `.rag-topics` files in `~/Documents/literature/books/*/`
   - Match question keywords against topics in each folder
   - Identify which folders contain relevant books

3. **Consult the RAG system:**

   - Use the MCP literature tools to query relevant books
   - Focus on the specified folder OR folders whose topics match the question
   - Retrieve relevant passages and citations

4. **Provide answer with sources:**

   - When mentioning an answer that has a source, add a superscript reference at the end of the sentence or term, like ^1, ^2, ^3.
   - At the end, list sources in this format (ensure links use markdown syntax and are not inside code blocks):

📚 Sources:

- 1️⃣ [Book Name](/Users/nfrota/Documents/literature/books/folder/book.epub): "some 30-character string from the book so you can find it"
- 2️⃣ [Another Book](/Users/nfrota/Documents/literature/books/folder/book.epub): "another 30-character string from the book"

5. **If no relevant books found:**

- Explain which topics you searched
- List available folders and their topics
- Suggest how to rephrase the question

## Advanced MCP Arguments

You can use these arguments in your MCP JSON requests for more control:

- `question`: The main query string.
- `book_context`: (optional) Specify a book or folder for focused search.
- `auto_detect`: (optional, default true) Set to false to disable topic auto-detection.
- `max_sources`: (optional) Limit the number of sources returned (e.g., 5).
- `return_snippets`: (optional) If true, include text snippets from sources.
- `return_metadata`: (optional) If true, include extra metadata (author, year, etc.).

**Example MCP JSON request:**

```json
{
  "method": "tools/call",
    "arguments": {
      "return_snippets": true,
      "return_metadata": true

---

## Available Topics

Current indexed folders and keywords:

- **AI:** ethics, UX, machine learning, algorithmic bias, software design
- **anthropocene:** ecology, forests, indigenous knowledge, climate
- **art direction:** generative design, creative coding, Processing
- **fiction:** sci-fi narratives (limited support)
- **oracles:** I Ching, hexagrams, divination
- **system theory:** complexity, emergence, gradients, simulation
- **urbanism:** legibility, state power, planning, high modernism
- **usability:** content strategy, validation, writing, UX

---
## Debug Commands

# View keywords for a folder
cat ~/Documents/literature/books/AI/.rag-topics
```

---

## Tips

**To ensure RAG activates:**

- Mention topics explicitly (e.g., "according to I Ching")
- Ask conceptual questions rather than generic ones
- "What is legibility?" → urbanism/
**Examples that might NOT trigger:**
- "How are you today?" (social, not knowledge-based)
