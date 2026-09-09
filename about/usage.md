# Usage

> Como CONSUMIR o Librarian (release **`9567aaec`**): MCP, HTTP, reader e CLI. Endpoints e ferramentas
> verificados contra `engine/scripts/librarian_http.py`, `engine/scripts/mcp_server_faiss.py` e
> `engine/reader/routes.py`.

## Formas de consumir

### 1. Via MCP (recomendado — o produto "casa" com seu assistente)

O Librarian expõe duas superfícies MCP equivalentes na busca semântica:

- **MCP sobre HTTP** — no processo principal (container), porta `READER_PORT` (default 8088),
  entrada JSON-RPC em `POST /` (protocol version `2024-11-05`, server `librarian-http`).
- **MCP stdio** — executando localmente `python3 engine/scripts/mcp_server_faiss.py` como um processo que
  seu cliente MCP lança. Exclusivo: nenhuma porta a configurar.

**Tools MCP (comuns às duas):**
| Tool | Args | Retorna |
|------|------|---------|
| `search_library` | `query` (obrig.), `k` (default?→top-N), `min_score` (opcional) | hits com `chunk_id/book_id/score` |
| `get_chunk` | `chunk_id` | conteúdo/texto do chunk |
| `stats` | — | contagem de books/chunks |

> **Exemplo (disparo no assistente):** *"consulte no meu acervo sobre design systems"* — o cliente MCP
> chama `search_library`, recebe os top-N hits com endereço resolvível, e pode mandar o leitor abrir a
> citação.

### 2. Via HTTP (REST)

Quando você quer chamar diretamente (curl/script).

**Busca:**
```sh
curl -X POST localhost:8088/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"mutual aid and care","limit":10}'
# → {"results":[{chunk_id,book_id,book_title,text,score,address}, ...]}
```

**Resolve um chunk (para abrir no reader):**
```sh
curl localhost:8088/resolve/<chunk_id>
# → {book_id, address, reader_url}
```

**Chunk avulso:**
```sh
curl localhost:8088/chunk/<chunk_id>
```

**Estado / diagnóstico:**
```sh
curl localhost:8088/health    # liveness
curl localhost:8088/stats     # books/chunks/modelo/dims
```

**MCP envelope sobre HTTP** (para clientes que falam JSON-RPC): `POST /` com
`{"method":..., "id":...}`. Suporta `initialize` e as tools do servidor.

### 3. Via Reader (verificação humana)

Quando uma resposta cita um `book_id`, abra o leitor para conferir a fonte exata:

```
http://localhost:8088/reader/<book_id>          # leitor do livro (abre no parágrafo citado, com highlight)
http://localhost:8088/wall                      # lista de paredes
http://localhost:8088/books/<book_id>.epub      # serve o EPUB bruto
```

### 4. Via CLI (dentro do container)

Para uma query rápida sem cliente MCP:

```sh
docker compose exec librarian python3 /app/engine/scripts/faiss_search.py "sua query"
```

---

## Circuito completo (o que o produto prova)

O uso "de verdade" exercita todo o caminho:

```
pergunta → MCP (search) → retrieval (FAISS) → answer
        → source link /resolve → reader → highlight → corroboration
```

- O assistente faz uma pergunta → `search_library`/`/search` retorna chunks com endereço.
- Para cada claim, o assistente abre `/resolve/{chunk_id}` → `reader_url`.
- O leitor abre o livro no parágrafo exato e faz highlight → você CONFIRMA que a resposta está
  fundamentada no texto real (não é alucinação).

---

## Exemplos de pergunta

- *"O que meu acervo diz sobre organização emergente?"*
- *"Consulte sobre mutual aid e sistemas de cuidado."*
- *"Como taxonomias diferem de folksonomias?"*

---

## Sobre escalas

- Indexar o corpus no primeiro boot demora conforme o tamanho (dezenas de minutos para ~1000 livros);
  depois disso adicionar um livro é incremental (<10 s).
- Query é subsegunda mesmo em bibliotecas grandes (FAISS + modelo na memória do mesmo processo).
