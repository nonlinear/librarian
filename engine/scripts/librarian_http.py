#!/usr/bin/env python3
"""
Librarian HTTP — persistent server on port 8088.
HTTP Contract boundary: /search, /chunk/{id}, /stats + legacy MCP at POST /.

Versioned API lives under /v1/*.
Human navigation: /reader/*, /wall, /books/*.
"""

import base64
import urllib.parse
import os, sys, json, signal, logging, threading
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
import uvicorn

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/ for config
from faiss_search import get_searcher
from sentence_transformers import SentenceTransformer
from config import get_config as _get_config

_cfg = _get_config()

# Shared API models (single source of truth) — generic layout, repo-relative
_SHARED_DIR = _cfg.shared_dir
if _SHARED_DIR.exists():
    sys.path.insert(0, str(_SHARED_DIR))
from models import Evidence, EvidenceSource, Locator, TextRange, CitationTarget
from response import ApiResponse, ok as api_ok, err as api_err, ERROR_NOT_FOUND

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("librarian-http")
logger.info(f"Shared models loaded from: {_SHARED_DIR}")

def _respond(body: dict):
    """Wrap MCP response in JSON-RPC envelope."""
    return {
        "jsonrpc": "2.0",
        "id": body.get("id", 0),
        "result": body.get("result", body)
    }

app = FastAPI(title="Librarian", version="1.0.0")

# ── Reader routes — fundido no mesmo processo ──
# Single source of truth: the static dir is resolved by the ConfigResolver
# (which already honors READER_STATIC_DIR if a user sets it). No second env read.
_reader_static = _cfg.reader_static_dir
if _reader_static.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=str(_reader_static)), name="reader_static")
    # Resolve routes.py: next to static/ (generic layout)
    _reader_routes_candidates = [
        _cfg.reader_routes_path,             # {engine}/reader/routes.py (generic)
        _reader_static.parent / "routes.py",  # fallback next to static
    ]
    _reader_routes_path = next((p for p in _reader_routes_candidates if p.exists()), None)
    if _reader_routes_path:
        import importlib.util
        _spec = importlib.util.spec_from_file_location("reader_routes", _reader_routes_path)
        if _spec and _spec.loader:
            _reader_mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_reader_mod)
            app.include_router(_reader_mod.router)
            logger.info(f"Reader routes mounted from {_reader_routes_path}")
    else:
        logger.info("Reader static dir exists but no routes.py found — serving static only")
else:
    logger.info("No reader static dir — reader routes disabled")

# Public URL for reader citations (resolved via config; default localhost)
READER_PUBLIC_URL = _cfg.reader_url_base

# ── Response Renderer ──
_renderer_path = Path(__file__).resolve().parent / "renderer.py"
if _renderer_path.exists():
    import importlib.util
    _spec = importlib.util.spec_from_file_location("renderer_routes", _renderer_path)
    if _spec and _spec.loader:
        _render_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_render_mod)
        app.include_router(_render_mod.router)
        logger.info(f"Response Renderer routes mounted from {_renderer_path}")

# ── End Reader setup ──

MODEL_NAME = _cfg.embedding_model

searcher = None
encoder = None
address_map = {}  # chunk_id → {cfi, book_id, confidence, ...}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _normalize_address(chunk: dict) -> dict:
    """Extract address from chunk source metadata.

    EPUB: returns {type, cfi (from chunk_address_map), href}
    PDF:  returns {type, page}
    """
    chunk_id = chunk.get("chunk_id", "")
    source = chunk.get("source", {})
    
    if isinstance(source, dict):
        doc_type = source.get("type", "epub")
        if doc_type == "pdf":
            return {
                "type": "pdf",
                "page": source.get("page")
            }
        
        # EPUB: check address_map for real CFI
        entry = address_map.get(chunk_id, {})
        if entry and entry.get("cfi"):
            return {
                "type": "epub",
                "cfi": entry["cfi"],
                "href": source.get("href")
            }
        return {
            "type": "epub",
            "cfi": None,
            "href": source.get("href")
        }
    return {"type": "epub", "cfi": None, "href": None}


def _normalize_chunk(chunk: dict) -> dict:
    """Normalize a raw chunk dict to Contract shape."""
    return {
        "chunk_id": chunk.get("chunk_id", ""),
        "book_id": chunk.get("book_id") or chunk.get("book_hash", ""),
        "book_title": chunk.get("book_title", ""),
        "text": chunk.get("text", ""),
        "score": chunk.get("score"),
        "address": _normalize_address(chunk),
    }


# ─── Existing endpoints (unchanged) ──────────────────────────────────────────

