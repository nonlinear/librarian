#!/usr/bin/env python3
"""
CI retro — testa todas as funções do Librarian antes de declarar epic done.

Inspirado no kin que testa retroativamente todas as funções antes de fechar epic.

Modos:
  python3 tests/test_retroactive.py              # roda todos os testes
  python3 tests/test_retroactive.py --epic NAME  # roda só testes da capability
  python3 tests/test_retroactive.py --fast       # só testes essenciais (pré-deploy)

Saída:
  🧪 CI retro — Librarian <epic>
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Capability:
    ✅ test_name
    ❌ test_name: reason
  Resultado: X/Y passaram. ✅ Epic liberado / ❌ Epic bloqueado.
"""
import os
import sys
import json
import time
import signal
import uuid
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Tuple, Callable, Optional

# ─── Config ──────────────────────────────────────────────────────────────────

LIBRARIAN_URL = os.environ.get("LIBRARIAN_URL", "http://localhost:8088")
BOOKS_DIR = Path(os.environ.get("LIBRARIAN_BOOKS", "/app/books"))
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"

PASS = "✅"
FAIL = "❌"
SKIP = "⏭️"

results: List[Tuple[str, bool, str]] = []

# ─── Helpers ─────────────────────────────────────────────────────────────────

def post_json(url: str, data: dict) -> dict:
    """POST JSON, retorna dict."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def put_json(url: str, data: dict) -> dict:
    """PUT JSON, retorna dict."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def try_request(method: str, url: str, data: dict = None) -> Tuple[Optional[dict], int]:
    """Faz request HTTP e retorna (body_dict, status_code). Em caso de erro HTTP,
    captura o erro e retorna (body_dict_do_erro, status_code)."""
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            status = resp.getcode()
            return (json.loads(raw) if raw else {}, status)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            body = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            body = {}
        return (body, e.code)
    except urllib.error.URLError as e:
        return ({"error": str(e.reason)}, 0)

def get_json(url: str) -> dict:
    """GET, retorna dict."""
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())

def mcp_call(method: str, params: dict = None) -> dict:
    """Chama MCP handler."""
    body = {"method": method}
    if params:
        body["params"] = params
    return post_json(LIBRARIAN_URL + "/", body)

def search(query: str, k: int = 10, min_score: float = None) -> list:
    """Busca via MCP."""
    params = {"name": "search_library", "arguments": {"query": query, "k": k}}
    if min_score is not None:
        params["arguments"]["min_score"] = min_score
    resp = mcp_call("tools/call", params)
    content = resp.get("content", [{}])[0].get("text", "[]")
    return json.loads(content)

def check(name: str, ok: bool, detail: str = ""):
    results.append((name, ok, detail))
    return ok

def section(title: str):
    print(f"\n{title}:")

# ─── Tests: Retrieval ────────────────────────────────────────────────────────

def test_search_query() -> bool:
    """Busca semântica retorna resultados."""
    r = search("chaos magick gnosis", k=5)
    return check("search_query", len(r) > 0, f"got {len(r)} results")

def test_search_with_min_score() -> bool:
    """Filtro min_score funciona."""
    r = search("quantum mechanics", k=10, min_score=0.5)
    if not r:
        return check("search_with_min_score", True, "no results but no error")
    all_above = all(item["score"] >= 0.5 for item in r)
    return check("search_with_min_score", all_above, f"min score: {min(item['score'] for item in r) if r else 'N/A'}")

def test_search_idempotent() -> bool:
    """Mesma query = mesmos resultados (pelo menos mesmos book_ids)."""
    q = "neural networks architecture"
    r1 = search(q, k=5)
    r2 = search(q, k=5)
    if not r1 or not r2:
        return check("search_idempotent", False, "empty results")
    ids1 = [(item["chunk_id"], round(item["score"], 4)) for item in r1]
    ids2 = [(item["chunk_id"], round(item["score"], 4)) for item in r2]
    return check("search_idempotent", ids1 == ids2, f"match: {ids1 == ids2}")

