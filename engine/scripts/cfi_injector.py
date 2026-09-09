#!/usr/bin/env python3
"""
CFI Injector (CIP-3) — Alinhamento chunk → posição EPUB.

Pipeline:
1. Lê metadata.json (chunks existentes)
2. Para cada chunk, resolve book_id → path via book_registry.json
3. Localiza o parágrafo via spine_index + href + paragraph_idx
4. Computa CFI determinístico via DOM traversal
5. Salva chunk_address_map.json (SEM tocar FAISS)

Uso:
  python3 cfi_injector.py                    # processa todos os livros no metadata
  python3 cfi_injector.py --book c9e672ff    # só um livro específico
  python3 cfi_injector.py --status           # quantos chunks têm CFI vs não
"""
import os, sys, json, re, zipfile, uuid, time
from pathlib import Path
from collections import defaultdict

# Unbuffer stdout for pipe/capture
sys.stdout.reconfigure(line_buffering=True)

# Books directory — resolved via config (Boundary: engine knows no instance paths)
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/ for config
from config import get_config
_cfg = get_config()
BOOKS_DIR = _cfg.corpus_path
METADATA_PATH = _cfg.metadata_path
ADDRESS_MAP_PATH = _cfg.address_map_path
BOOK_REGISTRY_PATH = _cfg.book_registry_path


def load_metadata():
    """Load chunk registry."""
    with open(METADATA_PATH) as f:
        data = json.load(f)
    return data.get("chunks", data if isinstance(data, list) else [])


def load_book_registry():
    """Load book_registry.json — canonical source for book_id → path."""
    if not BOOK_REGISTRY_PATH.exists():
        return {}
    with open(BOOK_REGISTRY_PATH) as f:
        return json.load(f)


def load_existing_address_map():
    """Load existing CFI mappings if any."""
    if not ADDRESS_MAP_PATH.exists():
        return {}, set()
    with open(ADDRESS_MAP_PATH) as f:
        data = json.load(f)
    return data, set(data.keys())


def resolve_book_path(book_id: str, registry: dict):
    # type: (str, dict) -> Path | None
    """
    Resolve book_id → local Path using book_registry.json.
    """
    entry = registry.get(book_id)
    if not entry:
        return None

    path_str = entry["path"]
    path_obj = Path(path_str)

    # Direct hit
    if path_obj.exists():
        return path_obj

    # Rebase any stored absolute path to the current corpus, generically.
    # Stored paths may come from a prior instance layout (e.g. a container mount
    # or another host); the engine rebases them to the instance corpus without
    # assuming any specific mount point.
    if path_obj.is_absolute():
        try:
            parts = list(path_obj.parts)
            # find the ".../books/<rest>" segment and rebase onto BOOKS_DIR
            if "books" in parts:
                idx = parts.index("books")
                local = BOOKS_DIR / Path(*parts[idx + 1:])
                if local.exists():
                    return local
        except Exception:
            pass

    # File name match in books dir
    by_name = BOOKS_DIR / path_obj.name
    if by_name.exists():
        return by_name

    return None