@app.get("/health")
async def health():
    stats = searcher.get_stats() if searcher else {"total_chunks": 0}
    return {"status": "ok", "service": "librarian-mcp", "port": 8088, "chunks": stats["total_chunks"]}

@app.post("/")
async def mcp_handler(body: dict):
    method = body.get("method", "")
    req_id = body.get("id", 0)

    if method == "initialize":
        return _respond({
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "experimental": {}
                },
                "serverInfo": {
                    "name": "librarian-http",
                    "version": "1.0.0"
                }
            }})

    if method == "notifications/initialized":
        return _respond({"id": req_id, "result": {}})

    if method == "tools/list":
        return _respond({
            "id": req_id,
            "result": {"tools": [{
                "name": "search_library",
                "description": "Semantic search across books using FAISS.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "k": {"type": "integer", "default": 10},
                        "min_score": {"type": "number"}
                    }
                }
            }]}
        })

    elif method == "tools/call":
        name = body.get("params", {}).get("name")
        args = body.get("params", {}).get("arguments", {})
        if name == "search_library":
            query = args.get("query", "")
            k = args.get("k", 10)
            try:
                vector = encoder.encode(query)
                results = searcher.search(vector, k=k)
                min_score = args.get("min_score")
                if min_score:
                    results = [r for r in results if r["score"] >= min_score]
                return _respond({
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(results)}]}
                })
            except Exception as e:
                return _respond({
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
                })

    return _respond({"id": req_id, "result": {"error": f"Unknown method: {method}"}})


# ─── HTTP Contract: A1 — Search ──────────────────────────────────────────────

from pydantic import BaseModel, Field
from typing import Optional

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    min_score: Optional[float] = None


@app.post("/search")
async def search_endpoint(req: SearchRequest):
    try:
        vector = encoder.encode(req.query)
        results = searcher.search(vector, k=req.limit)
        if req.min_score is not None:
            results = [r for r in results if r["score"] >= req.min_score]
        normalized = [_normalize_chunk(r) for r in results]
        return {"results": normalized}
    except Exception as e:
        logger.exception("search failed")
        raise HTTPException(status_code=500, detail={"error": "search_failed", "detail": str(e)})


# ─── HTTP Contract: A6 — Address Resolution ──────────────────────────────────

@app.get("/resolve/{chunk_id}")
async def resolve_address(chunk_id: str):
    """
    Resolve a chunk_id into book_id + address + reader_url.
    
    This is the key endpoint that decouples Reader from discovery.
    Reader calls this instead of searching or guessing.
    """
    if not chunk_id:
        raise HTTPException(status_code=400, detail={"error": "missing_chunk_id"})
    
    chunk = searcher.get_chunk_by_id(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail={"error": "chunk_not_found"})
    
    book_id = chunk.get("book_id") or chunk.get("book_hash", "")
    address = _normalize_address(chunk)
    address_type = address.get("type", "epub")
    cid = chunk.get("chunk_id", "")
    
    base = READER_PUBLIC_URL.rstrip("/") if READER_PUBLIC_URL else ""
    
    # Build reader_url: href + text anchor preferido, CFI como fallback
    # Motivo: CFI gerado atualmente falha no epub.js (CIP-003)
    href = address.get("href")
    cfi = address.get("cfi")
    
    # Text anchor do address_map para o fragmento de texto
    text_anchor = None
    addr_entry = address_map.get(cid, {})
    if addr_entry:
        raw = addr_entry.get("anchor_text", "")
        if raw and isinstance(raw, str) and len(raw) > 5:
            # Use first 3 words, stripped of punctuation, as text anchor
            import re
            words = re.sub(r"[^\w\s'-]", "", raw.strip()).split()
            exact = " ".join(words[:3]) if len(words) >= 3 else " ".join(words)
            text_anchor = {"exact": exact}
    
    if address_type == "epub":
        if href and text_anchor:
            fragment = f"href={href}&t={text_anchor['exact']}"
            reader_url = f"{base}/reader/{book_id}#{fragment}"
        elif cfi:
            reader_url = f"{base}/reader/{book_id}#{cfi}"
        else:
            reader_url = f"{base}/reader/{book_id}"
    elif address_type == "pdf":
        page = address.get("page")
        if page:
            reader_url = f"{base}/reader/{book_id}?page={page}"
        else:
            reader_url = f"{base}/reader/{book_id}"
    else:
        reader_url = f"{base}/reader/{book_id}"
    
    return {
        "chunk_id": chunk_id,
        "book_id": book_id,
        "book_title": chunk.get("book_title", ""),
        "type": address_type,
        "address": address,
        "reader_url": reader_url
    }


