# Personal Library MCP

**Local, offline-first RAG system for personal book libraries**

A semantic navigation system for EPUB/PDF collections. Designed for speed, control, and zero cloud dependencies.

---

## Core Principles

**Every millisecond matters.**

This system is a **semantic orientation tool**, not a conversational assistant.

- **Map ≠ Territory**: Uses a single metadata file for navigation, not content replication
- **Explicit invocation only**: No automatic exploration or unsolicited responses
- **Delta indexing**: Only reindexes what changed
- **Client-agnostic backend**: VS Code is just one possible interface

---

## Architecture

### Vault Structure

```
books/
├── topic_a/
│   ├── book1.epub
│   └── book2.pdf
├── topic_b/
│   └── book3.epub
```

**Rules:**

- Exactly 1 folder level below `books/`
- Each folder = 1 topic
- Only EPUBs and PDFs inside

### Technology Stack

| Component     | Choice                 | Why                             |
| ------------- | ---------------------- | ------------------------------- |
| Engine        | Python 3.11            | Homebrew-managed, local control |
| RAG Framework | LlamaIndex             | Efficient local indexing        |
| Embeddings    | `all-MiniLM-L6-v2`     | 384-dim, fast, open source      |
| Vector Store  | FAISS                  | Local, no network calls         |
| File Watching | `watchdog`             | Delta detection                 |
| Metadata      | Single `metadata.json` | Fast navigation map             |

---

## The Map: `metadata.json`

**Purpose:** Minimal abstraction for rapid AI decision-making.

**Not:**

- A content copy
- A search index
- A documentation system

**Analogy:** Subway map, not geographic map.

### Structure

```json
{
  "topics": [
    {
      "id": "fitness",
      "label": "Fitness & Training",
      "description": "Physical training, strength, conditioning",
      "books": [
        {
          "id": "starting_strength",
          "title": "Starting Strength",
          "author": "Mark Rippetoe",
          "year": 2011,
          "tags": ["barbell", "strength", "programming"]
        }
      ]
    }
  ]
}
```

**Design decisions:**

- Tags exist only on books (semantic signal)
- Topics have: name + short description
- No text duplication
- Every field serves navigation

---

## System Pseudocode

### 1. MCP Initialization

```mermaid
graph TD
  START[Start MCP] --> VAULT[Set VAULT_PATH]
  VAULT --> META[Load metadata.json]
  META --> EMB[Load embedding model<br/>all-MiniLM-L6-v2]
  EMB --> VEC[Load FAISS index]
  VEC --> WATCH[Start file watcher]
  WATCH --> WAIT[Wait for invocation]

  style WAIT fill:#90EE90
  style START fill:#87CEEB
```

**Rule:** MCP is passive. Nothing happens until explicitly called.

---

### 2. File Watching (Delta-Based)

```mermaid
graph TD
  EVENT[File event detected] --> TYPE{Event type?}

  TYPE -->|Added| PARSE[Parse document]
  PARSE --> CHUNK[Split into chunks]
  CHUNK --> GEN[Generate embeddings]
  GEN --> ADD[Add to vector index]
  ADD --> UPDATE1[Update metadata.json]

  TYPE -->|Removed| REMOVE[Remove from vector index]
  REMOVE --> UPDATE2[Update metadata.json]

  UPDATE1 --> SAVE[Save index + metadata]
  UPDATE2 --> SAVE
  SAVE --> WAIT[Wait for next event]

  style SAVE fill:#FFD700
```

**Rule:** Never reindex everything. Only delta changes.

---

### 3. Query Flow

```mermaid
graph TD
  CALL[MCP explicitly invoked] --> RECEIVE[Receive user query]
  RECEIVE --> READ[Read metadata.json ONLY]

  READ --> MATCH[Calculate semantic similarity:<br/>query vs topics/tags]

  MATCH --> SELECT[Select best topic + books]

  SELECT --> CONF{Confident<br/>match?}

  CONF -->|No| CLARIFY[Ask user for clarification]
  CLARIFY --> STOP[Stop]

  CONF -->|Yes| CONSTRAIN[Build constrained query<br/>for selected scope]

  CONSTRAIN --> SEARCH[Search vector index<br/>top_k chunks only]

  SEARCH --> RETRIEVE[Retrieve minimal context]

  RETRIEVE --> LLM[Send chunks + query to LLM]

  LLM --> ANSWER[Generate answer]

  ANSWER --> RETURN[Return to caller]

  style READ fill:#FFB6C1
  style SEARCH fill:#87CEEB
  style CLARIFY fill:#FF6347
  style RETURN fill:#90EE90
```