def process_chunks(chunks, registry, existing_map, existing_keys, book_filter=None):
    """Process chunks and inject CFI using book_registry for path resolution."""
    address_map = dict(existing_map)
    stats = {"total": 0, "already_had_cfi": 0, "new_cfi": 0, "failed": 0, "skipped": 0}

    # Group chunks by book for efficient EPUB opening
    book_chunks = defaultdict(list)
    for c in chunks:
        book_id = c.get("book_hash") or c.get("book_id") or c.get("book", "")
        if not book_id:
            stats["skipped"] += 1
            continue
        chunk_id = c.get("chunk_id", c.get("id", ""))
        if not chunk_id:
            stats["skipped"] += 1
            continue
        if book_filter and book_id != book_filter:
            continue
        book_chunks[book_id].append((chunk_id, c))
        stats["total"] += 1

    print(f"📚 Books to process: {len(book_chunks)}")
    print(f"📄 Chunks to address: {stats['total']}")

    for book_id, chunk_list in book_chunks.items():
        # Resolve path using canonical book_registry
        book_path = resolve_book_path(book_id, registry)

        if not book_path:
            print(f"  ⚠️  Book {book_id}: not found in book_registry, skipping {len(chunk_list)} chunks")
            stats["failed"] += len(chunk_list)
            continue

        # Quick-check: if ALL chunks for this book already have CFI in existing_map, skip entirely
        book_fully_done = all(
            existing_map.get(cid, {}).get("cfi")
            for cid, _ in chunk_list
            if cid in existing_map
        ) and all(cid in existing_map for cid, _ in chunk_list)

        if book_fully_done:
            stats["already_had_cfi"] += len(chunk_list)
            continue

        print(f"  📖 Processing: {book_path.name} ({len(chunk_list)} chunks)")

        # ---- OPTIMIZATION: cache parsed HTML per href within this book ----
        # Group chunks by href so we parse each spine file only once
        href_chunks = defaultdict(list)
        for chunk_id, chunk in chunk_list:
            if existing_map.get(chunk_id, {}).get("cfi"):
                stats["already_had_cfi"] += 1
                continue
            source = chunk.get("source", {})
            if not source or source.get("type") != "epub":
                address_map[chunk_id] = {
                    "book_id": book_id,
                    "cfi": None,
                    "confidence": 0,
                    "anchor_text": None,
                    "source_type": "pdf",
                    "page": source.get("page")
                }
                stats["skipped"] += 1
                continue
            href = source.get("href")
            if not href:
                address_map[chunk_id] = {
                    "book_id": book_id,
                    "cfi": None,
                    "confidence": 0,
                    "anchor_text": None
                }
                stats["failed"] += 1
                continue
            href_chunks[href].append((chunk_id, chunk))

        # Open EPUB once, cache soups
        epub_cache = {}  # href -> BeautifulSoup
        try:
            import zipfile
            from bs4 import BeautifulSoup

            with zipfile.ZipFile(book_path, 'r') as z:
                all_zip_names = set(z.namelist())

                for href, h_chunks in href_chunks.items():
                    normalized = href.lstrip("/")
                    if normalized in all_zip_names:
                        content = z.read(normalized)
                    else:
                        candidates = [n for n in all_zip_names if n.endswith("/" + normalized) or n == normalized]
                        if not candidates:
                            for chunk_id, _ in h_chunks:
                                address_map[chunk_id] = {
                                    "book_id": book_id,
                                    "cfi": None,
                                    "confidence": 0,
                                    "anchor_text": None
                                }
                                stats["failed"] += 1
                            continue
                        content = z.read(candidates[0])

                    html = content.decode("utf-8", errors="replace")
                    soup = BeautifulSoup(html, "html.parser")

                    # Match indexer selector exactly: p, li, blockquote, h1, h2, h3
                    text_elements = soup.find_all(["p", "li", "blockquote", "h1", "h2", "h3"])
                    para_elements = [el for el in text_elements if el.get_text(strip=True)]
                    max_elements = len(para_elements)

                    for chunk_id, chunk in h_chunks:
                        spine_index = chunk.get("source", {}).get("spine_index")
                        paragraphs = chunk.get("paragraphs", [])
                        first_para = paragraphs[0] if paragraphs else {}
                        para_idx = first_para.get("idx") if isinstance(first_para, dict) else None

                        if para_idx is None or para_idx >= max_elements:
                            address_map[chunk_id] = {
                                "book_id": book_id,
                                "cfi": None,
                                "confidence": 0.05 if para_idx is not None else 0,
                                "anchor_text": first_para.get("text", "")[:100] if isinstance(first_para, dict) else ""
                            }
                            stats["failed"] += 1
                            continue

                        target = para_elements[para_idx]
                        anchor = target.get_text(strip=True)[:100]

                        # Build XML path for CFI
                        path_parts = []
                        current = target
                        while current and current.name not in ("body", "html"):
                            parent = current.parent
                            if parent:
                                siblings = [c for c in parent.children if hasattr(c, 'name') and c.name == current.name]
                                idx = siblings.index(current) + 1 if len(siblings) > 1 else 1
                                path_parts.append(str(idx))
                            current = parent
                        path_parts.reverse()

                        spine_offset = spine_index + 2 if spine_index is not None else 0
                        para_path = "/".join(path_parts)
                        cfi = f"epubcfi(/6/{spine_offset}!/4/{para_path})"

                        address_map[chunk_id] = {
                            "book_id": book_id,
                            "cfi": cfi,
                            "confidence": 0.95,
                            "anchor_text": anchor
                        }
                        stats["new_cfi"] += 1

        except Exception as e:
            print(f"  ⚠️  Error opening {book_path.name}: {e}")
            stats["failed"] += sum(len(v) for v in href_chunks.values())
            continue

    return address_map, stats


