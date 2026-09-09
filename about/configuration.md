# Configuration

> Como o Librarian resolve configuração, verificado contra `engine/config.py` e
> `config.example.json` na release **`9567aaec`**. Defaults internos NÃO são documentados como se o
> usuário os fornecesse — ver "Config que você supri" vs "derivado".

## Modelo de resolução

O `ConfigResolver` resolve o valor efetivo assim (verificado em `engine/config.py`):

1. `config.json` carrega as chaves (via `LIBRARIAN_CONFIG` ou `{repo_root}/config.json`).
2. Para a MAIORIA dos campos, `config.json` **vence** o env — as getters leem `_raw` (config) primeiro e só
   usam env como fallback. Ex.: `corpus_path`, `models_dir`, `embedding_model`, `reader_url_base`.
3. **Exceção `library_root`:** aqui env (`LIBRARIAN_BOOKS`) **vence** `config.json` — ordem:
   `library_root(arg) > LIBRARIAN_BOOKS (env) > config.json library_root > dev-fallback {repo_root}/books`.

Regra prática: **use env (`LIBRARIAN_*`/`READER_*`) quando Docker**, e `config.json` quando execução direta
versionada. Para os campos de corpus/modelos declarados nas DUAS fontes, `config.json` é o mais forte; para
a raiz da biblioteca, o env é o mais forte.

## Variáveis de ambiente (verificadas em `engine/config.py`)

### Corpus / caminhos raiz
| Variável | O que faz | Default |
|----------|-----------|---------|
| `LIBRARIAN_BOOKS` | Raiz da biblioteca (onde o corpus vive). Determina `library_root`. | em dev: `{repo_root}/books`; no compose: `/app/books` (volume) |
| `LIBRARIAN_CORPUS` | Path explícito para o diretório de livros (corpus). Se ausente, = `library_root`. | = `library_root` |
| `LIBRARIAN_MODELS` | Onde modelos embedding ficam em cache. | `{library_root}/models`, ou `/app/engine/models` (compose) |
| `LIBRARIAN_CONFIG` | Path para um `config.json` alternativo. | `{repo_root}/config.json` |

### Modelo de embedding / leitor / rede
| Variável | O que faz | Default |
|----------|-----------|---------|
| `LIBRARIAN_MODEL` | Nome do modelo embedding (HuggingFace). | `BAAI/bge-small-en-v1.5` |
| `READER_PORT` | Porta do servidor HTTP/reader. | `8088` |
| `READER_PUBLIC_URL` | URL pública base p/ deep-links de citação (túnel/domínio custom). | `http://localhost:{READER_PORT}` |
| `READER_STATIC_DIR` | Path do diretório de assets estáticos do reader. | derivado: `{engine}/reader/static` |

> `embedding_dim` e `reader_static_dir` **não** devem ser fornecidos no config do usuário: são derivados
> (384 p/ o modelo default; static em `{engine}/reader/static`). O `config.example.json` da release não os
> declara de propósito — ver "Princípio".

## config.json vs config.example.json

- `config.example.json` é um **template** do que o usuário normalmente **suprir** (caminhos do próprio
  corpus), **não** um espelho de todos os defaults internos.
- Ele declara (valores de exemplo genéricos): `library_root`, `corpus_path`, `models_dir`,
  `embedding_model`, `embedding_dim`, `reader_port`, `reader_url_base`.
- **Não** declara `reader_static_dir` nem defaults derivados — o ConfigResolver os deriva.

### Exemplo de config.json mínima
```json
{
  "library_root": "/caminho/para/minha/biblioteca"
}
```
O resto (`corpus_path` = library_root, `models_dir` = library_root/models, embedding default, porta 8088)
é derivado.

### Exemplo completo (config.example.json da release)
```json
{
  "$schema": "librarian-config/v0.1",
  "library_root": "/path/to/your/library",
  "corpus_path": "/path/to/your/library/books",
  "models_dir": "/path/to/your/library/models",
  "embedding_model": "BAAI/bge-small-en-v1.5",
  "embedding_dim": 384,
  "reader_port": 8088,
  "reader_url_base": "http://localhost:8088"
}
```

## Estrutura de diretórios derivada (a partir de `library_root`)

```
{library_root}/
├── books/                 ← seu corpus (EPUB/PDF); watcher indexa aqui
│   ├── book_registry.json ← livro → {id, path, title,...}  (gerado)
│   └── .index_state.json  ← estado do índice (gerado)
├── faiss.index            ← índice vetorial do seu corpus (gerado)
├── metadata.json          ← metadados do índice (gerado)
├── chunk_address_map.json ← chunk_id → {cfi/href/page} (gerado)
├── models/                ← cache de modelos embedding
└── reading_state.json     ← progresso de leitura (gerado)
```

> Tudo que é "gerado" você NÃO cria à mão: o engine deriva do `library_root` no primeiro boot.

## Segurança por padrão

- Nenhuma credencial/segredo é exigida nem shipada.
- O engine **nunca** assume URL pública: deep-links do reader saem por `READER_PUBLIC_URL`
  (default `localhost`) — se você expor via túnel/domínio, configure `READER_PUBLIC_URL`.
- Tudo é local por padrão (livros, modelos, banco) — sem chamada de API externa obrigatória.

---

## Config que você supri vs derivado (princípio)

> Se o canônico é derivado pelo `ConfigResolver`, a doc NÃO o materializa como um campo que você preenche.
> A lista acima distingue: **você fornece** os caminhos de corpus/modelos/porta/URL pública; **o engine
> deriva** dirs internos (`reader/static`, paths de índice, dimensão). Isso é o que evita o drift
> config-doc-código.