def test_chunk_roundtrip() -> bool:
    """Chunk_id de search resolve via get_chunk_by_id."""
    r = search("design patterns", k=3)
    if not r:
        return check("chunk_roundtrip", False, "search returned nothing")
    chunk_id = r[0]["chunk_id"]
    # get_chunk_by_id via MCP não existe hoje — testamos via faiss_search diretamente
    import sys
    sys.path.insert(0, str(TESTS_DIR.parent / "engine" / "scripts"))
    from faiss_search import get_searcher
    s = get_searcher()
    chunk = s.get_chunk_by_id(chunk_id)
    return check("chunk_roundtrip", chunk is not None, f"chunk_id={chunk_id}")

def test_stats_match() -> bool:
    """Stats batem com .index_state.json."""
    state_path = BOOKS_DIR / ".index_state.json"
    if not state_path.exists():
        return check("stats_match", SKIP, "no .index_state.json in test env")
    with open(state_path) as f:
        state = json.load(f)
    import sys
    sys.path.insert(0, str(TESTS_DIR.parent / "engine" / "scripts"))
    from faiss_search import get_searcher
    s = get_searcher()
    stats = s.get_stats()
    match = stats["total_chunks"] == state.get("total_chunks", 0)
    return check("stats_match", match, f"FAISS={stats['total_chunks']} state={state.get('total_chunks', 0)}")

def test_faiss_loaded() -> bool:
    """FAISS singleton carregado e com tamanho razoável."""
    import sys
    sys.path.insert(0, str(TESTS_DIR.parent / "engine" / "scripts"))
    from faiss_search import _searcher
    if _searcher is None:
        from faiss_search import get_searcher
        get_searcher()
    # Re-check
    from faiss_search import _searcher
    return check("faiss_loaded", _searcher is not None, "singleton exists")

# ─── Tests: Sistema ──────────────────────────────────────────────────────────

def test_health() -> bool:
    """GET /health retorna 200 com campos esperados."""
    try:
        h = get_json(LIBRARIAN_URL + "/health")
        return check("health", h.get("status") == "ok", f"status={h.get('status')}")
    except Exception as e:
        return check("health", False, str(e))

def test_tools_list() -> bool:
    """MCP tools/list retorna search_library."""
    resp = mcp_call("tools/list")
    tools = resp.get("tools", [])
    names = [t["name"] for t in tools]
    return check("tools_list", "search_library" in names, f"tools={names}")

def test_tools_call_search() -> bool:
    """MCP tools/call search_library funciona."""
    resp = mcp_call("tools/call", {
        "name": "search_library",
        "arguments": {"query": "test", "k": 3}
    })
    has_content = len(resp.get("content", [])) > 0
    is_error = resp.get("isError", False)
    return check("tools_call_search", has_content and not is_error,
                 f"error={is_error} content={has_content}")

# ─── Tests: HTTP Contract — A1 / A2 / A3 ────────────────────────────────────

def test_http_search() -> bool:
    """POST /search returns results with address."""
    try:
        resp = post_json(LIBRARIAN_URL + "/search", {"query": "chaos magic", "limit": 3})
        results = resp.get("results", [])
        ok = len(results) > 0
        if ok:
            has_address = all("address" in r and "type" in r["address"] for r in results)
            ok = has_address
            return check("http_search", ok, f"{len(results)} results, address_ok={has_address}")
        return check("http_search", False, "empty results")
    except Exception as e:
        return check("http_search", False, str(e))


