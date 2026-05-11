# Librarian

> A BYOB (Bring Your Own Books) semantic search for your personal library.

> All local (books, embedding models, database). Connect with your favorite AI provider and ask away.

```mermaid
flowchart LR
    USER["👨‍🔬 Adds book to folder"] --> WATCHER["🤖 Watches, auto-index"]
    WATCHER --> MCP["🤖 Updates MCP"]
    MCP --> QUERY["👨‍🔬 Consults AI"]
```

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

## Features

🏠 **All local:** No API calls, works offline  
🧠 **Semantic search:** Not just keywords  
👁️ **File watcher:** Drop book in folder → indexed automatically  
⚡ **Incremental indexing:** Add books → auto-reindex in <10s  
🔌 **MCP server:** Claude Desktop / OpenClaw integration  
📖 **EPUB reader (soon):** Deep linking to exact paragraphs  
🔒 **Stable IDs:** Content-addressed, survives renames  

---

## Example Queries

- "Research on what do I have about design systems?"
- "Consult books on mutual aid and care"
- "Consult on how do taxonomies differ from folksonomies?"

---

## Requirements

1. Docker Desktop

   - Memory: **16GB minimum** (Settings → Resources → Memory)

   - ⚠️ **Critical:** Default 7.6GB will cause indexing to crash

   - Disk space:** ~2GB (dependencies + models)

2. macOS/Linux (Windows: use WSL2)

3. Any AI system with MCP capabilities

---

### Installation

#### Clone the repo

```
cd ~/Documents
git clone https://github.com/nonlinear/librarian.git librarian
cd librarian
```

#### Start Docker Desktop and increase memory

Settings → Resources → Memory → 16GB → Apply & Restart

#### Start the container

```
cd ~/Documents/librarian
docker-compose up -d
```

This will: 

- Build Docker image (~5-10 min first time)
- Download embedding model (~130MB, cached for future runs)
- Index any book on `librarian/books` folder (~2-5 min for 3 test books)

#### Install skill/prompt

- [SKILL.md](SKILL.md) (triggers: "consult" "librarian" "research")
- [librarian.prompt.md](librarian.prompt.md)

#### Optional: check logs

```
docker logs librarian -f
```

#### Try your first query

> Consult books on white rabbit, wonderland

> Research monster creator regret

CLI query: `docker exec librarian python3 ~/Documents/librarian/app/engine/scripts/faiss_search.py "query"`

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

---

## Performance

| Library Size | Index Time | Query Time | Disk Space |
|--------------|------------|------------|------------|
| 100 books    | 2-5 min    | <0.3s      | ~100 MB    |
| 500 books    | 10-15 min  | <0.5s      | ~400 MB    |
| 1000 books   | 20-30 min  | <0.7s      | ~800 MB    |

**After initial index:** Adding 1 book takes <10s.

---

**See [specifications.md](specifications.md) for first-run details, MCP connection, and troubleshooting.**

---

## Credits

- **[FAISS](https://github.com/facebookresearch/faiss):** Meta AI (vector search)
- **[Sentence Transformers](https://www.sbert.net/):** HuggingFace (embeddings)
- **[epub.js](https://github.com/futurepress/epub.js/):** FuturePress (EPUB rendering)
- **[FastAPI](https://fastapi.tiangolo.com/):** Sebastián Ramírez (web framework)

---

**Built by [Nonlinear Studio](https://nonlinear.nyc)**
