#!/usr/bin/env python3
"""
Librarian Config Resolver — single source of truth for instance paths.

Boundary principle (Publication Policy P1):
    The ENGINE knows nothing about a specific instance. It receives a RESOLVED
    config and works against it. This module is the ONLY place that resolves
    paths; scripts consume `get_config()` and never hardcode instance paths.

Resolution order (highest wins):
    1. config.json (LIBRARIAN_CONFIG env or {repo_root}/config.json)
    2. Environment variables (LIBRARIAN_*)
    3. Derived defaults from library_root

Layout (generic, instance-agnostic):
    {library_root}/              ← corpus root (books, subfolders)
        faiss.index              ← FAISS index
        metadata.json            ← chunk metadata
        .index_state.json        ← incremental index state
        book_registry.json       ← book_id → path registry
        chunk_address_map.json   ← CFI address map
        no-indexing/             ← excluded books
    {models_dir}/                ← embedding model cache (default {library_root}/models)
    {reader_port}                ← reader/MCP port
    {reader_url_base}            ← public URL for deep links (default http://localhost:{port})
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# ── Defaults (product defaults, NOT instance values) ─────────────────────────
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_EMBEDDING_DIM = 384
DEFAULT_READER_PORT = 8088

# Paths that must exist even when unconfigured (dev fallback: repo-relative)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class ConfigResolver:
    """Resolves the effective Librarian config.

    Resolution: config.json > env (LIBRARIAN_*) > derived defaults.
    Everything is derived from `library_root` when possible; the engine never
    invents its own paths.
    """

    def __init__(self, library_root: Optional[str] = None,
                 config_path: Optional[str] = None, environ: Optional[Dict[str, str]] = None):
        self._environ = environ if environ is not None else os.environ
        self._raw: Dict[str, Any] = {}

        # 1. config.json — explicit path or default location
        if config_path is None:
            config_path = self._environ.get("LIBRARIAN_CONFIG", str(_REPO_ROOT / "config.json"))
        self._config_path = Path(config_path) if config_path else None
        if self._config_path and self._config_path.is_file():
            try:
                self._raw = json.loads(self._config_path.read_text())
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid config.json at {self._config_path}: {e}")

        # 2. env overrides (LIBRARIAN_*) — beat config.json? No: explicit config
        #    file wins over ambient env (env may leak from the instance).
        #    Actually: env is MORE explicit at runtime (docker -e). Order:
        #    CLI/library_root arg > env > config.json. We keep that.

        # 3. library_root — arg > env > config.json > dev fallback
        self._library_root = (
            library_root
            or self._environ.get("LIBRARIAN_BOOKS")
            or self._raw.get("library_root")
            or str(_REPO_ROOT / "books")
        )

    # ── Getters (resolved values) ────────────────────────────────────────────

    @property
    def library_root(self) -> Path:
        return Path(self._library_root)

    @property
    def corpus_path(self) -> Path:
        """Where books live. Default {library_root}/books (BYOBook mount)."""
        raw = self._raw.get("corpus_path") or self._environ.get("LIBRARIAN_CORPUS")
        if raw:
            return Path(raw)
        return self.library_root

    @property
    def models_dir(self) -> Path:
        raw = self._raw.get("models_dir") or self._environ.get("LIBRARIAN_MODELS")
        if raw:
            return Path(raw)
        return self.library_root / "models"

    @property
    def index_path(self) -> Path:
        return self.corpus_path / "faiss.index"

    @property
    def metadata_path(self) -> Path:
        return self.corpus_path / "metadata.json"

    @property
    def index_state_path(self) -> Path:
        return self.corpus_path / ".index_state.json"

    @property
    def book_registry_path(self) -> Path:
        return self.corpus_path / "book_registry.json"

    @property
    def address_map_path(self) -> Path:
        return self.corpus_path / "chunk_address_map.json"

    @property
    def no_indexing_dir(self) -> Path:
        return self.corpus_path / "no-indexing"

    @property
    def embedding_model(self) -> str:
        return (self._raw.get("embedding_model")
                or self._environ.get("LIBRARIAN_MODEL")
                or DEFAULT_EMBEDDING_MODEL)

    @property
    def embedding_dim(self) -> int:
        return int(self._raw.get("embedding_dim") or DEFAULT_EMBEDDING_DIM)

    @property
    def reader_port(self) -> int:
        raw = self._raw.get("reader_port") or self._environ.get("READER_PORT")
        return int(raw) if raw else DEFAULT_READER_PORT

    @property
    def reader_url_base(self) -> str:
        """Public base URL for reader deep links. Default: localhost:{port}.

        Instance-specific exposure (tunneling, custom domains) is configured by
        the USER — the engine never assumes a public URL.
        """
        raw = (self._raw.get("reader_url_base")
               or self._environ.get("READER_PUBLIC_URL"))
        if raw:
            return raw.rstrip("/")
        return f"http://localhost:{self.reader_port}"

    @property
    def reader_static_dir(self) -> Path:
        """Reader static assets. Generic layout: {engine}/reader/static."""
        raw = self._raw.get("reader_static_dir") or self._environ.get("READER_STATIC_DIR")
        if raw:
            return Path(raw)
        return Path(__file__).resolve().parent / "reader" / "static"

    @property
    def engine_scripts_dir(self) -> Path:
        """Directory of the engine scripts (engine/scripts)."""
        return Path(__file__).resolve().parent / "scripts"

    @property
    def reader_dir(self) -> Path:
        """Reader routes dir. Generic layout: {engine}/reader."""
        return Path(__file__).resolve().parent / "reader"

    @property
    def reader_routes_path(self) -> Path:
        return self.reader_dir / "routes.py"

    @property
    def renderer_dir(self) -> Path:
        """Response renderer package. Generic layout: {engine}/evidence_renderer."""
        return Path(__file__).resolve().parent / "evidence_renderer"

    @property
    def shared_dir(self) -> Path:
        """Shared API models (shared/). Generic layout: {engine}/shared."""
        return Path(__file__).resolve().parent / "shared"

    @property
    def raw(self) -> Dict[str, Any]:
        return self._raw

    # ── Convenience ──────────────────────────────────────────────────────────

    def ensure_dirs(self) -> None:
        """Create the instance layout dirs if missing (models, corpus/no-indexing)."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.corpus_path.mkdir(parents=True, exist_ok=True)
        self.no_indexing_dir.mkdir(parents=True, exist_ok=True)


# ── Module-level singleton (import-time cheap; resolution is lazy) ───────────
_config: Optional[ConfigResolver] = None


def get_config() -> ConfigResolver:
    global _config
    if _config is None:
        _config = ConfigResolver()
    return _config


def reset_config(library_root: Optional[str] = None) -> ConfigResolver:
    """Test hook: build a fresh resolver against an arbitrary library_root.

    Lets tests prove the engine works on a DIFFERENT path than the instance.
    """
    global _config
    _config = ConfigResolver(library_root=library_root)
    return _config