# ─── Evidence Builder (shared between resolve and search) ────────────────────

def build_evidence(chunk: dict) -> Evidence:
    """
    Build an Evidence object from a raw FAISS chunk dict.
    
    This is the single point of truth for:
      - source (book_id, chunk_id)
      - locator (href, text_range, cfi)
      - citation (label, url)
    
    Used by:
      - /v1/resolve/{id}
      - /v1/search
    """
    chunk_id = chunk.get("chunk_id", "")
    book_hash = chunk.get("book_hash", "")
    book = searcher.books.get(book_hash, {})
    book_title = book.get("title", chunk.get("book_title", ""))

    source_meta = chunk.get("source", {})
    href = source_meta.get("href", "") if isinstance(source_meta, dict) else ""

    # Extract start and end text from chunk content
    text = chunk.get("text", "")
    lines = text.strip().split("\n") if text else []
    start_text = lines[0][:80].strip() if lines else ""
    # V1: end = last line (approximation). Tomorrow: proper sentence boundary.
    end_text = lines[-1][:80].strip() if len(lines) > 1 else ""

    # Build locator with text_range(start, end)
    locator = Locator(
        href=href,
        text_range=TextRange(start=start_text, end=end_text),
        cfi=None,  # Added when CIP-003 resolves
    )

    # Build citation target
    # V1 URL: uses #locator=<base64url> for robust encoding.
    # Backward-compatible: legacy #href=...&start=...&end=... still works.
    base = READER_PUBLIC_URL.rstrip("/") if READER_PUBLIC_URL else ""

    # Build locator JSON and base64-encode it
    locator_json = {
        "href": href,
        "text_range": {
            "start": start_text,
            "end": end_text,
        },
    }
    if locator.cfi:
        locator_json["cfi"] = locator.cfi

    locator_encoded = base64.urlsafe_b64encode(
        json.dumps(locator_json, separators=(",", ":")).encode("utf-8")
    ).decode("utf-8").rstrip("=")
    # urlsafe_b64encode output is already URL-safe; strip trailing = to avoid encoding issues
    target_url = f"{base}/reader/{book_hash}#locator={locator_encoded}"

    label_text = text.strip()[:60] if text else book_title
    citation_label = f"{book_title} — {label_text}"

    return Evidence(
        evidence_id=f"ev_{chunk_id}",
        source=EvidenceSource(book_id=book_hash, chunk_id=chunk_id),
        locator=locator,
        citation=CitationTarget(label=citation_label, url=target_url),
    )


# ─── HTTP Contract V1 — Resolve ──────────────────────────────────────────────

@app.get("/v1/resolve/{chunk_id}")
async def v1_resolve(chunk_id: str) -> ApiResponse:
    if not chunk_id:
        return api_err("INVALID_ARGUMENT", "chunk_id is required")
    chunk = searcher.get_chunk_by_id(chunk_id)
    if chunk is None:
        return api_err("NOT_FOUND", f"Chunk not found: {chunk_id}")
    ev = build_evidence(chunk)
    # V1 envelope: citation.target.url (D1: URL é projeção)
    data = ev.model_dump()
    data["citation"] = {
        "label": ev.citation.label,
        "target": {"url": ev.citation.url},
    }
    return api_ok(data)


# ─── HTTP Contract V1 — Search ───────────────────────────────────────────────

from pydantic import BaseModel, Field


class CitationTargetNested(BaseModel):
    """Citation representation com target.url aninhado.
    
    Diferente do CitationTarget (que tem url plana),
    este aninha target.url como projeção separada do conteúdo.
    """
    label: str
    target: dict = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class SearchEvidenceResult(BaseModel):
    """Single search result: Evidence with score.
    
    - text: original chunk text (para Renderer)
    - score: similarity score (0-1)
    - source, locator alinhados com /v1/resolve
    - citation com target.url (não url plana) por consistência com D1
    """
    evidence_id: str
    source: EvidenceSource
    text: str
    locator: Locator
    citation: CitationTargetNested
    score: float

    model_config = {"extra": "forbid"}


class V1SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    min_score: float | None = None


class V1SearchData(BaseModel):
    """Search response envelope."""
    query: str
    results: list[SearchEvidenceResult]
    total: int

    model_config = {"extra": "forbid"}


