# Librarian

> A BYOB (Bring Your Own Books) semantic search over your personal library.

> All local (books, embedding models, database). Connect with your favorite AI provider and ask away.

---

| Possible uses               | Description                                                                                                                                                     |
| :-------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ⚖️&nbsp;**Compliance**      | Collect all compliance and regulation manuals to test a new idea the proper way                                                                                 |
| 🔧&nbsp;**Home&nbsp;fixes** | Move all your home devices and appliances' instruction manuals + warranties, ask troubleshooting questions                                                      |
| 🌱&nbsp;**Gardening**       | Permaculture, indigenous plant guides, water management books to redesign your garden with less trial-and-error                                                 |
| 🎸&nbsp;**New&nbsp;hobby**  | Wanna try a new hobby but have no idea of scope? Collect authoritative books in the field you wanna learn, and reduce your confusion by asking freely questions |
| 🎮&nbsp;**Game&nbsp;Dev**   | Design patterns, procedural generation, narrative theory—query mid-project to find exactly which book explained that algorithm                                  |
| 🌍&nbsp;**Academic**        | Anthropology, ethnography, linguistics—entire library indexed locally, works offline for weeks in remote locations                                              |
| 💼&nbsp;**Professional**    | Legal texts, industry whitepapers, case studies—cite exact sources during audits or client presentations                                                        |
| 💪&nbsp;**Fitness**         | Training programs, nutrition guides, sports science—get grounded advice without influence rabbit holes                                                          |

---

## Installation

### Prerequisites
- Docker & Docker Compose
- 2GB RAM minimum
- macOS/Linux (Windows: use WSL2)

### Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/nonlinear/librarian.git
cd librarian

# 2. BYOB: Bring Your Own Books
# Add .epub and .pdf files to books/ folder
# (or use test books from test-books/)
cp test-books/*.epub books/

# 3. Start (downloads embedding model automatically on first run)
docker-compose up -d

# 4. Test
docker exec librarian python3 /app/engine/scripts/faiss_search.py "your query here"
```

**First run:** 
- Downloads embedding model (~130MB, BAAI/bge-small-en-v1.5)
- Indexing takes ~2-5 min per 100 books (one-time only)
- After that, adding books takes <10s (incremental indexing)

---

## Usage

### Command Line

```bash
docker exec librarian python3 /app/engine/scripts/faiss_search.py "design systems"
```

### AI Assistant Integration

**Two options:**

1. **Full MCP integration** → See [SKILL.md](SKILL.md)
   - Claude Desktop / OpenClaw
   - Complete setup guide
   - Output format rules

2. **Quick prompt** → See [skill-prompt.md](skill-prompt.md)
   - Copy-paste into custom instructions
   - No installation needed
   - Works with any AI assistant

**Example queries:**
- "What do I have about design systems?"
- "Find books on mutual aid and care"
- "How do taxonomies differ from folksonomies?"

> 👉 Without MCP/prompt your AI uses general knowledge. With it you get precise citations from your library

---

## How it works

```mermaid
graph TD
    QUERY([User query]) --> EMBED[Generate embedding]
    EMBED --> FAISS[Search FAISS index]
    FAISS --> RESULTS[Top N results]
    RESULTS --> FORMAT[Format with citations]
    FORMAT --> ANSWER([Answer with book excerpts])
```

**Architecture:**
- **Indexer:** Extracts text from EPUB/PDF → chunks → embeddings
- **FAISS:** Vector similarity search (BAAI/bge-small-en-v1.5, 384-dim)
- **Incremental:** Only processes new/changed books (O(Δ))
- **Watcher:** Auto-detects new files (<10s reindex)
- **MCP:** Claude Desktop / OpenClaw integration

---

## Features

✅ **Semantic search** (not just keywords)  
✅ **Incremental indexing** (add books → auto-reindex in <10s)  
✅ **File watcher** (drop book in folder → indexed automatically)  
✅ **MCP server** (Claude Desktop / OpenClaw integration)  
✅ **EPUB reader** (deep linking to exact paragraphs)  
✅ **Stable IDs** (content-addressed, survives renames)  
✅ **All local** (no API calls, works offline)

---

## Performance

| Library Size | Index Time | Query Time | Disk Space |
|--------------|------------|------------|------------|
| 100 books    | 2-5 min    | <0.3s      | ~100 MB    |
| 500 books    | 10-15 min  | <0.5s      | ~400 MB    |
| 1000 books   | 20-30 min  | <0.7s      | ~800 MB    |

**After initial index:** Adding 1 book takes <10s.

---

## Test Books

Included in `test-books/`:
- Alice in Wonderland (Lewis Carroll)
- Frankenstein (Mary Shelley)
- Moby Dick (Herman Melville)

All public domain (Project Gutenberg).

---

## Utilities

### AI Assistant Integration
- **[SKILL.md](SKILL.md)** - Full MCP integration guide
- **[skill-prompt.md](skill-prompt.md)** - Quick copy-paste prompt

---

## Troubleshooting

### Indexing stuck
```bash
# Restart container
docker-compose restart

# Force reindex
docker exec librarian python3 /app/engine/scripts/indexer_v6.py
```

### No results for query
1. Check books indexed: `docker exec librarian cat /app/books/.index_state.json | jq .total_books`
2. Check FAISS loaded: `docker logs librarian | grep "FAISS loaded"`
3. Try broader terms

### Watcher not detecting new books
```bash
# Check watcher is running
docker logs librarian | grep "Watcher active"

# Restart watcher
docker-compose restart
```

---

## Community

Join the discussion:
- **Matrix:** [#librarian:matrix.org](https://matrix.to/#/#librarian:matrix.org) *(coming soon)*
- **Issues:** [GitHub Issues](https://github.com/nonlinear/librarian/issues)

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Credits

- **[FAISS](https://github.com/facebookresearch/faiss):** Meta AI (vector search)
- **[Sentence Transformers](https://www.sbert.net/):** HuggingFace (embeddings)
- **[epub.js](https://github.com/futurepress/epub.js/):** FuturePress (EPUB rendering)
- **[FastAPI](https://fastapi.tiangolo.com/):** Sebastián Ramírez (web framework)

---

**Built by [Nonlinear Studio](https://nonlinear.nyc)**