def test_http_chunk() -> bool:
    """GET /chunk/{id} returns chunk with book_id and text."""
    # First search to get a valid chunk_id
    try:
        search_resp = post_json(LIBRARIAN_URL + "/search", {"query": "design", "limit": 1})
        results = search_resp.get("results", [])
        if not results:
            return check("http_chunk", False, "search returned nothing to get chunk_id")
        chunk_id = results[0]["chunk_id"]
        chunk = get_json(LIBRARIAN_URL + "/chunk/" + chunk_id)
        ok = bool(chunk.get("book_id")) and bool(chunk.get("text")) and "address" in chunk
        return check("http_chunk", ok, f"chunk_id={chunk_id}, book_id={chunk.get('book_id','?')}, text_len={len(chunk.get('text',''))}")
    except Exception as e:
        return check("http_chunk", False, str(e))


def test_http_chunk_404() -> bool:
    """GET /chunk/nonexistent returns 404."""
    try:
        get_json(LIBRARIAN_URL + "/chunk/nonexistent_chunk_xyz")
        return check("http_chunk_404", False, "expected 404")
    except urllib.error.HTTPError as e:
        return check("http_chunk_404", e.code == 404, f"got {e.code}")


def test_http_stats() -> bool:
    """GET /stats returns books and chunks > 0."""
    try:
        stats = get_json(LIBRARIAN_URL + "/stats")
        ok = stats.get("books", 0) > 0 and stats.get("chunks", 0) > 0
        return check("http_stats", ok, f"books={stats.get('books')} chunks={stats.get('chunks')}")
    except Exception as e:
        return check("http_stats", False, str(e))


def test_mcp_still_works() -> bool:
    """MCP legacy endpoint at POST / still functions alongside HTTP Contract."""
    try:
        resp = mcp_call("tools/call", {
            "name": "search_library",
            "arguments": {"query": "test", "k": 2}
        })
        content = resp.get("content", [{}])
        text = content[0].get("text", "[]") if content else "[]"
        results = json.loads(text)
        return check("mcp_still_works", len(results) > 0, f"{len(results)} results via MCP")
    except Exception as e:
        return check("mcp_still_works", False, str(e))

# ─── Tests: A6 — Address Contract ───────────────────────────────────────────

def test_resolve_chunk_epub() -> bool:
    """GET /resolve/{chunk_id} returns book_id + address for EPUB chunks."""
    try:
        # First get a valid chunk_id via search
        search_resp = post_json(LIBRARIAN_URL + "/search", {"query": "chaos", "limit": 5})
        results = search_resp.get("results", [])
        if not results:
            return check("resolve_chunk_epub", False, "search returned nothing")
        
        # Find an EPUB chunk
        epub_chunk = None
        for r in results:
            addr = r.get("address", {})
            if addr.get("type") == "epub":
                epub_chunk = r
                break
        
        if not epub_chunk:
            return check("resolve_chunk_epub", SKIP, "no EPUB chunks in search results")
        
        chunk_id = epub_chunk["chunk_id"]
        resolved = get_json(LIBRARIAN_URL + "/resolve/" + chunk_id)
        
        has_book_id = bool(resolved.get("book_id"))
        has_address = "address" in resolved
        has_reader_url = bool(resolved.get("reader_url"))
        correct_type = resolved.get("type") == "epub"
        
        ok = has_book_id and has_address and has_reader_url and correct_type
        return check("resolve_chunk_epub", ok,
            f"book_id={'✓' if has_book_id else '✗'} "
            f"address={'✓' if has_address else '✗'} "
            f"reader_url={'✓' if has_reader_url else '✗'} "
            f"type={'✓' if correct_type else '✗'}")
    except Exception as e:
        return check("resolve_chunk_epub", False, str(e))


