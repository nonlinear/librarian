# Librarian

> **A BYOB (Bring Your Own Books) semantic search for your personal library.**
> All local — books, embedding model, index. Works offline. No account, no API key.

Put EPUBs or PDFs in a folder. Librarian indexes them locally and answers questions from them,
with citations that carry a `book_id`, a chunk address, and a reader link — so an answer can be
checked against the book instead of trusted.

---

## Why

Librarian exists because a useful answer needs a source you can open.

You already own the books. What you do not have is a way to ask a question across all of them at
once and land on the paragraph that answers it. Search engines give you links; a general model gives
you confident prose with no provenance. Librarian indexes your EPUBs and PDFs into a local vector
index and returns **addressable** results — every hit resolves to a book, a location, and a reader
link you can open and check.

Three properties follow, and all three are the point:

| | |
|---|---|
| **Local** | Your corpus never leaves the machine. One container, one index, no account, no API key. |
| **Offline** | After the first start (model download) it works with no network at all. |
| **Verifiable** | An answer without a source is not an answer. Every hit carries `chunk_id`, `book_id`, and an address. |

Librarian is a **server you run**, not a service you subscribe to. MCP comes with it: the image ships
the MCP server, so the only thing you configure in your agent is a command to launch it.

---

## Who this is for

- **You**, if you have a folder of EPUBs/PDFs and want to ask questions across all of them.
- **Your AI agent** (Claude Code, Cursor, Codex, OpenClaw, or any harness with shell access).
  This README is written to be **handed to an agent** and executed top to bottom. A human can
  follow it identically — the commands are the same.

Not for you if: you want a hosted endpoint, a login, or cross-session memory. None of those exist —
see [Status](#status) before you build on them.

---

## Status

What works today, stated plainly so nobody builds on an assumption:

| | Status | Notes |
|---|---|---|
| Semantic search over your own books | ✅ | FAISS + `BAAI/bge-small-en-v1.5`, fully local. |
| Drop a book in a folder → indexed automatically | ✅ | Folder watcher, incremental, ~seconds per book. |
| MCP server | ✅ | Ships in the image. Stdio. Your agent launches it. |
| HTTP REST API | ✅ | `/search`, `/chunk/<id>`, `/resolve/<id>`, `/stats`, `/health`. |
| Reader | ✅ | Opens a cited book; paragraph highlight depends on `address.cfi`. |
| **Citation link from `/resolve`** | ⚠️ | Returns a `reader_url` that 404s. Defect — see [Reader](#reader). |
| Hosted MCP endpoint | ❌ | Does not exist, by architecture. There is no URL to paste. |
| Cross-session memory / personalization | ❌ | Every query is independent. No user model. |

---

## How

### 0. Detect your compose command

```sh
docker compose version >/dev/null 2>&1 && echo "USE: docker compose" || echo "USE: docker-compose"
```

Use whichever it prints for every command below. Commands here write `docker compose`; if yours
printed `docker-compose`, substitute it — including in the MCP config where it becomes
`"docker-compose", "exec"` instead of `"docker", "compose", "exec"`.

> ⚠️ Some Docker Desktop installs ship only the legacy binary and error with
> `docker: unknown command: docker compose`.

### 1. Requirements

| Requirement | Detail | Why |
|---|---|---|
| **Docker** | Docker Desktop (macOS/Windows) or Docker Engine (Linux) | Everything runs in one container. |
| **Compose** | `docker compose` (v2) **or** `docker-compose` (v1) | Either works — see Step 0. |
| **Memory** | **16 GB allocated to Docker** | ⚠️ The 7.6 GB default makes first indexing crash (OOM). |
| **Disk** | ~2 GB + your books | Dependencies, model (~130 MB), index. |
| **OS** | macOS / Linux / Windows via WSL2 | |
| **Network** | Outbound HTTPS on **first start only** | Downloads the embedding model. Then fully offline. |
| **Books** | `.epub` and `.pdf` only | Other extensions are ignored — silently. |

You do **not** need Python on the host. You do **not** need an API key.

### 2. Clone

```sh
git clone https://github.com/nonlinear/librarian.git
cd librarian
```

### 3. Point it at your books

The container mounts `${LIBRARY_ROOT:-./books}` → `/app/books`. Pick one:

**A — bundled folder (simplest).** Copy your books into the repo's `books/`:

```sh
cp ~/Downloads/*.epub ./books/
```

**B — keep your library where it already is.** Export an absolute path before starting:

```sh
export LIBRARY_ROOT=/absolute/path/to/my/library
```

> The folder **must already exist** — Docker fails to mount a missing host path.
> The repo ships `books/` empty on purpose. It never distributes a corpus (BYOBook).

> **`config.example.json` is optional** — the container reads environment variables and works out
> of the box. See [`about/configuration.md`](about/configuration.md).

### 4. Start

```sh
docker compose up -d
```

First run: **~5–10 min** (image build) + **~2 min** (model download) + indexing time.

**Watch it** — this is how you tell "working" from "hung":

```sh
docker compose logs -f
```

Expected order: model download → index check/rebuild → `Starting file watcher...` → HTTP server up.

### 5. Prove it is alive — do not skip

"Container is Up" is **not** proof. The container is Up while still downloading the model.

```sh
curl -s localhost:8088/health
# {"status":"ok","service":"librarian-mcp","port":8088,"chunks":0}
```

| Response | Meaning | Action |
|---|---|---|
| No response | Still starting | Keep tailing logs. Wait. |
| `"status":"ok"` | Server is live | **Continue.** |
| `"chunks":0` | Live, nothing indexed yet | Expected with an empty corpus. Add a book. |

### 6. Use it

**a) Add books.** Drop an `.epub` or `.pdf` into the corpus folder (default `./books`, or your
`LIBRARY_ROOT`). The watcher detects it → waits ~5 s → indexes in the background → reloads the index.
No restart.

```sh
curl -s localhost:8088/stats
# {"books":1,"chunks":613,"embedding_model":"BAAI/bge-small-en-v1.5","dimensions":384}
```

Only `.epub`/`.pdf` are indexed; everything else is ignored silently. Anything inside
`no-indexing/` is skipped. Incremental: one book ≈ seconds.

**b) Query over HTTP.**