---

### 4. Navigation Logic (Map ≠ Territory)

```mermaid
graph LR
  Q[User Query:<br/>'Compare Foucault<br/>and Han on discipline'] --> MAP[Read metadata.json]

  MAP --> SIM[Semantic similarity]

  SIM --> T1[Topic: philosophy<br/>Score: 0.89]
  SIM --> T2[Topic: AI<br/>Score: 0.32]

  T1 --> B1[Book: Psychopolitics<br/>Tags: power, discipline<br/>Score: 0.91]

  B1 --> DECISION{Confident?}

  DECISION -->|Yes| VEC[Query FAISS<br/>scope: philosophy/Psychopolitics]
  DECISION -->|No| ASK[Ask user]

  VEC --> RAG[RAG retrieval]

  style MAP fill:#FFD700
  style VEC fill:#87CEEB
  style ASK fill:#FF6347
```

**Key insight:** The map guides navigation. Territory is only accessed after direction is clear.

---

## Query Flow Principles

**Steps:**

1. User asks a question
2. AI reads **only** `metadata.json`
3. AI calculates semantic similarity (query ↔ topics/tags)
4. AI selects best topic + books
5. **Only then** does vector store query execute
6. If unclear → request clarification

**Never:**

- Explore the vault without direction
- Load large contexts speculatively
- Attempt "smart" auto-discovery
- Make guesses when uncertain

---

## File Watching & Indexing

**Trigger:** Book added/removed from vault

**Process:**

1. `watchdog` detects filesystem change
2. Extract delta (new/removed files only)
3. Update embeddings (incremental)
4. Update `metadata.json`
5. Persist to FAISS

**No full reindexing unless explicitly requested.**

---

## What This System Is Not

- ❌ Not a chat interface
- ❌ Not cloud-dependent
- ❌ Not a general-purpose MCP
- ❌ Not trying to be "smart" beyond navigation

**It is:**

- ✅ A navigation layer for your books
- ✅ A semantic index with minimal latency
- ✅ A local-first, privacy-preserving tool

---

## Development Environment

### Python

**Always use Homebrew Python 3.11:**

```bash
/opt/homebrew/bin/python3.11 -m pip install <package>
/opt/homebrew/bin/python3.11 script.py
```

**Never use:**

- `python3`, `python`, `pip`, `pip3` without full path
- Virtual environments (venv, conda, etc.)
- System Python

### Environment Variables

All secrets in `.env`:

```bash
GEMINI_API_KEY=your_key_here
```

**Never commit `.env` or hardcode keys.**

---

## Roadmap

### Phase 1: Core Infrastructure

- [ ] Implement `metadata.json` generation
- [ ] File watcher with delta detection
- [ ] FAISS vector store setup
- [ ] Local embedding pipeline (`all-MiniLM-L6-v2`)

### Phase 2: Query System

- [ ] Metadata-first query routing
- [ ] Clarification prompts when ambiguous
- [ ] RAG retrieval from selected topics/books
- [ ] Response caching

### Phase 3: Optimization

- [ ] Threading/multiprocessing
- [ ] Index persistence optimization
- [ ] PDF support
- [ ] Image extraction and indexing

### Phase 4: Clients

- [ ] VS Code extension (thin client)
- [ ] Terminal client
- [ ] API documentation

---

## For AI Agents

When working on this codebase:

1. **Read `metadata.json` first** before any RAG query
2. **Never explore the vault** without explicit instruction
3. **Use Homebrew Python 3.11** for all operations
4. **Respect the map-territory distinction**
5. **Optimize for latency** over comprehensiveness

This is a navigation system, not a knowledge base.