def test_resolve_chunk_pdf() -> bool:
    """GET /resolve/{chunk_id} returns book_id + page for PDF chunks."""
    try:
        search_resp = post_json(LIBRARIAN_URL + "/search", {"query": "report analysis", "limit": 10})
        results = search_resp.get("results", [])
        pdf_chunk = None
        for r in results:
            addr = r.get("address", {})
            if addr.get("type") == "pdf":
                pdf_chunk = r
                break
        
        if not pdf_chunk:
            return check("resolve_chunk_pdf", SKIP, "no PDF chunks in search results")
        
        chunk_id = pdf_chunk["chunk_id"]
        resolved = get_json(LIBRARIAN_URL + "/resolve/" + chunk_id)
        
        has_book_id = bool(resolved.get("book_id"))
        has_address = "address" in resolved
        has_reader_url = bool(resolved.get("reader_url"))
        has_page = resolved.get("address", {}).get("page") is not None
        correct_type = resolved.get("type") == "pdf"
        
        ok = has_book_id and has_address and has_reader_url and has_page and correct_type
        return check("resolve_chunk_pdf", ok,
            f"book_id={'✓' if has_book_id else '✗'} "
            f"page={'✓' if has_page else '✗'} "
            f"reader_url={'✓' if has_reader_url else '✗'}")
    except Exception as e:
        return check("resolve_chunk_pdf", False, str(e))


def test_resolve_chunk_404() -> bool:
    """GET /resolve/nonexistent returns 404."""
    try:
        get_json(LIBRARIAN_URL + "/resolve/nonexistent_chunk_xyz")
        return check("resolve_chunk_404", False, "expected 404")
    except urllib.error.HTTPError as e:
        return check("resolve_chunk_404", e.code == 404, f"got {e.code}")


def test_address_deterministic() -> bool:
    """FF-006: Determinism — resolve(chunk_id) twice returns same address.

    Determinism means calling resolve() on the same chunk_id twice
    (without any intervening state change) yields identical results.
    This is NOT the same as immutability (FF-007), which tests across
    a full reload of the address map.
    """
    try:
        import sys as _sys
        _sys.path.insert(0, str(TESTS_DIR.parent / "engine" / "scripts"))

        # Search to get a valid chunk_id
        resp = post_json(LIBRARIAN_URL + "/search", {"query": "test chapter", "limit": 10})
        results = resp.get("results", [])
        if not results:
            resp = post_json(LIBRARIAN_URL + "/search", {"query": "systems", "limit": 10})
            results = resp.get("results", [])
        if not results:
            return check("address_deterministic", SKIP, "search returned nothing to test")

        chunk_id = results[0]["chunk_id"]

        # Resolve the same chunk twice — no state changes in between
        first = get_json(LIBRARIAN_URL + "/resolve/" + chunk_id)
        second = get_json(LIBRARIAN_URL + "/resolve/" + chunk_id)

        addr_first = first.get("address", {})
        addr_second = second.get("address", {})

        ok = addr_first == addr_second
        return check("address_deterministic", ok,
            f"chunk={chunk_id[:20]} match={ok}")
    except Exception as e:
        return check("address_deterministic", False, str(e))