```sh
# semantic search
curl -s -X POST localhost:8088/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"mutual aid and care","limit":5}'

# one chunk's text
curl -s localhost:8088/chunk/<chunk_id>

# readiness / inventory
curl -s localhost:8088/health
curl -s localhost:8088/stats
```

**c) Query over CLI, inside the container.**

```sh
docker compose exec librarian python3 /app/engine/scripts/faiss_search.py "mutual aid and care"
```

### 7. Install as MCP

MCP is already installed. The image builds it (`pip install mcp`, `mcp_server_faiss.py` made
executable) — **there is nothing to install and no port to open.** You give your agent a command; it
launches the server as a subprocess over stdio.

```json
{
  "mcpServers": {
    "librarian": {
      "command": "docker",
      "args": [
        "compose", "exec", "-T", "librarian",
        "python3", "/app/engine/scripts/mcp_server_faiss.py"
      ],
      "cwd": "/absolute/path/to/librarian"
    }
  }
}
```

> **`cwd` must be the absolute path to your clone** — otherwise `docker compose exec` runs in the
> wrong project and finds no `librarian` service. This is the #1 setup failure.
> `-T` disables TTY allocation, required for stdio.

**Tools** (verify on your own instance — the answer depends on your build):

| Tool | Args |
|---|---|
| `search_library` | `query` (required), `k` (default 10, max 50), `min_score` (optional) |
| `get_chunk` | `chunk_id` |
| `stats` | — |

> ⚠️ **If you call `agent` / `epic` / `session_id`, expect them to be ignored.** Those exist in an
> older prebuilt image and were removed from the source on `main`. A fresh `docker compose up --build`
> gives you the version without them. Run `tools/list` to see what your instance actually exposes.

**Test without a client:**

```sh
docker compose exec -T librarian python3 /app/engine/scripts/mcp_server_faiss.py
```

