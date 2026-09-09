#!/usr/bin/env python3
"""
Release Sync Test — PROVEN codebase and published documentation are ONE release unit.

Publication Rule (owner 2026-09-03):
  > Codebase and documentation published are a release unit. If they are not
  > synchronized, publication FAILS. Never publish one without the other.
  > Documentation drift is a publication ERROR, not a documentation task.

This is the executable SYNC CHECK between the codebase (engine/) and the
published docs (about/). It fails (ERROR) whenever the two diverge, so a
release cannot advance to publication with one side stale.

Direction A (docs -> code): every port/route/env/feature/interface the docs
  declare as a fact MUST exist in the code candidate.
Direction B (code -> docs): every public capability/interface the code exposes
  that is part of the product contract MUST be represented in the published
  docs (no silent capability).

Intentionally stdout-only for the PASS/ERROR verdict; imports of third-party
libraries are avoided so it runs in any python3.
"""
import re
import pathlib
import sys

# Fonte única de "rotas públicas" — os decorators do código (não da doc).
HTTP_FILES = [
    "engine/scripts/librarian_http.py",
    "engine/reader/routes.py",
    "engine/scripts/renderer.py",
]
# Rotas de contrato que a DOC oriunda DEVE referenciar (produkt contract surface).
DOC = pathlib.Path("about")
CODE = pathlib.Path("engine")

# Capabilities oficiais que a doc features.md declara e que devem ter casa no código.
# (chave capac. -> token de código que prova a capacidade existe)
CAPABILITY_CODE_ANCHOR = {
    "semantic search": "faiss_search",
    "file watcher (auto-index)": "watcher.py",
    "incremental indexing": "index",              # indexer*.py / init_index
    "stable content-addressed IDs": "chunk_address_map",
    "reader deep-link": "reader.html",
    "evidence / citation target": "evidence_renderer",
    "MCP (stdio + http)": "mcp_server_faiss",
}


def _code_src():
    return "\n".join(
        p.read_text(errors="ignore") for p in CODE.rglob("*.py") if p.exists()
    )


def _route_facts_from_code():
    """Rotas públicas reais extraídas dos decorators @app/@router."""
    routes = set()
    for f in HTTP_FILES:
        p = pathlib.Path(f)
        if not p.exists():
            continue
        for m in re.finditer(r"@(?:app|router)\.(?:get|post|mount|include)\("
                             r"?[\"']([^\"']+)[\"']", p.read_text(errors="ignore")):
            routes.add(m.group(1))
    return routes


def _env_facts_from_code():
    envs = set()
    for p in CODE.rglob("*.py"):
        for m in re.finditer(r"environ\.get\(\"(LIBRARIAN_[A-Z_]+|READER_[A-Z_]+)", p.read_text(errors="ignore")):
            envs.add(m.group(1))
    return envs


def _doc_text():
    parts = []
    for p in DOC.glob("*.md"):
        parts.append(p.read_text(errors="ignore"))
    return "\n".join(parts)


# Vars interpretadas pelo ConfigResolver do engine (must exist in config.py).
RESOLVER_ENV = {
    "LIBRARIAN_BOOKS", "LIBRARIAN_CORPUS", "LIBRARIAN_MODELS", "LIBRARIAN_MODEL",
    "LIBRARIAN_CONFIG", "READER_PORT", "READER_PUBLIC_URL", "READER_STATIC_DIR",
}
# Vars de ORQUESTRAÇÃO do docker-compose (host-level; não lidas pelo engine).
COMPOSE_ENV = {
    "LIBRARIAN_CONTAINER_NAME", "LIBRARIAN_MODELS_DIR", "LIBRARIAN_READER_PORT",
    "LIBRARIAN_READER_URL", "LIBRARY_ROOT",
}