def compute_stats(address_map, chunks=None):
    """Compute coverage statistics broken down by EPUB and PDF."""
    total = len(address_map)

    chunk_type = {}
    if chunks:
        for c in chunks:
            cid = c.get("chunk_id", c.get("id", ""))
            src = c.get("source", {})
            st = src.get("type", "unknown")
            chunk_type[cid] = st

    def resolve_type(v, cid):
        st = v.get("source_type") or chunk_type.get(cid, "unknown")
        return st

    epub_total = 0
    epub_with_cfi = 0
    pdf_total = 0
    pdf_with_page = 0

    for cid, v in address_map.items():
        st = resolve_type(v, cid)
        if st == "pdf":
            pdf_total += 1
            if v.get("page"):
                pdf_with_page += 1
        elif v.get("cfi"):
            epub_total += 1
            epub_with_cfi += 1
        else:
            epub_total += 1

    with_cfi = sum(1 for v in address_map.values() if v.get("cfi"))
    coverage_pct = round(with_cfi / total * 100, 1) if total else 0

    return {
        "total": total,
        "with_cfi": with_cfi,
        "without_cfi": total - with_cfi,
        "coverage_pct": coverage_pct,
        "epub": {
            "total": epub_total,
            "with_cfi": epub_with_cfi,
            "coverage_pct": round(epub_with_cfi / epub_total * 100, 1) if epub_total else 0
        },
        "pdf": {
            "total": pdf_total,
            "with_page": pdf_with_page,
            "coverage_pct": round(pdf_with_page / pdf_total * 100, 1) if pdf_total else 0
        }
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIP-3 CFI Injector (book_registry)")
    parser.add_argument("--book", help="Process only one book hash")
    parser.add_argument("--status", action="store_true", help="Show coverage stats only")
    args = parser.parse_args()

    print("=" * 50)
    print("CIP-3: CFI Injection Layer (book_registry)")
    print("=" * 50)

    print("\n📂 Loading data...")
    chunks = load_metadata()
    registry = load_book_registry()
    existing_map, existing_keys = load_existing_address_map()

    print(f"   Chunks in metadata:       {len(chunks):,}")
    print(f"   Books in registry:        {len(registry):,}")
    print(f"   Already addressed:         {len(existing_map):,}")

    if args.status:
        stats = compute_stats(existing_map, chunks=chunks)
        e = stats['epub']
        p = stats['pdf']
        print(f"\n📊 Coverage:")
        print(f"EPUB chunks:")
        print(f"   total:        {e['total']:,}")
        print(f"   with_cfi:     {e['with_cfi']:,}")
        print(f"   coverage:     {e['coverage_pct']}%")
        print(f"")
        print(f"PDF chunks:")
        print(f"   total:        {p['total']:,}")
        print(f"   with_page:    {p['with_page']:,}")
        print(f"   coverage:     {p['coverage_pct']}%")
        return

    start = time.time()
    address_map, stats = process_chunks(chunks, registry, existing_map, existing_keys, book_filter=args.book)
    elapsed = time.time() - start

    print(f"\n📊 Results:")
    print(f"   Already had CFI:     {stats['already_had_cfi']:,}")
    print(f"   New CFIs generated:  {stats['new_cfi']:,}")
    print(f"   Failed:              {stats['failed']:,}")
    print(f"   Skipped (PDF/no ID): {stats['skipped']:,}")
    print(f"   Total in map:        {stats['total']:,}")
    print(f"   Time:                {elapsed:.1f}s")

    coverage = compute_stats(address_map, chunks=chunks)
    e = coverage['epub']
    p = coverage['pdf']
    print(f"\n📊 Coverage:")
    print(f"EPUB chunks:")
    print(f"   total:        {e['total']:,}")
    print(f"   with_cfi:     {e['with_cfi']:,}")
    print(f"   coverage:     {e['coverage_pct']}%")
    print(f"")
    print(f"PDF chunks:")
    print(f"   total:        {p['total']:,}")
    print(f"   with_page:    {p['with_page']:,}")
    print(f"   coverage:     {p['coverage_pct']}%")

    print(f"\n💾 Saving to {ADDRESS_MAP_PATH}...")
    with open(ADDRESS_MAP_PATH, "w") as f:
        json.dump(address_map, f, indent=2)
    print(f"   ✅ {len(address_map):,} entries saved.")


if __name__ == "__main__":
    main()
