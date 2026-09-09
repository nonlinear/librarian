# Troubleshooting

> Problema → diagnóstico → solução. Verificado contra o comportamento real do container
> (`entrypoint.sh`, `watcher.py`, `init_index.py`, `librarian_http.py`) na release **`9567aaec`**.

## Indexação / primeiro boot

### "O container sobe mas `/stats` mostra 0 books"
- **Causa:** o volume de corpus está vazio ou `LIBRARY_ROOT` aponta para uma pasta sem EPUB/PDF.
- **Verifique:** `docker compose logs` (deve mostrar "Index check" + watcher a rodar).
- **Solucione:** coloque `.epub`/`.pdf` no diretório montado. O watcher detecta novos arquivos e indexa.
  Se o índice ainda está sendo construído, aguarde; `/stats` reflete após o index.

### "Indexação do primeiro boot levou muito tempo / parece travada"
- **Causa:** indexar ~milhares de livros é pesado; o entrypoint roda o índice com retry (3×30 s) se falhar.
- **Solucione:** aguarde a conclusão no log. Não mate o container no meio — o `init_index.py` usa
  checkpoint; se o processo morre sem finalizar, o self-heal reconstrói na próxima subida (idempotente).

### "OOM / crash durante a indexação"
- **Causa:** memória Docker insuficiente. O indexador + modelo + FAISS vivem no mesmo processo — consumir
  RAM em excesso derruba o build.
- **Solucione:** suba a memória do Docker (Settings → Resources → Memory → 16 GB mínimo → Apply & Restart).
  Não rode indexador e servidor competindo por RAM sem folga.

## Runtime / servidor

### "Não consigo abrir `localhost:8088`"
- **Verifique:** porta correta? (`READER_PORT` default 8088). Container de pé? `docker ps`.
- **Solucione:** veja logs `docker compose logs -f`. Se o modelo não baixou ainda, o entrypoint aguarda
  o download antes de subir o HTTP.

### "O MCP do meu assistente não conecta"
- **Causa provável:** você está tentando abrir uma **porta MCP dedicada** — não existe. O produto é
  **stdio** (o cliente lança `mcp_server_faiss.py`) **ou** HTTP na 8088 (`POST /`, envelope JSON-RPC).
- **Solucione:** se seu cliente suporta stdio, aponte para `engine/scripts/mcp_server_faiss.py`; se
  suporta HTTP, use `http://localhost:8088` (entrada JSON-RPC em `/`). Não há porta "8089 MCP" legada.

## Corpus / identidade

### "Adicionei um livro e ele não aparece nas buscas"
- **Causa:** o watcher detectou mas o reindex incremental ainda não terminou, OU o arquivo está num
  formato não suportado.
- **Solucione:** aguarde alguns segundos (incremental <10s) e cheque `docker logs`. Formato suportado:
  EPUB e PDF.

### "Renomeei um arquivo e os links antigos quebraram?"
- **Não deveria:** os `book_id`/`chunk_id` são content-addressed (estáveis ao conteúdo). Renomear o
  arquivo **não** quebra os deep-links emitidos antes — eles apontam para o id estável.

## Leitor / evidência

### "O reader abre mas não faz highlight do parágrafo citado"
- **Causa:** provavelmente a citação caiu num caso de ancoragem de texto que o renderer não achou.
- **Solucione:** o sistema tenta `text_anchor` → `cfi` → fallback (abre o livro). Se abrir sem highlight,
  é limitação pontual de ancoragem no texto (PDF/epub edge), não quebra do produto. Confira o texto do
  chunk em `/chunk/{id}` para validar a evidência por conta própria.

## Config / build

### "Quero expor o leitor via túnel/domínio, mas os links vêm localhost"
- Configure `READER_PUBLIC_URL` com a URL pública (túnel/domínio). Default é `localhost` — o engine não
  assume URL pública sozinho (segurança por padrão). A env aparece em `engine/config.py` como
  `reader_url_base`.

### "Mudei config mas nada muda"
- `config.example.json` muda o exemplar; o **efetivo** vem de `config.json` (ou env). Verifique qual
  fonte o processo está lendo (`LIBRARIAN_CONFIG`). Em Docker, env via compose `environment` é a forma
  determinística.

---

## Quando é um bug de produto vs uma questão da instance

> Se o problema é específico do SEU corpus/instância (um PDF edge, spam FAISS, memória da sua máquina),
> não é um bug do Librarian como produto. Se um **comportamento documentado** não ocorre (ex.: leitor não
> abre nenhum `book_id`, `/search` não responde mesmo com corpus), aí sim é defeito de produto.
> Registrationo esses como achados, não como configuração.