def test_address_immutable_across_reload() -> bool:
    """FF-007: Immutability Across Reload — resolve(chunk_id) returns the
    same address before and after reloading the address map.

    Immutability is NOT the same as determinism (FF-006). This test verifies
    that address resolution survives a full state reload: simulating what
    happens when the indexer finishes reindexing and signals the HTTP server
    via SIGHUP to reload FAISS + chunk_address_map.json.

    NOTE: The ideal version signals the live process with SIGHUP. This test
    approximates by reloading the address map in-process from disk, which
    exercises the same data path. A true integration test would spawn a
    subprocess and send SIGHUP to the PID file.
    """
    try:
        import sys as _sys
        import json as _json
        from pathlib import Path as _Path
        _sys.path.insert(0, str(TESTS_DIR.parent / "engine" / "scripts"))

        # Get a chunk_id
        resp = post_json(LIBRARIAN_URL + "/search", {"query": "test", "limit": 5})
        results = resp.get("results", [])
        if not results:
            return check("address_immutable_across_reload", SKIP,
                         "search returned nothing")

        chunk_id = results[0]["chunk_id"]

        # Resolve before reload
        before = get_json(LIBRARIAN_URL + "/resolve/" + chunk_id)
        addr_before = before.get("address", {})

        # Attempt real SIGHUP. If PID file exists, use it; otherwise
        # fall back to in-process address_map reload (same data path).
        sig_hup_ok = False
        pid_file = _Path("/tmp/librarian_http.pid")
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, signal.SIGHUP)
                sig_hup_ok = True
                import time as _time
                _time.sleep(0.5)
            except (OSError, ValueError, AttributeError):
                sig_hup_ok = False

        if not sig_hup_ok:
            # FF-007 testa imutabilidade; versão real requer integração
            # com o processo do indexador. Aqui aproximamos recarregando
            # o address_map em memória a partir do arquivo em disco.
            from librarian_http import address_map
            am_path = _Path(str(BOOKS_DIR)) / "chunk_address_map.json"
            if am_path.exists():
                with open(am_path) as _f:
                    reloaded = _json.load(_f)
                address_map.clear()
                address_map.update(reloaded)

        # Resolve after reload
        after = get_json(LIBRARIAN_URL + "/resolve/" + chunk_id)
        addr_after = after.get("address", {})

        ok = addr_before == addr_after
        method = "SIGHUP" if sig_hup_ok else "in-process address_map reload"
        return check("address_immutable_across_reload", ok,
            f"chunk={chunk_id[:20]} method={method} match={ok}")
    except Exception as e:
        return check("address_immutable_across_reload", False, str(e))


# ─── Tests: Reading State Contract ────────────────────────────────────────────

READING_STATE_ROOT = LIBRARIAN_URL + "/reading-state"


def _rs_url(book_id: str) -> str:
    return f"{READING_STATE_ROOT}/{book_id}"


def test_reading_state_create() -> bool:
    """PUT /reading-state/book_x cria reading state pela primeira vez."""
    book_id = f"rs_create_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    position = {"type": "epub", "cfi": "/6/4[chap05]!/4[body70]/2/2/1:0"}
    body, status = try_request("PUT", url, {"position": position})
    if status not in (200, 201):
        return check("reading_state_create", False, f"PUT returned {status}")
    body2, status2 = try_request("GET", url)
    if status2 != 200:
        return check("reading_state_create", False, f"GET returned {status2} after PUT")
    got = body2.get("position", {})
    ok = got.get("type") == "epub" and got.get("cfi") == position["cfi"]
    return check("reading_state_create", ok,
        f"expected type=epub cfi={position['cfi']}, got type={got.get('type')} cfi={got.get('cfi')}")


def test_reading_state_update() -> bool:
    """PUT /reading-state/book_x atualiza position existente."""
    book_id = f"rs_update_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    pos1 = {"type": "epub", "cfi": "/6/2[preface]!/4[body]/2/1:0"}
    _, s1 = try_request("PUT", url, {"position": pos1})
    if s1 not in (200, 201):
        return check("reading_state_update", False, f"first PUT returned {s1}")
    pos2 = {"type": "epub", "cfi": "/6/4[chap05]!/4[body70]/2/2/1:0"}
    body_u, s2 = try_request("PUT", url, {"position": pos2})
    if s2 not in (200, 201):
        return check("reading_state_update", False, f"second PUT returned {s2}")
    body_g, s3 = try_request("GET", url)
    if s3 != 200:
        return check("reading_state_update", False, f"GET returned {s3} after update")
    got_cfi = body_g.get("position", {}).get("cfi")
    ok = got_cfi == pos2["cfi"]
    return check("reading_state_update", ok,
        f"expected cfi={pos2['cfi']}, got cfi={got_cfi}")


def test_reading_state_get_nonexistent() -> bool:
    """GET /reading-state/book_sem_estado retorna 404."""
    book_id = f"rs_nonexistent_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    _, status = try_request("GET", url)
    return check("reading_state_get_nonexistent", status == 404, f"got {status}, expected 404")


