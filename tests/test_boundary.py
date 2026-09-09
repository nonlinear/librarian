#!/usr/bin/env python3
"""
Boundary Tests — PROVE the engine knows nothing about an instance.

Publication Policy P1 (Engine/Instance Boundary): the engine receives a RESOLVED
config and works against it. It must not:
  - hardcode instance paths (/app/books, /Users/<user>)
  - hardcode instance hosts/URLs (*.example.com)
  - assume books/ lives next to the engine
  - access corpus/index/model outside the resolver

These tests are the GUARD for P1. They run against the published codebase and
fail if any instance fingerprint leaks back in.

The static scan uses `ast` so it inspects REAL CODE only — docstrings, comments
and string literals (including fixture examples) are ignored. Env-provided
defaults (os.environ.get("X", "/app/books") / ${VAR:-...}) are permitted.
"""
import ast
import re
import sys
import tempfile
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
SCRIPTS_DIR = ENGINE_DIR / "scripts"

# Instance fingerprints — any match in EXECUTED CODE = boundary violation.
INSTANCE_PATTERNS = [
    re.compile(r"/app/books"),            # hardcoded corpus path
    re.compile(r"/app/engine/models"),    # hardcoded model dir
    re.compile(r"nonlinear\.nyc"),        # instance host
    re.compile(r"8088\.nonlinear"),       # instance reader URL
    re.compile(r"/users/[^/\s\"]+", re.IGNORECASE),  # personal mac path
]

# True for executable lines that legitimately carry ENV-provided defaults
# (the resolver / entrypoint / compose may name paths so a user can inject them).
ENV_DEFAULT = re.compile(
    r"(environ\.get|getenv)\([^\n]*\"/app"
    r"|LIBRARIAN_(BOOKS|MODELS|CONFIG|CORPUS)"
    r"|READER_(PORT|PUBLIC_URL|STATIC_DIR)"
)


def _iter_code_files():
    for path in sorted(ENGINE_DIR.rglob("*.py")):
        yield path
    repo = Path(__file__).resolve().parent.parent
    for name in ("entrypoint.sh",):
        p = repo / name
        if p.exists():
            yield p


def _module_executable_lines(src: str):
    """Return lines of EXECUTED code, skipping docstrings and comments.

    Docstrings (module/class/function), comments and standalone string
expressions are EXCLUDED — only real runtime code is scanned, so fixture
examples inside docstrings don't trip the boundary check.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        # unparseable: fall back to crude comment stripping
        return [ln for ln in src.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    lines = src.splitlines()
    # Collect line ranges covered by docstrings
    skip = set()
    for node in ast.walk(tree):
        body = None
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = getattr(node, "body", None)
        if body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                for ln in range(first.lineno, first.end_lineno + 1):
                    skip.add(ln)
        # Also skip any standalone string expression (data-bearing) not assigned

    result = []
    for i, ln in enumerate(lines, 1):
        if i in skip:
            continue
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        result.append(ln)
    return result


def _code_lines(path):
    if path.suffix == ".py":
        return _module_executable_lines(path.read_text(errors="ignore"))
    # shell: drop comment/blank lines
    out = []
    for ln in path.read_text(errors="ignore").splitlines():
        if ln.strip() and not ln.lstrip().startswith("#"):
            out.append(ln)
    return out


def _is_env_default(line: str) -> bool:
    return bool(ENV_DEFAULT.search(line))


def test_no_instance_paths_in_engine_source():
    """Engine .py/.sh must not hardcode instance paths/URLs/hosts in code."""
    violations = []
    for path in _iter_code_files():
        for lineno, line in enumerate(_code_lines(path), 1):
            if _is_env_default(line):
                continue
            for pat in INSTANCE_PATTERNS:
                if pat.search(line):
                    violations.append(f"{path.name}:{lineno}: {line.strip()}")
    assert not violations, "Boundary violation(s) — engine references instance:\n" + \
        "\n".join(violations)


def test_resolver_resolves_against_custom_root():
    """Resolver must derive a full generic layout from an ARBITRARY library_root."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    sys.path.insert(0, str(ENGINE_DIR))
    import config

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "alt-library"
        cfg_file = root.parent / "config.json"
        cfg_file.write_text('{"library_root": "%s"}' % (root))
        cfg = config.ConfigResolver(config_path=str(cfg_file))

        assert cfg.corpus_path == root
        assert cfg.index_path == root / "faiss.index"
        assert cfg.metadata_path == root / "metadata.json"
        assert cfg.index_state_path == root / ".index_state.json"
        assert cfg.book_registry_path == root / "book_registry.json"
        assert cfg.address_map_path == root / "chunk_address_map.json"
        assert cfg.no_indexing_dir == root / "no-indexing"
        assert cfg.models_dir == root / "models"
        assert cfg.reader_url_base == "http://localhost:8088"  # local default