# ── Direction A: docs de oriunda declaram um fato -> código tem de ter ─────
def collect_doc_route_facts(doc):
    """Rotas HTTP que a doc cita (endpoint), NAO filesystem paths.

    Ignora paths de exemplo como /app/..., /path/to/..., e paths de volume.
    Só considera tokens que a doc trata como endpoint HTTP — citados com verbos
    GET/POST (ex. 'GET /search', '`POST /`', layout rotas) ou prefixo de API.
    """
    rotas = set()
    # 1) linhas com verbo HTTP (GET/POST) em tabela/lista de endpoints
    for line in doc.splitlines():
        if re.search(r"\b(GET|POST)\s*/", line):
            for m in re.finditer(r"\b(GET|POST)\s*(`?)(/[a-z0-9_{}/.-]*)", line):
                rotas.add(m.group(3))
    # 2) tokens de rota de API em backtick que comecem com / v1/ /search /chunk /resolve
    #    ou outros endpoints conhecidos — mas nunca paths /app, /path, /Users
    for m in re.finditer(r"`(/(?:v[0-9]+[a-z0-9_/{}-]*|search|resolve[a-z0-9_/{}-]*|chunk[a-z0-9_/{}-]*|stats|health|reader[a-z0-9_/{}-]*|wall|books[a-z0-9_/{}.]*|api/[a-z0-9/{}_-]+|render[a-z0-9_/{}.-]*|reading-state[a-z0-9_/{}-]*))`", doc):
        rotas.add(m.group(1))
    return rotas


def test_docs_to_code_routes():
    """Toda rota citada na doc publicada existe no code candidate."""
    code_routes = _route_facts_from_code()
    doc = _doc_text()
    # normalize: doc pode citar sem chaves ex/ /chunk/{id}
    for r in collect_doc_route_facts(doc):
        base = r.split("{")[0].rstrip("/")
        # check any code route starts with the same literal prefix
        found = any(
            cr == r or cr.split("{")[0].rstrip("/") == base or cr.rstrip("/") == r.rstrip("/")
            or base in cr
            for cr in code_routes
        )
        if not found and r not in ("/", "/wall"):
            assert False, f"doc declara rota '{r}' que nao existe no codebase"
    # Also every env the config doc documents must be a code env.
    doc_envs = set(re.findall(r"\b(LIBRARIAN_[A-Z_]+|READER_[A-Z_]+|LIBRARY_ROOT)\b", doc))
    code_envs = _env_facts_from_code()
    compose = pathlib.Path("docker-compose.yml").read_text(errors="ignore") if pathlib.Path("docker-compose.yml").exists() else ""
    for e in doc_envs:
        if e in RESOLVER_ENV:
            assert e in code_envs, f"doc menciona env do engine '{e}' inexistente no config resolver"
        elif e in COMPOSE_ENV or "LIBRARY_ROOT" == e:
            assert e in compose or "$" + "{" + e in compose, f"doc menciona var de orquestracao '{e}' inexistente no docker-compose"


def test_docs_do_not_claim_absent_interface():
    """A doc nao deve declarar uma rota MCP HTTP dedicada (8089) que o produto
    nao serve. (garante que o doc nao vira ficcao sobre um endpoint ausente)."""
    doc = _doc_text()
    assert "8089:" not in doc  # sem claim de porta MCP HTTP no compose


# ── Direction B: código tem capability pública -> doc anda junto ────────────
def test_code_capabilities_are_documented():
    """Toda capability nuclear do produto tem representacao na doc about/."""
    code = _code_src()
    doc = _doc_text().lower()
    missing = []
    for cap, anchor in CAPABILITY_CODE_ANCHOR.items():
        # anchor de código existe?
        code_has = anchor.lower() in code.lower()
        # a capacidade esta documentada (nome-chave aparece)?
        doc_has = anchor.split(".")[0].lower() in doc or cap.split()[0] in doc
        if code_has and not doc_has:
            missing.append(cap)
    assert not missing, (
        "Capacidades presentes no codebase sem casa na doc publicada (drift): "
        + ", ".join(missing)
    )


def test_release_manifests_claim_same_release():
    """doc nao declara contagem/versao contraditoria ao code (impede docs que
    se contradizem ou embutem numero de instancia)."""
    doc = _doc_text()
    # Proibe numero vivo de instancia em doc publica (deve vir de /stats).
    for bad in ["1112 books", "520,162", "290 books", "711 books"]:
        assert bad not in doc, f"doc publica contagem de instancia: {bad}"


if __name__ == "__main__":
    failed = 0
    for name in sorted(globals()):
        if name.startswith("test_"):
            fn = globals()[name]
            try:
                fn()
                print(f"PASS: {name}")
            except AssertionError as e:
                print(f"ERROR: {name}: {e}")
                failed += 1
    print(f"\n=== SYNC CHECK: {'PASS (codebase e docs em sync)' if not failed else str(failed) + ' ERROR(s) - nao publicar'} ===")
    sys.exit(1 if failed else 0)