@app.post("/v1/search")
async def v1_search(req: V1SearchRequest) -> ApiResponse:
    """
    Search → Evidence[].

    Retrieval primitive: query → Evidence collection.
    Returns structured results, not formatted text — Renderer/Agency decide presentation.

    Same search engine (/search), different envelope.
    """
    if not req.query:
        return api_err("INVALID_ARGUMENT", "query is required")

    try:
        vector = encoder.encode(req.query)
        raw = searcher.search(vector, k=req.limit)
        if req.min_score is not None:
            raw = [r for r in raw if r["score"] >= req.min_score]
    except Exception as e:
        logger.exception("search failed")
        return api_err("INTERNAL", str(e))

    results = []
    for r in raw:
        ev = build_evidence(r)
        results.append(SearchEvidenceResult(
            evidence_id=ev.evidence_id,
            source=ev.source,
            text=r.get("text", ""),
            locator=ev.locator,
            citation=CitationTargetNested(
                label=ev.citation.label,
                target={"url": ev.citation.url},
            ),
            score=r.get("score", 0),
        ))

    return api_ok(V1SearchData(
        query=req.query,
        results=results,
        total=len(results),
    ))




# ─── HTTP Contract V1 — Health ───────────────────────────────────────────────

@app.get("/v1/health")
async def v1_health() -> ApiResponse:
    stats = searcher.get_stats() if searcher else {"total_chunks": 0, "total_books": 0, "dimensions": 0, "index_type": "not_loaded"}
    
    # Corpus: count books on disk
    corpus_count = 0
    try:
        for ext in ("*.epub", "*.pdf"):
            corpus_count += len(list(BOOKS_DIR.glob(ext)))
    except Exception:
        pass
    
    index_healthy = stats["total_chunks"] > 1000
    search_healthy = index_healthy
    reader_healthy = True
    
    if index_healthy and search_healthy:
        overall = "healthy"
    else:
        overall = "degraded"
    
    return api_ok({
        "status": overall,
        "service": "librarian",
        "version": "1.0.0",
        "reader": "healthy" if reader_healthy else "unavailable",
        "corpus": {
            "books": corpus_count,
            "accessible": corpus_count,
        },
        "index": {
            "status": "healthy" if index_healthy else "degraded",
            "chunks": stats["total_chunks"],
            "books_indexed": stats["total_books"],
        },
        "search": "healthy" if search_healthy else "unavailable",
    })


# ─── HTTP Contract: A2 — Chunk ───────────────────────────────────────────────

@app.get("/chunk/{chunk_id}")
async def get_chunk(chunk_id: str):
    if not chunk_id:
        raise HTTPException(status_code=400, detail={"error": "missing_chunk_id"})
    chunk = searcher.get_chunk_by_id(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail={"error": "chunk_not_found"})
    return _normalize_chunk(chunk)


# ─── HTTP Contract: A3 — Stats ───────────────────────────────────────────────

@app.get("/stats")
async def get_stats():
    stats = searcher.get_stats()
    return {
        "books": stats["total_books"],
        "chunks": stats["total_chunks"],
        "embedding_model": MODEL_NAME,
        "index_version": "",
        "dimensions": stats["dimensions"],
    }

BOOKS_DIR = _cfg.corpus_path

# ─── Reading State ────────────────────────────────────────────────────────────

# Storage: reading_state.json lives in the corpus (instance-agnostic)
READING_STATE_PATH = _cfg.corpus_path / "reading_state.json"
_reading_state: dict[str, dict] = {}  # keyed by "{user_id}:{book_id}"
_reading_state_lock = threading.Lock()
_READING_STATE_INITIALIZED = False

VALID_POSITION_TYPES = {"epub", "pdf"}


def _load_reading_state():
    """Load reading state from reading_state.json. Initializes empty if missing."""
    global _reading_state, _READING_STATE_INITIALIZED
    if READING_STATE_PATH.exists():
        try:
            with open(READING_STATE_PATH) as f:
                _reading_state = json.load(f)
            logger.info(f"Reading state loaded: {len(_reading_state)} entries")
        except Exception as e:
            logger.warning(f"Failed to load reading_state.json: {e}")
            _reading_state = {}
    else:
        logger.info("No reading_state.json yet — starting fresh")
        _reading_state = {}
    _READING_STATE_INITIALIZED = True


def _save_reading_state():
    """Persist reading state to reading_state.json."""
    READING_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(READING_STATE_PATH, "w") as f:
        json.dump(_reading_state, f, indent=2, sort_keys=True)
    logger.debug("Reading state saved")


class ReadingStatePosition(BaseModel):
    type: str
    cfi: Optional[str] = None
    page: Optional[int] = None


class ReadingStatePutBody(BaseModel):
    position: ReadingStatePosition
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    updated_at: Optional[str] = None  # rejected — server sets this