If that handshakes, the server is fine and the problem is your client config — usually `cwd`.

### 8. Install the Librarian skill

The MCP connection gives your agent a tool. The **skill** gives it the discipline to use the tool
well — when to consult, how to assemble a query, and what an answer must contain.

**Installed at** `~/.openclaw/skills/librarian/SKILL.md`. **This repo carries a copy at**
[`skills/librarian/SKILL.md`](skills/librarian/SKILL.md), published automatically by a `pre-push`
hook — so a clone includes the protocol without an OpenClaw environment.

| | |
|---|---|
| **Source of truth** | `~/.openclaw/skills/librarian/` (the installed copy) |
| **In this repo** | `skills/librarian/` — a copy, refreshed on every `git push` |
| **Direction** | always installed → repo. The repo is downstream, never upstream. |

> ⚠️ **Do not edit `skills/librarian/SKILL.md` in this repo.** The next push overwrites it.

The skill is an operating protocol, not a prompt snippet: a fail-closed activation gate, query
assembly before the call, 8 research rules (including *absence of evidence is not evidence of
absence*), a mandatory output format with source links, and locator-integrity hard stops.

Two caveats before adopting it as-is:

1. **It contains instance-specific URLs** — `8088.nonlinear.nyc` in examples, and a worked example
   linking a real `book_id` in the author's corpus. Copy the **shape**, not the link.
2. **It passes `agent`/`epic`/`session_id`** to `search_library`. A build from this repo ignores them;
   the protocol still works, you just lose memory tagging.

### 9. Acceptance check (definition of done)

```sh
# 1. server live
curl -s localhost:8088/health

# 2. corpus indexed — books > 0
curl -s localhost:8088/stats

# 3. a query returns hits
curl -s -X POST localhost:8088/search -H 'Content-Type: application/json' \
  -d '{"query":"a phrase you know is in your book","limit":3}'

# 4. a hit resolves to a reader link that opens
curl -s localhost:8088/resolve/<chunk_id from step 3>
```