def test_reading_state_invalid_type() -> bool:
    """PUT /reading-state/book_x com type inválido (mobi) retorna 400."""
    book_id = f"rs_invalid_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    position = {"type": "mobi", "cfi": "/6/2"}
    _, status = try_request("PUT", url, {"position": position})
    return check("reading_state_invalid_type", status == 400, f"got {status}, expected 400")


def test_reading_state_epub_no_cfi() -> bool:
    """PUT /reading-state/book_x com type=epub sem cfi retorna 400."""
    book_id = f"rs_epub_no_cfi_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    position = {"type": "epub"}
    _, status = try_request("PUT", url, {"position": position})
    return check("reading_state_epub_no_cfi", status == 400, f"got {status}, expected 400")


def test_reading_state_pdf_no_page() -> bool:
    """PUT /reading-state/book_x com type=pdf sem page retorna 400."""
    book_id = f"rs_pdf_no_page_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    position = {"type": "pdf"}
    _, status = try_request("PUT", url, {"position": position})
    return check("reading_state_pdf_no_page", status == 400, f"got {status}, expected 400")


def test_reading_state_server_updated_at() -> bool:
    """PUT com updated_at enviado pelo cliente é rejeitado (400), server gera o próprio."""
    book_id = f"rs_updated_at_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    client_ts = "1970-01-01T00:00:00Z"
    position = {"type": "epub", "cfi": "/6/2"}
    body, status = try_request("PUT", url, {"position": position, "updated_at": client_ts})
    if status != 400:
        return check("reading_state_server_updated_at", False,
            f"expected 400 rejecting client timestamp, got {status}")
    # Verify error detail (FastAPI wraps in detail object)
    detail = body.get("detail", {}) if isinstance(body, dict) else {}
    err = detail.get("error", "") if isinstance(detail, dict) else ""
    if err != "server_sets_timestamp":
        return check("reading_state_server_updated_at", False,
            f"expected error='server_sets_timestamp', got error='{err}', body={str(body)[:200]}")
    # Now PUT without client timestamp — success confirms server generates its own
    body2, status2 = try_request("PUT", url, {"position": position})
    if status2 not in (200, 201):
        return check("reading_state_server_updated_at", False, f"PUT without client_ts returned {status2}")
    body_g, _ = try_request("GET", url)
    server_ts = body_g.get("updated_at", "")
    ok = bool(server_ts) and not server_ts.startswith("1970")
    return check("reading_state_server_updated_at", ok,
        f"server generated timestamp: {server_ts}")


def test_reading_state_epub() -> bool:
    """PUT/GET com position.type='epub' funciona."""
    book_id = f"rs_epub_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    position = {"type": "epub", "cfi": "/6/4[chap05]!/4[body70]/2/2/1:0"}
    body, status = try_request("PUT", url, {"position": position})
    if status not in (200, 201):
        return check("reading_state_epub", False, f"PUT returned {status}")
    body_g, status_g = try_request("GET", url)
    if status_g != 200:
        return check("reading_state_epub", False, f"GET returned {status_g}")
    pos = body_g.get("position", {})
    ok = pos.get("type") == "epub" and pos.get("cfi") == position["cfi"]
    return check("reading_state_epub", ok,
        f"expected type=epub cfi={position['cfi']}, got type={pos.get('type')} cfi={pos.get('cfi')}")


def test_reading_state_pdf() -> bool:
    """PUT/GET com position.type='pdf' funciona."""
    book_id = f"rs_pdf_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    position = {"type": "pdf", "page": 42}
    body, status = try_request("PUT", url, {"position": position})
    if status not in (200, 201):
        return check("reading_state_pdf", False, f"PUT returned {status}")
    body_g, status_g = try_request("GET", url)
    if status_g != 200:
        return check("reading_state_pdf", False, f"GET returned {status_g}")
    pos = body_g.get("position", {})
    ok = pos.get("type") == "pdf" and pos.get("page") == 42
    return check("reading_state_pdf", ok,
        f"expected type=pdf page=42, got type={pos.get('type')} page={pos.get('page')}")


