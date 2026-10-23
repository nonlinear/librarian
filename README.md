# Librarian

> **A BYOB (Bring Your Own Books) semantic search for your personal library.**
> All local — books, embedding model, index. Works offline. No account, no API key.

Put EPUBs or PDFs in a folder. Librarian indexes them locally and answers questions from them,
with citations that open the exact paragraph so you can verify instead of trust.

---

## ⚠️ Read this first: MCP is not ready as a *service*

**There is no hosted MCP endpoint to paste into a client.** No URL, no account, no
`https://.../mcp` to add.

This is not a missing feature flag. It is the architecture: **Librarian runs on your machine, and
your agent launches it as a local process.** The MCP server is a subprocess, not a network service.

| Expectation | Status | What actually works today |
|---|---|---|
| "I'll connect to Librarian's hosted MCP server" | ❌ **Not available** | No remote endpoint exists. MCP runs locally, from your clone. |
| "It remembers my history / personalizes over time" | ❌ **Not available** | Every query is independent. No cross-session memory, no user model. |
| "I'll paste a URL into Claude/Cursor and it just works" | ❌ **Not available** | You configure a **command**, not a URL. See [Step 6](#6-connect-it-to-your-ai-agent). |
| Semantic search over your own books | ✅ **Works** | FAISS + `BAAI/bge-small-en-v1.5`, fully local. |
| Drop a book in a folder → indexed automatically | ✅ **Works** | Folder watcher, incremental. ~seconds per book. |
| Ask through an AI agent | ✅ **Works** | MCP **stdio** (agent launches it) or plain HTTP REST. |
| Citations you can open and verify | ⚠️ **Partial** | `/resolve` hands back a `reader_url` that 404s. The reader works — you just have to build the URL with the book's content hash. [Details](#reader--check-a-citation-yourself). |

> **The one-line truth:** Librarian is a **local library server you run yourself**. Clone it, point it
> at your books, let your agent launch the MCP process. There is nothing to log into.

### Why this table exists (changelog)

Three documentation defects caused real users to conclude the product was broken. Each is recorded
here so the mistake cannot be repeated, and each is why specific checks below exist.

| When | What the docs said | What was true | Cost to the reader |
|---|---|---|---|
| ≤ 2026-09-02 | "MCP over HTTP on port **8089**" (`about/install.md`, `about/stack.md`, `about/views/mcp-distribution.md`) | MCP surface is **stdio**. Nothing listens on 8089. | Configured a dead port → "product doesn't work" |
| 2026-09-10 | GitHub docs pinned release **`9567aaec`** in 5 files | `9567aaec` was the **Round 6 candidate**, never released. The release is **`7302d5a6`** (tag `librarian-15`). | Chasing a SHA that never shipped |
| This README | Publish `main` as "the product" | The shipped image was built **2026-10-02** from a tree that is **not** `main`. See [Version drift](#version-drift--read-before-you-trust-toolslist). | Tool signatures differ from the source you read |

Every command in Sections 0, 4, 5, 7 and 8 below was executed against a **running Librarian
instance** before being written down — health check, `stats`, a live `search_library` call, a
`/resolve` round trip, and the stdio `initialize` + `tools/list` handshake. Where a command did
**not** behave as the product intends, that is stated in place rather than hidden.

---

## Who this is for

- **You**, if you have a folder of EPUBs/PDFs and want to ask questions across all of them.
- **Your AI agent** (Claude Code, Cursor, Codex, OpenClaw, or any harness with shell access).
  This README is written to be **handed to an agent** and executed top to bottom. A human can
  follow it identically — the commands are the same.

---

## Requirements

| Requirement | Detail | Why |
|---|---|---|
| **Docker** | Docker Desktop (macOS/Windows) or Docker Engine (Linux) | Everything runs in one container. |
| **Compose** | `docker compose` (v2) **or** `docker-compose` (v1) | Either works — but see Step 0, they are **not** interchangeable mid-command. |
| **Memory** | **16 GB allocated to Docker** | ⚠️ The 7.6 GB default makes first indexing crash (OOM). Settings → Resources → Memory. |
| **Disk** | ~2 GB + your books | Dependencies, model (~130 MB), index. |
| **OS** | macOS / Linux / Windows via WSL2 | |
| **Network** | Outbound HTTPS on **first start only** | Downloads the embedding model. Then fully offline. |
| **Books** | `.epub` and `.pdf` only | Other extensions are ignored — silently. |

You do **not** need Python on the host. You do **not** need an API key.

---

## Install — the exact sequence

### 0. Detect your compose command

```sh
docker compose version >/dev/null 2>&1 && echo "USE: docker compose" || echo "USE: docker-compose"
```

Use whichever it prints for **every** command below.

> ⚠️ Many Docker Desktop installs ship only the legacy binary and fail with
> `docker: unknown command: docker compose`. This is not hypothetical — the instance this README was
> verified against is one of them (`docker-compose` = v5.1.4, `docker compose` = error). The detect
> command above catches that.
>
> The difference matters twice, and only there:
> - `docker compose exec -T …` vs `docker-compose exec -T …`
> - In the MCP `args` array: `["docker","compose","exec"]` is **three** elements,
>   `["docker-compose","exec"]` is **two**. Mixing them yields a client that starts and finds nothing.

### 1. Clone

```sh
git clone https://github.com/nonlinear/librarian.git
cd librarian
```

### 2. Point it at your books

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
> of the box. You only need a `config.json` to override paths explicitly; see
> [`about/configuration.md`](about/configuration.md).

### 3. Start

```sh
docker compose up -d        # or: docker-compose up -d
```

First run: **~5–10 min** (image build) + **~2 min** (model download) + indexing time.

**Watch it** — this is how you tell "working" from "hung":

```sh
docker compose logs -f      # or: docker-compose logs -f
```

Expected order: model download → index check/rebuild → `Starting file watcher...` →
HTTP server up on 8088.

### 4. Prove it is alive — do not skip

"Container is Up" is **not** proof. The container is Up while still downloading the model.

```sh
curl -s localhost:8088/health
# {"status":"ok","service":"librarian-mcp","port":8088,"chunks":0}
```

| Response | Meaning | Action |
|---|---|---|
| No response | Still starting | Keep tailing logs. Wait. |
| `"status":"ok"` | Server is live | **Continue.** |
| `"chunks":0` | Live, nothing indexed yet | Expected with an empty corpus. Add a book (next step). |

---

## 5. Add books → they index themselves

Drop an `.epub` or `.pdf` into the corpus folder (default `./books`, or your `LIBRARY_ROOT`).

The watcher detects the file → waits ~5 s for the write to finish → indexes in the background →
reloads the search index. **No restart.**

Confirm:

```sh
curl -s localhost:8088/stats
# {"books":1,"chunks":613,"embedding_model":"BAAI/bge-small-en-v1.5","dimensions":384}
```

Rules:

- Only `.epub` / `.pdf` are indexed. Everything else is ignored **silently**.
- Anything inside a folder named **`no-indexing/`** is skipped — use it to park books.
- Incremental: one new book is ~seconds, not a rebuild.
- Looks stuck? `docker compose logs --tail=50`.

---

## 6. Connect it to your AI agent

This is the part that surprises people, so read it twice.

### MCP is **stdio**, not a URL

Your harness **launches the MCP server as a subprocess** and talks to it over stdin/stdout.
There is no port to open, no endpoint to paste. The config is a **command**:

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
> `-T` disables TTY allocation, which is required for stdio.

If Step 0 printed `docker-compose`, the args become two elements:

```json
"command": "docker-compose",
"args": ["exec", "-T", "librarian", "python3", "/app/engine/scripts/mcp_server_faiss.py"]
```

### Version drift — read before you trust `tools/list`

The `tools/list` you get **depends on which image you built**, and the two do not agree:

| Surface | Tools | `search_library` args |
|---|---|---|
| **Stdio MCP**, image built from this repo's tree | `search_library`, `get_chunk`, `stats` | `query`, `k`, `min_score` |
| **Stdio MCP**, older prebuilt image (`2026-10-02`) | same three tools | `query`, `k`, `min_score`, **`agent`, `epic`, `session_id`** |
| **HTTP JSON-RPC** bridge (`POST /` on 8088) | `search_library` **only** — hardcodes one tool | `query`, `limit` |

> ⚠️ **If you call `agent` / `epic` / `session_id`, expect them to be ignored on a fresh build.**
> Those parameters exist in older images (they feed an experimental event-supply path) and were
> **removed** from the source in `main`. A clone + `docker compose up --build` gives you the version
> **without** them. Do not build features on them; verify with `tools/list` before relying on a field.
>
> **Always run `tools/list` on your own instance.** It is the only authoritative answer for what your
> client will actually see — and it takes one command (below).

### Test the same path without a client first

If the config above misbehaves, verify the server itself before blaming the client:

```sh
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"check","version":"1"}}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
 | docker compose exec -T librarian python3 /app/engine/scripts/mcp_server_faiss.py
```

Expected: a `serverInfo` line, then a `tools` array. If that works, the problem is your client
config (usually `cwd`).

> The index loads **lazily on the first `search_library` call** (~1 GB FAISS index). The first query
> is slow; that is expected, not a hang. `initialize` answers instantly.

### Tell the agent when to use it

A connected tool is not a used tool. Give your agent a trigger — in a skill, system prompt, or
project rules:

> **"consult", "research", "librarian", "pesquisa", "biblioteca"** → call `search_library`.

And wire the **full loop**, not just the search:

```
search_library → top-k hits → /resolve each chunk_id → open reader_url
```

Search without resolve gives answers with **no verifiable source**. That is the product.

---

## 🧠 The Librarian skill — ready to use, and where it lives

Writing that trigger from scratch is unnecessary: a production-tested skill already exists and is the
recommended way to use this product.

**The canonical copy is installed at:**

```
~/.openclaw/skills/librarian/SKILL.md
```

**This repo carries a read-only copy at `skills/librarian/SKILL.md`**, published automatically by a
`pre-push` git hook — so anyone who clones gets the protocol without an OpenClaw environment.

| | |
|---|---|
| **Source of truth** | `~/.openclaw/skills/librarian/` (the installed copy) |
| **In this repo** | `skills/librarian/` — a copy, refreshed on every `git push` |
| **Direction** | always installed → repo. The repo is downstream, never upstream. |

> ⚠️ **Do not edit `skills/librarian/SKILL.md` in this repo.** The next push overwrites it from the
> installed copy. Change the installed skill, then push.

### What the skill gives you

It is not a prompt snippet — it is an operating protocol (v3.5, 427 lines) covering:

- a **fail-closed activation gate** — the agent must open the skill that turn, or it may not answer;
- **query assembly before the call** (expansion, primary source first, structure-aware navigation);
- **8 research rules**, including *Rule 4 — absence of evidence is not evidence of absence* and
  *Rule 8 — cite or it did not happen*;
- a **mandatory output format** with source links and similarity scores;
- **locator-integrity checks** and hard stops.

The practical difference: without the skill, an agent calls `search_library` and summarizes. With it,
the agent must show sources or decline to answer.

### Two caveats before you adopt it as-is

The shipped skill is written against a **specific production instance** and a **newer build** than
this repo. It is honest to say so:

1. **It contains instance-specific URLs.** Examples reference `https://8088.nonlinear.nyc/reader/...`
   and "1100+ EPUBs". Replace those with your own host and corpus size.
2. **It expects a memory-aware build.** The skill passes `agent`, `epic`, and `session_id` to
   `search_library`. The container that ships with this repo **does** accept them; the published
   source on `main` **does not** (see the pinning note in [Step 6](#6-connect-it-to-your-ai-agent)).
   If you run a build without them, the extra arguments are ignored — the protocol still works, you
   just lose per-agent/epic memory tagging.

Neither caveat breaks the retrieval loop. Both matter if you are publishing this skill to your own
users.

---

## 7. Use it without an agent

### HTTP REST

```sh
# semantic search
curl -s -X POST localhost:8088/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"mutual aid and care","limit":5}'

# a hit → reader deep-link
curl -s localhost:8088/resolve/<chunk_id>
# → {"book_id":..., "address":..., "reader_url":"http://localhost:8088/reader/<book_id>"}

# one chunk's text
curl -s localhost:8088/chunk/<chunk_id>

# readiness / inventory
curl -s localhost:8088/health
curl -s localhost:8088/stats
```

### CLI (inside the container)

```sh
docker compose exec librarian python3 /app/engine/scripts/faiss_search.py "mutual aid and care"
```

### Reader — check a citation yourself

```
http://localhost:8088/reader/<book_hash>   # opens the book at the cited paragraph, highlighted
http://localhost:8088/wall                 # library wall
```

> ⚠️ **Known defect — `/resolve` returns a `reader_url` that 404s.**
> The `book_id` on a hit is `librarian:<uuid>`, but the reader route resolves books by their
> 16-char **content hash**. The URL `/resolve` hands you therefore returns HTTP 404.
>
> **Verified against a running instance:**
>
> ```
> /resolve/ch_73bc4ca8c404              → book_id "librarian:01cbd455-…"
> /reader/librarian:01cbd455-…          → 404
> /reader/df4667d1be9719fe              → 200   (same book, by content hash)
> ```
>
> **Workaround:** the 16-char hash is the book's **filename stem** in your corpus. The REST `/search`
> response does **not** include it. Two places do:
>
> - **MCP `search_library`** — the hit carries `book_hash`
> - **`GET /api/books`** — each entry's `id` is the hash
>
> ```sh
> curl -s localhost:8088/api/books
> ```
>
> **This is a defect, not intended behaviour.** Citation verification is **partially working** until
> it is fixed — and for books whose `address.cfi` is `null`, the reader opens at the book's start
> rather than the cited paragraph.

---

## 8. Acceptance check (definition of done)

All four must return data:

```sh
# 1. server live
curl -s localhost:8088/health

# 2. corpus indexed — books > 0
curl -s localhost:8088/stats

# 3. a query returns hits
curl -s -X POST localhost:8088/search -H 'Content-Type: application/json' \
  -d '{"query":"a phrase you know is in your book","limit":3}'

# 4. a hit resolves to a reader link that actually opens
curl -s localhost:8088/resolve/<chunk_id from step 3>
curl -s -o /dev/null -w '%{http_code}\n' "<reader_url from step 4>"   # expect 200
```

Steps 1–3 must return data. For step 4, **check the status code — do not assume the URL works.**
If it returns 404, the hit uses the `librarian:<uuid>` form; look up the hash via
`GET /api/books` or MCP's `book_hash` (see [Known defect](#reader--check-a-citation-yourself)). The
citation loop is only proven when the reader responds 200 and shows the paragraph.

Report what the four checks returned — not "container started".

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/health` never answers | Model downloading, or first index running | `docker compose logs -f`; wait for the HTTP server line |
| Container restarts in a loop | Docker memory < 16 GB → OOM on first index | Raise Docker memory to 16 GB, then `docker compose up -d` |
| Model download fails / times out | No outbound HTTPS on first start | Retry with network access; only first start needs it |
| `chunks:0` forever | Corpus empty, or mounted elsewhere | `docker compose exec librarian ls /app/books` |
| A book never indexes | Wrong extension, or inside `no-indexing/` | Only `.epub`/`.pdf`; move it out |
| `docker: unknown command: docker compose` | Only legacy Compose installed | Use `docker-compose` everywhere, including MCP `args` |
| Port 8088 in use | Another service on 8088 | `LIBRARIAN_READER_PORT=8090 docker compose up -d` |
| MCP client shows no tools | Client pointed at a URL instead of launching stdio | Use the config in [Step 6](#6-connect-it-to-your-ai-agent) |
| MCP client errors on exec | Wrong `cwd` — wrong compose project | `cwd` = absolute path to your clone |
| Client ignores `agent` / `epic` / `session_id` | Those args were removed from `main`; only older images have them | Expected. Run `tools/list`; do not depend on them |
| First query very slow | FAISS index (~1 GB) loads lazily | Expected once; then fast |
| `reader_url` from `/resolve` returns 404 | Hit uses `librarian:<uuid>`; reader resolves by content hash | Known defect. Get hashes from `GET /api/books` (`id`) or MCP `search_library` (`book_hash`) |
| Reader opens but not at the cited paragraph | `address.cfi` is `null` for some books | Known limitation; the reader lands at the book start |

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

> The skill is the recommended entry point for agents. If you only read one file besides this README,
> read [`skills/librarian/SKILL.md`](skills/librarian/SKILL.md) — it is the difference between an
> agent that searches and an agent that cites.

> ⚠️ `about/install.md` still says "MCP (recommended): point your client at the container's HTTP
> server **or** the stdio process". Only **stdio** gives you all three tools. Trust this README over
> that doc where they disagree, and prefer [`about/usage.md`](about/usage.md) for the MCP section.

---

## How it works

```mermaid
flowchart LR
    BOOK[You add a book] --> WATCH[Folder watcher]
    WATCH --> INDEX[Incremental index]
    INDEX --> MCP[MCP stdio / HTTP ready]
    MCP --> AGENT[Your agent asks]
    AGENT --> CITATION[Hit + reader_url]
    CITATION --> READER[You verify the paragraph]
```

### Performance reference

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
- **`config.example.json`** — generic config template (no instance paths)

Python 3.11 · FAISS · sentence-transformers · FastAPI · epub.js

---

## Credits

- **[FAISS](https://github.com/facebookresearch/faiss):** Meta AI (vector search)
- **[Sentence Transformers](https://www.sbert.net/):** HuggingFace (embeddings)
- **[epub.js](https://github.com/futurepress/epub.js/):** FuturePress (EPUB rendering)
- **[FastAPI](https://fastapi.tiangolo.com/):** Sebastián Ramírez (web framework)

---

**Built by [Nonlinear Studio](https://nonlinear.nyc)**