@app.get("/reading-state/{book_id}")
async def get_reading_state(book_id: str, user_id: str = "local"):
    """
    GET /reading-state/{book_id}

    Returns the reading state for a given book_id, or 404 if none exists.
    Optional query param: ?user_id=... (default: "local")
    """
    if not _READING_STATE_INITIALIZED:
        _load_reading_state()

    key = f"{user_id}:{book_id}"

    with _reading_state_lock:
        state = _reading_state.get(key)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "reading_state_not_found",
                "book_id": book_id,
                "user_id": user_id
            }
        )

    return state


@app.put("/reading-state/{book_id}", status_code=200)
async def put_reading_state(book_id: str, body: ReadingStatePutBody):
    """
    PUT /reading-state/{book_id}

    Upsert reading state. Only 'epub' and 'pdf' position types accepted.
    Timestamp is set server-side. user_id defaults to "local".
    """
    if not _READING_STATE_INITIALIZED:
        _load_reading_state()

    # Reject client-supplied timestamp
    if body.updated_at is not None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "server_sets_timestamp",
                "detail": "updated_at is set by the server; do not include it"
            }
        )

    # Validate position
    if body.position is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_position", "detail": "position is required"}
        )

    pos = body.position

    # Validate position type — only epub and pdf accepted
    if pos.type not in VALID_POSITION_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_position_type",
                "detail": f"Unsupported type: '{pos.type}'. Must be 'epub' or 'pdf'"
            }
        )

    # Type-specific field validation
    if pos.type == "epub":
        if not pos.cfi or not isinstance(pos.cfi, str) or pos.cfi.strip() == "":
            raise HTTPException(
                status_code=400,
                detail={"error": "missing_cfi", "detail": "position.cfi is required (non-empty string) when type is 'epub'"}
            )
    elif pos.type == "pdf":
        if pos.page is None or not isinstance(pos.page, int) or pos.page < 1:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_page", "detail": "position.page must be a positive integer when type is 'pdf'"}
            )

    # Build the position dict with the type-specific field
    pos_dict = {"type": pos.type}
    if pos.type == "epub":
        pos_dict["cfi"] = pos.cfi.strip()
    else:
        pos_dict["page"] = pos.page

    user_id = body.user_id or "local"
    device_id = body.device_id or "local"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    state = {
        "user_id": user_id,
        "book_id": book_id,
        "position": pos_dict,
        "device_id": device_id,
        "updated_at": now,
    }

    key = f"{user_id}:{book_id}"
    with _reading_state_lock:
        _reading_state[key] = state
        _save_reading_state()

    logger.info(f"Reading state updated: user={user_id}, book={book_id}, type={pos.type}, device={device_id}")

    # Return full state per contract
    return state


def _load_address_map():
    """Load chunk_address_map.json for CFI resolution."""
    global address_map
    am_path = BOOKS_DIR / "chunk_address_map.json"
    if am_path.exists():
        try:
            with open(am_path) as f:
                address_map = json.load(f)
            with_cfi = sum(1 for v in address_map.values() if isinstance(v, dict) and v.get("cfi"))
            logger.info(f"Address map loaded: {len(address_map):,} entries, {with_cfi:,} with CFI")
        except Exception as e:
            logger.warning(f"Failed to load address map: {e}")
            address_map = {}
    else:
        logger.info("No chunk_address_map.json found — CFI resolution will use null")
        address_map = {}


if __name__ == "__main__":
    logger.info(f"Loading encoder model: {MODEL_NAME}")
    encoder = SentenceTransformer(MODEL_NAME)
    logger.info("Encoder ready")
    
    logger.info("Loading FAISS index...")
    searcher = get_searcher()
    stats = searcher.get_stats()
    logger.info(f"FAISS ready: {stats['total_chunks']:,} chunks, {stats['total_books']} books, {stats['dimensions']} dims")
    
    _load_address_map()
    _load_reading_state()
    
    # Write PID so indexer can signal us on completion
    PID_FILE = Path("/tmp/librarian_http.pid")
    PID_FILE.write_text(str(os.getpid()))
    logger.info(f"PID {os.getpid()} written to {PID_FILE}")
    
    def reload_handler(signum, frame):
        global searcher, address_map
        logger.info("SIGHUP: Reloading...")
        import faiss_search
        faiss_search._searcher = None
        faiss_search._searcher_lock = threading.Lock()
        searcher = get_searcher()
        _load_address_map()
        logger.info("FAISS + Address Map reloaded")
    
    signal.signal(signal.SIGHUP, reload_handler)
    uvicorn.run(app, host="0.0.0.0", port=_cfg.reader_port, log_level="info")