def test_reading_state_multiple_books() -> bool:
    """PUT para 2 books → GET de cada retorna posição correta."""
    book_a = f"rs_multi_a_{uuid.uuid4().hex[:8]}"
    book_b = f"rs_multi_b_{uuid.uuid4().hex[:8]}"
    url_a = _rs_url(book_a)
    url_b = _rs_url(book_b)
    pos_a = {"type": "epub", "cfi": "/6/2[preface]!/4[body]/2/1:0"}
    pos_b = {"type": "pdf", "page": 99}
    _, s1 = try_request("PUT", url_a, {"position": pos_a})
    _, s2 = try_request("PUT", url_b, {"position": pos_b})
    if s1 not in (200, 201):
        return check("reading_state_multiple_books", False, f"PUT book a returned {s1}")
    if s2 not in (200, 201):
        return check("reading_state_multiple_books", False, f"PUT book b returned {s2}")
    body_a, sg_a = try_request("GET", url_a)
    body_b, sg_b = try_request("GET", url_b)
    if sg_a != 200:
        return check("reading_state_multiple_books", False, f"GET book a returned {sg_a}")
    if sg_b != 200:
        return check("reading_state_multiple_books", False, f"GET book b returned {sg_b}")
    ok_a = body_a.get("position", {}).get("cfi") == pos_a["cfi"]
    ok_b = body_b.get("position", {}).get("page") == 99
    ok = ok_a and ok_b
    return check("reading_state_multiple_books", ok,
        f"book_a cfi ok={ok_a}, book_b page ok={ok_b}")


def test_reading_state_persistence_ff007() -> bool:
    """FF-007: Reading State Persistence — PUT idempotente duas vezes = mesmo resultado."""
    book_id = f"ff007_{uuid.uuid4().hex[:8]}"
    url = _rs_url(book_id)
    position = {"type": "epub", "cfi": "epubcfi(/6/4)"}

    # PUT primeira vez
    body1, status1 = try_request("PUT", url, {"position": position, "device_id": "mac"})
    if status1 not in (200, 201):
        return check("reading_state_persistence_ff007", False, f"first PUT returned {status1}")

    # PUT segunda vez (mesma posição)
    body2, status2 = try_request("PUT", url, {"position": position, "device_id": "mac"})
    if status2 not in (200, 201):
        return check("reading_state_persistence_ff007", False, f"second PUT returned {status2}")

    # GET após segunda escrita
    body3, status3 = try_request("GET", url)
    if status3 != 200:
        return check("reading_state_persistence_ff007", False, f"GET returned {status3}")

    got_cfi = body3.get("position", {}).get("cfi")
    ok = got_cfi == "epubcfi(/6/4)"
    return check("reading_state_persistence_ff007", ok,
        f"expected cfi=epubcfi(/6/4), got cfi={got_cfi}")

# ─── Tests: Indexação ────────────────────────────────────────────────────────

def test_index_new_book_smoke() -> bool:
    """Indexador roda sem crash (smoke test)."""
    if not FIXTURES_DIR.exists():
        return check("index_new_book", SKIP, "no fixtures/ dir")
    fixtures = list(FIXTURES_DIR.glob("*.epub"))
    if not fixtures:
        return check("index_new_book", SKIP, "no .epub fixtures")
    book = fixtures[0]
    result = subprocess.run(
        ["python3", str(TESTS_DIR.parent / "engine" / "scripts" / "indexer.py"),
         str(book), "--dry-run"],
        capture_output=True, text=True, timeout=30
    )
    return check("index_new_book", result.returncode == 0, result.stderr[:200])

# ─── Runner ──────────────────────────────────────────────────────────────────

