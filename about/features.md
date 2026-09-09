# Features

> Capacidades OFICIAIS do Librarian na release **`9567aaec`**, cada uma verificada contra o código do
> candidate. Se algo não está aqui, não é uma capability declarada do produto.

## Busca semântica (núcleo)

- **Recuperação vetorial** sobre o corpus inteiro via FAISS (`faiss_search.py`). Não é busca por keyword: é
  busca por similaridade de embedding.
- **Modelo embedding:** `BAAI/bge-small-en-v1.5`, 384 dims (default, configurável por `LIBRARIAN_MODEL`).
- **Top-k com score:** `/search` aceita `{query, limit, min_score}`; `limit` 1–100, default 10.
- Resultado normalizado: cada hit traz `chunk_id`, `book_id`, `book_title`, `text`, `score`, `address`
  (endereço de citação — ver Evidence).

## Indexação automática

- **Watcher de pasta** (`watcher.py`): livro EPUB/PDF colocado no diretório de corpus → indexado
  automaticamente.
- **Indexação incremental:** adicionar um livro reindexa só o delta (<10 s), não o corpus todo.
- **Self-heal do índice** (`init_index.py` no entrypoint): se `faiss.index`/estado faltar ou corromper,
  reconstrói com retry (máx. 3 tentativas). É idempotente — se o índice é válido, termina em segundos.

## MCP (transporte)

- **HTTP MCP** (`librarian_http.py`, porta `READER_PORT`=8088): protocolo JSON-RPC em `POST /` +
  endpoints REST `/v1/*`. Suporta `initialize`, tools. É o processo principal do container.
- **MCP stdio** (`mcp_server_faiss.py`): servidor MCP sobre **stdio** para clientes que lançam um processo
  local. Tools: `search_library(query, k, min_score)`; `get_chunk(chunk_id)`; `stats`.

> MCP é **stdio** (o executável `mcp_server_faiss.py` é chamado como subprocesso pelo cliente, sem porta
> própria). O compose NÃO expõe porta 8089 — não há listener HTTP dedicado a MCP nessa porta.

## Evidence / citação verificável (proof layer)

- Cada chunk recuperado carrega um **endereço** resolvível: EPUB → `{href, text_anchor|cfi}`; PDF → page.
- **`/resolve/{chunk_id}`**: resolve um `chunk_id` em `book_id` + endereço + `reader_url` — o elo que
  desacopla a descoberta da leitura.
- **Reader com highlight** — ver seção Reader.
- **Renderer de evidência** (`evidence_renderer` + `/render/evidence`): formata a evidência com o alvo de
  citação, para a resposta poder citar a fonte exata.

## Reader (deep-links)

- **`/reader/{book_id}`**: leitor EPUB que abre o livro no parágrafo exato indicado pela citação e faz o
  highlight — você confere a resposta contra o texto original.
- **`/wall`**: página de lista (sem catálogo por padrão).
- **`/books/{book_id}.epub`**: serve o EPUB bruto resolvido via `book_registry`.
- **`/api/books`**: JSON de introspecção da biblioteca (id/title/author/chunk_count).

## Endpoints HTTP (resumo, verificado em `librarian_http.py`)

| Método+rota | Função |
|-------------|--------|
| `GET /health` | liveness + contagem de chunks |
| `GET /stats` | books, chunks, modelo, dimensões |
| `POST /` | entrada MCP JSON-RPC (initialize/tools) |
| `POST /search` | busca semântica `{query, limit, min_score}` |
| `GET /resolve/{chunk_id}` | chunk → book/address/reader_url |
| `GET /chunk/{chunk_id}` | conteúdo do chunk |
| `POST /v1/search`, `GET /v1/resolve/{id}`, `GET /v1/health` | API versionada |
| `GET /reading-state/{book_id}` | estado de leitura por livro |
| `GET /reader/{book_id}`, `/wall`, `/books/{id}.epub`, `/api/books` | reader (ver acima) |
| `POST /render`, `/render/evidence`, `GET /render/health` | renderer de evidência |
| `GET /` | health MCP (no `/`) |

## Estabilidade / identidade

- **Stable IDs content-addressed:** `book_id`/`chunk_id` derivados do conteúdo — sobrevivem a renames de
  arquivo (o endereço não quebra se você renomear o `.epub`).
- Deep-links emitidos (via `/resolve`) apontam para o `book_id` estável, não para um path.

## Operacional

- Tudo local por padrão (livros, modelos, índice) — funciona offline.
- Config por env/`config.json` sem path de instance embutido (BYOBook).
