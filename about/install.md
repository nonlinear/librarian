# Install

> Como instalar e rodar o Librarian do zero (BYOBook) verificado contra o candidate
> **`9567aaec`**. Documentação de produto — cada passo corresponde ao comportamento real
> do `Dockerfile` / `entrypoint.sh` / `docker-compose.yml` da release.

## Pré-requisitos

- **Docker** com Docker Compose (macOS/Linux; Windows: WSL2).
- **Memória:** 16 GB mínimo dedicada ao Docker (Settings → Resources → Memory). O indexador + o modelo
  embedding + o servidor FAISS rodam no mesmo processo; abaixo de ~16 GB o index do primeiro boot pode
  crashar por OOM. (É um limite de runtime da instance, não um requisito do código.)
- **Disco:** ~2 GB para dependências + modelo embedding (~130 MB) + o índice do seu corpus.
- Um cliente capaz de falar MCP (assistente/HI que você já usa) OU uso por HTTP/CLI.

## Fluxo de instalação

### 1. Clone + entre no repo

```sh
git clone <repo-do-librarian> librarian
cd librarian
```

> O repo NÃO embute corpus. `books/` é um diretório que VOCÊ monta como volume (BYOBook) — o engine
> nunca é distribuído com uma biblioteca.

### 2. (Opcional) Aponte o compose para o seu corpus

O `docker-compose.yml` monta `${LIBRARY_ROOT:-./books}:/app/books`. Por padrão usa `./books` (vazio, só
`.gitkeep`). Se seus livros vivem em outro lugar, informe o caminho absoluto na hora de subir:

```sh
LIBRARY_ROOT=/caminho/para/minha/biblioteca docker compose up -d
```

> Se `LIBRARY_ROOT` não existir ou estiver vazio, o Librarian sobe com índice vazio e o watcher passa a
> indexar o que for colocado na pasta. A indexação acontece **no primeiro boot** — não embutimos
> `faiss.index`.

### 3. Suba o container

```sh
docker compose up -d
```

No primeiro boot o entrypoint (`entrypoint.sh`) faz, nesta ordem:

1. **Baixa o modelo embedding** (`BAAI/bge-small-en-v1.5`, ~130 MB) para `/app/engine/models`, **se**
   ainda não estiver em cache (checa `models--BAAI--bge-small-en-v1.5`). Modelos ficam persistidos no
   volume `LIBRARIAN_MODELS_DIR` para não rebaixar a cada rebuild.
2. **Self-heals o índice** (`init_index.py`, até 3 tentativas com retry de 30 s): se o índice/estado
   existir e for válido, termina em segundos; se faltar/corromper, reconstrói do zero com checkpoint.
3. **Sobe o file watcher** (`watcher.py`, em background) — detecta EPUB/PDF novos na pasta de corpus e
   indexa incrementalmente.
4. **Sobe o servidor HTTP** (`librarian_http.py`) em **`8088`** (foreground) — é o processo principal.

Primeiro build/start: ~5–10 min (imagem) + ~2–5 min (indexação dos primeiros livros). Depois disso,
adicionar um livro leva <10 s de reindex incremental.

### 4. Verifique que está de pé

```sh
curl -s localhost:8088/health
# → {"status":"ok","service":"librarian-mcp","port":8088,"chunks":<n>}
```

ou veja os logs:

```sh
docker compose logs -f
```

### 5. Use

- **MCP (recomendado):** aponte seu assistente/cliente MCP para o servidor (HTTP do container ou o
  processo stdio `mcp_server_faiss.py`) — veja `usage.md`.
- **HTTP:** endpoints `/search`, `/chunk/{id}`, `/resolve/{chunk_id}`, `/stats`, `/reader/*` — veja
  `usage.md`.
- **CLI dentro do container:** `docker compose exec librarian python3 /app/engine/scripts/faiss_search.py "sua
  query"`.

---

## Instalação não-Docker (execução direta)

> ROI p/ a maioria é Docker. Se quiser rodar sem container: precisa de Python ≥ 3.10 com as deps de
> `engine/requirements.txt`, o modelo embedding, e as env `LIBRARIAN_BOOKS`/`LIBRARIAN_MODELS` apontando
> para o seu corpus/modelos. O entrypoint é o contrato de inicialização; os passos acima (modelo → índice
> → watcher → server) valem igualmente fora do compose, só que você os executa manualmente.

---

## Pergunta frequente (instalação)

**Por que o `books/` local não tem livros?** Porque o Librarian é BYOBook: o corpus é seu. O diretório
montado existe para você apontar sua biblioteca; nada de corpus da "nossa" instance é distribuído.