Steps 1–3 must return data. For step 4, **check the status code — do not assume the URL works** (see
[Reader](#reader)). Report what the four checks returned, not "container started".

### Reader

```
http://localhost:8088/reader/<book_hash>   # opens the book; highlight when address.cfi is set
http://localhost:8088/wall                 # library wall
```

> ⚠️ **Known defect — `/resolve` returns a `reader_url` that 404s.**
> The `book_id` on a hit is `librarian:<uuid>`, but the reader resolves books by their 16-char
> **content hash**.
>
> ```
> /resolve/ch_73bc4ca8c404      → book_id "librarian:01cbd455-…"
> /reader/librarian:01cbd455-…  → 404
> /reader/df4667d1be9719fe      → 200   (same book, by content hash)
> ```
>
> **Workaround:** the hash is the book's filename stem. `GET /api/books` returns it as `id`; MCP's
> `search_library` returns it as `book_hash`. The REST `/search` response does **not** include it.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/health` never answers | Model downloading, or first index running | `docker compose logs -f`; wait |
| Container restarts in a loop | Docker memory < 16 GB → OOM on first index | Raise to 16 GB, then `up -d` |
| Model download fails | No outbound HTTPS on first start | Retry with network; only first start needs it |
| `chunks:0` forever | Corpus empty, or mounted elsewhere | `docker compose exec librarian ls /app/books` |
| A book never indexes | Wrong extension, or inside `no-indexing/` | `.epub`/`.pdf` only; move it out |
| `docker compose` not found | Only legacy Compose installed | Use `docker-compose` |
| Port 8088 in use | Another service on 8088 | `LIBRARIAN_READER_PORT=8090 docker compose up -d` |
| MCP client shows no tools | Client pointed at a URL instead of launching stdio | Use the config in [Step 7](#7-install-as-mcp) |
| MCP client errors on exec | Wrong `cwd` — wrong compose project | `cwd` = absolute path to your clone |
| First query very slow | FAISS index (~1 GB) loads lazily | Expected once; then fast |
| `reader_url` returns 404 | `book_id` is a uuid, reader keyed by hash | See [Reader](#reader) |

---

## What it is for

| | Description |
| :-- | :-- |
| ⚖️ **Compliance** | Collect regulation and compliance manuals; test an idea the proper way |
| 🔧 **Home fixes** | Appliance manuals + warranties in one place; ask troubleshooting questions |
| 🌱 **Gardening** | Permaculture, indigenous plant guides, water management — redesign with less trial-and-error |
| 🎸 **New hobby** | Collect authoritative books in a field; reduce confusion by asking freely |
| 🎮 **Game dev** | Design patterns, procedural generation, narrative theory — find which book explained that algorithm |
| 🌍 **Academic** | Anthropology, ethnography, linguistics — offline for weeks in remote locations |
| 💼 **Professional** | Legal texts, whitepapers, case studies — cite exact sources in audits and presentations |
| 💪 **Fitness** | Training programs, nutrition, sports science — grounded advice without influence rabbit holes |

**Example questions**

- "What does my library say about design systems?"
- "Consult on mutual aid and care."
- "How do taxonomies differ from folksonomies?"

---

## Configuration

Resolution order (highest wins): `config.json` → environment variables → defaults derived from
`library_root`. Details in [`about/configuration.md`](about/configuration.md).

| Variable | Default | Meaning |
|---|---|---|
| `LIBRARY_ROOT` | `./books` | Host path mounted as the corpus |
| `LIBRARIAN_BOOKS` | `/app/books` | Corpus path **inside** the container |
| `LIBRARIAN_READER_PORT` | `8088` | Host **and** container port for HTTP / reader |
| `LIBRARIAN_MODELS_DIR` | `./models` | Embedding model cache (persists across rebuilds) |
| `LIBRARIAN_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model |

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [`skills/librarian/SKILL.md`](skills/librarian/SKILL.md) | **The agent skill** — activation gate, query assembly, 8 research rules, output format |
| [`about/README.md`](about/README.md) | Overview + use cases |
| [`about/install.md`](about/install.md) | Install from zero (BYOBook) |
| [`about/configuration.md`](about/configuration.md) | How config is resolved (env / config.json / defaults) |
| [`about/features.md`](about/features.md) | Official capabilities, verified against code |
| [`about/usage.md`](about/usage.md) | How to consume: MCP, HTTP, reader, CLI |
| [`about/troubleshooting.md`](about/troubleshooting.md) | Problem → diagnosis → fix |

---

## How it works

```mermaid
flowchart LR
    BOOK[You add a book] --> WATCH[Folder watcher]
    WATCH --> INDEX[Incremental index]
    INDEX --> MCP[MCP stdio / HTTP ready]
    MCP --> AGENT[Your agent asks]
    AGENT --> CITATION[Hit + address]
    CITATION --> READER[You open the book]
```

| Library size | First index | Query | Disk |
|---|---|---|---|
| 100 books | 2–5 min | <0.3 s | ~100 MB |
| 500 books | 10–15 min | <0.5 s | ~400 MB |
| 1000 books | 20–30 min | <0.7 s | ~800 MB |

After the first index, adding one book is <10 s.

---

## Tech stack

- **`engine/scripts`** — indexing, retrieval, FAISS search, watcher, HTTP/MCP servers
- **`engine/reader`** — EPUB reader shell (deep-links + highlight)
- **`engine/shared`** — shared response/evidence models (single source of truth)
- **`engine/evidence_renderer`** — renders evidence with citation targets

Python 3.11 · FAISS · sentence-transformers · FastAPI · epub.js

---

## Credits

- **[FAISS](https://github.com/facebookresearch/faiss):** Meta AI (vector search)
- **[Sentence Transformers](https://www.sbert.net/):** HuggingFace (embeddings)
- **[epub.js](https://github.com/futurepress/epub.js/):** FuturePress (EPUB rendering)
- **[FastAPI](https://fastapi.tiangolo.com/):** Sebastián Ramírez (web framework)

**Built by [Nonlinear Studio](https://nonlinear.nyc)** — contact: **hi@nonlinear.nyc**