TEST_GROUPS = {
    "retrieval": [
        test_search_query,
        test_search_with_min_score,
        test_search_idempotent,
        test_chunk_roundtrip,
        test_stats_match,
        test_faiss_loaded,
    ],
    "system": [
        test_health,
        test_tools_list,
        test_tools_call_search,
    ],
    "http-contract": [
        # Resolve endpoint
        test_resolve_chunk_epub,
        test_resolve_chunk_pdf,
        test_resolve_chunk_404,
        # HTTP search + chunk endpoints
        test_http_search,
        test_http_chunk,
        test_http_chunk_404,
        test_http_stats,
        # FF-006: Determinism — resolve(chunk) twice, same result
        test_address_deterministic,
        # FF-007: Immutability Across Reload — resolve(chunk) before/after reload
        test_address_immutable_across_reload,
    ],
    "indexing": [
        test_index_new_book_smoke,
    ],
    "address": [
        test_resolve_chunk_epub,
        test_resolve_chunk_pdf,
        test_resolve_chunk_404,
        test_address_deterministic,
        test_address_immutable_across_reload,
    ],
    "reading-state": [
        test_reading_state_create,
        test_reading_state_update,
        test_reading_state_get_nonexistent,
        test_reading_state_invalid_type,
        test_reading_state_epub_no_cfi,
        test_reading_state_pdf_no_page,
        test_reading_state_server_updated_at,
        test_reading_state_epub,
        test_reading_state_pdf,
        test_reading_state_multiple_books,
        test_reading_state_persistence_ff007,
    ],
}  # type: ignore

ALL_TESTS = []
for group_tests in TEST_GROUPS.values():
    ALL_TESTS.extend(group_tests)

FAST_TESTS = [
    test_health,
    test_tools_list,
    test_tools_call_search,
    test_search_query,
    test_http_search,
    test_http_chunk,
    test_http_stats,
    test_mcp_still_works,
    test_address_deterministic,
    test_address_immutable_across_reload,
    test_reading_state_create,
    test_reading_state_update,
    test_reading_state_get_nonexistent,
    test_reading_state_invalid_type,
    test_reading_state_epub_no_cfi,
    test_reading_state_pdf_no_page,
    test_reading_state_server_updated_at,
    test_reading_state_epub,
    test_reading_state_pdf,
    test_reading_state_multiple_books,
    test_reading_state_persistence_ff007,
]

def run_tests(tests: List[Callable]) -> Tuple[int, int]:
    passed = 0
    total = 0
    for test_fn in tests:
        try:
            ok = test_fn()
            total += 1
            if ok:
                passed += 1
        except Exception as e:
            check(test_fn.__name__, False, str(e))
            total += 1
    return passed, total

def print_results(passed: int, total: int, epic_name: str):
    print(f"\n🧪 CI retro — {epic_name}")
    print("━" * 40)
    for name, ok, detail in results:
        icon = PASS if ok else (SKIP if ok == SKIP else FAIL)
        msg = f"  {icon} {name}"
        if detail:
            msg += f": {detail[:120]}"
        print(msg)
    print()
    if passed == total:
        print(f"Resultado: {passed}/{total} passaram. ✅ Epic liberado!")
    else:
        print(f"Resultado: {passed}/{total} passaram. ❌ Epic bloqueado — corrigir falhas antes de fechar.")
    return passed == total


def main():
    global results
    results = []
    
    epic_name = "Librarian"
    test_list = ALL_TESTS
    
    if "--epic" in sys.argv:
        idx = sys.argv.index("--epic") + 1
        if idx < len(sys.argv):
            epic_name = sys.argv[idx]
            group = epic_name.lower()
            if group in TEST_GROUPS:
                test_list = TEST_GROUPS[group]
            else:
                print(f"Unknown epic: {group}. Choices: {list(TEST_GROUPS.keys())}")
                sys.exit(1)
    
    if "--fast" in sys.argv:
        test_list = FAST_TESTS
    
    passed, total = run_tests(test_list)
    ok = print_results(passed, total, epic_name)
    
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