def test_resolver_accepts_env_override():
    """Env vars (LIBRARIAN_*) must override config for runtime injection."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    sys.path.insert(0, str(ENGINE_DIR))
    import config

    cfg = config.ConfigResolver(
        environ={"LIBRARIAN_BOOKS": "/srv/custom/books",
                 "READER_PUBLIC_URL": "https://reader.example.com"},
        config_path="/nonexistent/config.json",
    )
    assert cfg.corpus_path == Path("/srv/custom/books")
    assert cfg.reader_url_base == "https://reader.example.com"
    assert cfg.index_path == Path("/srv/custom/books/faiss.index")


def test_internalized_pieces_no_flagship_ref():
    """shared/, reader/, evidence_renderer/ must live in engine/ and not
    depend on the legacy flagship submodule (recovered code is part of the
    Librarian, not the deprecated artifact)."""
    root = Path(__file__).resolve().parent.parent
    for sub in ("shared", "reader", "evidence_renderer"):
        d = root / "engine" / sub
        assert d.is_dir(), f"engine/{sub} missing after internalization"
        for f in d.rglob("*"):
            if f.suffix in (".py", ".html", ".json", ".md"):
                if "flagship" in f.read_text(errors="ignore"):
                    # reader.html may contain the string 'flagship' generically;
                    # only flag actual code deps (import/reference to the path)
                    if "flagship." in f.read_text(errors="ignore") or \
                       "flagship/" in f.read_text(errors="ignore"):
                        assert False, f"{sub}/{f.name} still references flagship"
    # The reader routes must resolve via generic env keys
    routes_src = (root / "engine" / "reader" / "routes.py").read_text()
    assert "flagship" not in routes_src


def test_config_example_does_not_declare_reader_static_dir():
    """config.example.json is a TEMPLATE of what a user supplies, not a copy
    of internal resolver defaults. `reader_static_dir` is derived canonically
    by the ConfigResolver; materializing it in the example invites drift and
    was the source of the legacy flagship/ path. (Product finding #1.)"""
    repo = Path(__file__).resolve().parent.parent
    example = repo / "config.example.json"
    assert example.exists(), "config.example.json missing"
    import json
    data = json.loads(example.read_text())
    assert "reader_static_dir" not in data, \
        "config.example.json must not declare reader_static_dir " \
        "(resolver-derived default, not user-supplied path)"
    # flagship must be fully gone from the example too
    assert "flagship" not in example.read_text()


def test_reader_routes_consume_resolver_not_own_fallback():
    """routes.py must get its paths from the ConfigResolver (single source of
    truth), NOT keep a second env/fallback copy. A duplicated default is what
    let `routes.py` diverge from the resolver default. (Product finding #2.)"""
    repo = Path(__file__).resolve().parent.parent
    routes = repo / "engine" / "reader" / "routes.py"
    src = routes.read_text()
    # It must import the same resolver the HTTP server uses.
    assert "from config import get_config" in src
    assert "get_config()" in src
    # It must NOT hold a second literaled fallback path.
    assert "READER_STATIC_DIR" not in src, \
        "routes.py must not read READER_STATIC_DIR directly (single default)"
    assert "/app/reader/static" not in src, \
        "routes.py must not hardcode a reader static fallback path"
    # Paths come from resolved config, not a local os.environ fallback.
    assert "_cfg.reader_static_dir" in src or "_cfg.corpus_path" in src
    # The HTTP server (which mounts /static AND loads routes.py) must also
    # read the dir from the resolver — not hold its own parallel env read.
    http_src = (repo / "engine" / "scripts" / "librarian_http.py").read_text()
    # READER_STATIC_DIR may only appear as a mention/comment, not as an env read.
    assert "os.environ.get(\"READER_STATIC_DIR\"" not in http_src, \
        "librarian_http.py must not read READER_STATIC_DIR directly (single default)"
    assert "_cfg.reader_static_dir" in http_src


def test_compose_does_not_publish_mcp_8089():
    """MCP transport is stdio (not a HTTP listener). Compose must not publish
    a port no listener serves. (Product finding #3; owner decision 2026-09-02.)"""
    repo = Path(__file__).resolve().parent.parent
    compose = repo / "docker-compose.yml"
    assert compose.exists(), "docker-compose.yml missing"
    text = compose.read_text()
    assert "8089" not in text, "compose must not publish 8089 (MCP is stdio)"
    assert "MCP HTTP" not in text


def test_config_example_has_no_instance_fingerprint():
    """config.example.json must be a clean generic template (no nonlinear/Users)."""
    repo = Path(__file__).resolve().parent.parent
    example = repo / "config.example.json"
    if not example.exists():
        return
    text = example.read_text()
    assert "nonlinear" not in text
    assert "/Users/" not in text
    assert "/app/books" not in text


def test_mcp_tool_description_has_no_instance_book_count():
    """MCP tool descriptions are published to every client via list_tools(); they
    must NOT hardcode instance metadata (e.g. a fixed book count from the source
    library). Description must be functional/generic, not a claim about a
    specific corpus. (Round 7 finding: mcp_server_faiss.py had "290 books".)"""
    repo = Path(__file__).resolve().parent.parent
    mcp = repo / "engine" / "scripts" / "mcp_server_faiss.py"
    src = mcp.read_text()
    assert "290" not in src, \
        "mcp_server_faiss.py must not hardcode the source library's book count"
    # Tool descriptions must not promise a numeric corpus size.
    import re
    assert not re.search(r"across\s+\d+\s+books", src, re.IGNORECASE)


def test_compose_allows_multi_instance_coexistence():
    """PV-3 find: two instances of the product must be able to coexist on one
    machine without sharing container identity, volumes or data (unless
    explicitly configured). The compose must NOT force a fixed global
    container_name (which made a clean-room instance reuse/collide with the
    real instance's name and mount). Instead the container name derives from
    the compose project (per directory), and corpus + model volumes and the
    host port are parametrizable so each instance is isolated."""
    repo = Path(__file__).resolve().parent.parent
    compose = repo / "docker-compose.yml"
    text = compose.read_text()
    # No hardcoded bare container_name declaration (only per-project naming).
    # A comment may mention it; rule is NO real YAML key `container_name:` in
    # the service (a comment/mere word is fine).
    import re as _re
    assert not _re.search(r"^\s*container_name:\s*\$", text, _re.M), \
        "compose must not force a fixed container_name (breaks coexistence)"
    # Corpus and model mounts must be env-parametrizable (LIBRARY_ROOT,
    # LIBRARIAN_MODELS_DIR) so instances don't share data unless configured.
    assert "LIBRARY_ROOT" in text
    assert "LIBRARIAN_MODELS_DIR" in text
    # Host port must be parametrizable so instances don't collide.
    assert "LIBRARIAN_READER_PORT" in text or "READER_PORT" in text
    # PV-4: the ports mapping must map external to the SAME var as internal
    # (READER_PORT is the uvicorn listen port injected into the container). If
    # the internal side were pinned to a fixed 8088 while READER_PORT changed,
    # an override would leave host -> dead internal port.
    assert "${LIBRARIAN_READER_PORT:-8088}:${LIBRARIAN_READER_PORT:-8088}" in text, \
        "compose ports must map host:container to the SAME port var (PV-4)"
    # The compose must force OFFLINE out only at steady state; first-boot
    # download is handled by the entrypoint (allow online there).
    assert "TRANSFORMERS_OFFLINE=1" in text  # steady-state offline is intended


def test_v6_indexer_writes_book_registry():
    """PV-6: the indexer that runs on first boot (indexer_v6, via init_index)
    must generate book_registry.json alongside faiss.index + metadata.json.
    Without it the reader/citation layer (reader, /books/{id}.epub, /api/books)
    is dead (resolves book_id against the registry) while retrieval works."""
    repo = Path(__file__).resolve().parent.parent
    v6 = (repo / "engine/scripts/indexer_v6.py").read_text()
    # The v6 indexer (which init_index actually invokes) must define and call
    # a book-registry save after writing the FAISS index.
    assert "def save_book_registry" in v6
    assert "save_book_registry(state)" in v6
    # And it must call it in the main index path (not just be defined).
    idx = v6.find("def index_incremental")
    body = v6[idx:]
    assert "save_faiss_and_metadata" in body
    assert "save_book_registry(state)" in body


def test_mcp_requirement_matches_code_api():
    """PV-5: the mcp SDK dependency must not float across the API break.
    mcp_server_faiss.py targets the pre-2.0 Server API (@app.list_tools,
    stdio_server). An unpinned '>=0.1.0' resolved to mcp 2.x where FastMCP->
    MCPServer and Server lost list_tools -> server failed at import. The
    requirement must be pinned to the v1 API the code uses (with reason)."""
    repo = Path(__file__).resolve().parent.parent
    reqs = (repo / "engine/requirements.txt").read_text()
    mcp_req = [l for l in reqs.splitlines() if l.strip().startswith("mcp")]
    assert mcp_req, "requirements must declare mcp"
    line = mcp_req[0]
    assert "<2" in line or "==" in line, \
        "mcp requirement must be pinned below 2.x (code targets the v1 Server API)"
    # The stdio server code must actually be present to target.
    mcp_src = (repo / "engine/scripts/mcp_server_faiss.py").read_text()
    assert "stdio_server" in mcp_src  # uses the v1 stdio API

def test_mcp_reader_url_matches_served_route():
    """PV-7: the reader deep-link that the MCP stdio server emits must point at
    a route the product ACTUALLY serves.

    Bug: mcp_server_faiss.py built every reader_url with prefix `/book/{book_id}`,
    but no `/book` route exists — the canonical route served is
    `/reader/{book_id}` (engine/reader/routes.py). A Consumer following the MCP
    stdio link got a dead 404 on corroboration.

    This test ties the URL producer (MCP stdio) to the served route (reader
    router): the MCP must emit `/reader/...` and must NOT emit `/book/...`."""
    repo = Path(__file__).resolve().parent.parent
    mcp_src = (repo / "engine/scripts/mcp_server_faiss.py").read_text()
    routes_src = (repo / "engine/reader/routes.py").read_text()

    # The route the product serves (authoritative) — keep this canonical.
    assert '@router.get("/reader/{book_id}"' in routes_src, \
        "reader/routes.py must serve /reader/{book_id} (canonical route)"

    # The MCP stdio server must generate reader URLs against /reader/ ...
    assert "/reader/{book_id}" in mcp_src, \
        "mcp_server_faiss.py must emit reader_url with prefix /reader/{book_id}"
    # ... and must NOT emit /book/{book_id} (the bug) nor any /book/ prefix.
    assert "/book/" not in mcp_src, \
        "mcp_server_faiss.py must not emit /book/... URLs (no such served route)"

    # Anchor preservation: the epub reader deep-link must keep #href=&t= so the
    # reader can open the exact source span (PV-7 fix keeps these intact).
    assert "#href=" in mcp_src and "#p=" in mcp_src
    assert "#href={href_param}&t={t_param}" in mcp_src, \
        "epub reader_url must preserve #href=...&t=... anchor (PV-7)"


if __name__ == "__main__":
    try:
        import pytest
        sys.exit(pytest.main([__file__, "-v"]))
    except ImportError:
        passed = failed = 0
        for name in sorted(dir()):
            if name.startswith("test_"):
                fn = globals()[name]
                if callable(fn):
                    try:
                        fn()
                        print(f"PASS: {name}")
                        passed += 1
                    except Exception as e:
                        print(f"FAIL: {name}: {e}")
                        import traceback; traceback.print_exc()
                        failed += 1
        print(f"\n=== {passed} passed, {failed} failed ===")
        sys.exit(1 if failed else 0)
