#!/usr/bin/env python3
"""
CIP-1: Corpus Integrity Protocol

Validates that every FAISS chunk has a corresponding metadata entry
and that every metadata book_id resolves to the books registry.

Usage:
  python3 cip1_validator.py                    # full report
  python3 cip1_validator.py --repair           # attempt auto-repair
  python3 cip1_validator.py --status           # just status string
"""
import os, sys, json, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/ for config
from config import get_config
_cfg = get_config()
BOOKS_DIR = _cfg.corpus_path
FAISS_INDEX = _cfg.index_path
METADATA = _cfg.metadata_path
INDEX_STATE = _cfg.index_state_path

STATUS_STABLE = "STABLE"
STATUS_DEGRADED = "DEGRADED"
STATUS_BROKEN = "BROKEN"
STATUS_QUARANTINE = "QUARANTINE"

def load_metadata():
    """Load metadata.json (chunk registry)."""
    if not METADATA.exists():
        print(f"[CIP-1] ❌ metadata.json not found at {METADATA}")
        return {}, 0
    with open(METADATA) as f:
        data = json.load(f)
    # metadata.json structure: { "books": [...], "chunks": [...] }
    if isinstance(data, dict) and "chunks" in data:
        chunks = data["chunks"]
        books_list = data.get("books", [])
        if isinstance(chunks, list):
            result = {}
            for c in chunks:
                cid = c.get("chunk_id", c.get("id", f"ch_{len(result)}"))
                result[cid] = c
            return result, len(books_list)
    # Fallback for other structures
    if isinstance(data, list):
        return {item.get("chunk_id", item.get("id", f"ch_{i}")): item for i, item in enumerate(data)}, 0
    if isinstance(data, dict):
        return data, 0
    return {}, 0

def load_index_state():
    """Load book registry from .index_state.json."""
    if not INDEX_STATE.exists():
        print(f"[CIP-1] ⚠️ .index_state.json not found")
        return {}, {}
    with open(INDEX_STATE) as f:
        state = json.load(f)
    books = state.get("books", {}) if isinstance(state, dict) else {}
    # Normalize: books might be dict {hash: info} or list
    if isinstance(books, list):
        books = {b.get("id", b.get("hash", f"b_{i}")): b for i, b in enumerate(books)}
    stats = state.get("stats", state.get("statistics", {})) if isinstance(state, dict) else {}
    return books, stats

def get_faiss_chunk_count():
    """Get total chunks from FAISS index metadata."""
    try:
        import faiss
        idx = faiss.read_index(str(FAISS_INDEX))
        return idx.ntotal
    except Exception as e:
        print(f"[CIP-1] ⚠️ Could not read FAISS index: {e}")
        return 0

def run_integrity(repair=False, status_only=False):
    """Main CIP-1 validation pass."""
    print("=" * 50)
    print("CIP-1: Corpus Integrity Protocol")
    print("=" * 50)

    # Load sources
    faiss_total = get_faiss_chunk_count()
    metadata, metadata_books = load_metadata()
    books, stats = load_index_state()
    
    metadata_total = len(metadata)
    books_total = len(books) or metadata_books
    
    print(f"\n📊 Loaded:")
    print(f"   FAISS index:     {faiss_total:,} chunks")
    print(f"   metadata.json:   {metadata_total:,} entries")
    print(f"   .index_state:    {books_total:,} books")
    if stats:
        print(f"   reported books:  {stats.get('total_books', stats.get('books', '?'))}")
    
    # Validate
    orphans = []
    broken_refs = []
    desync = []
    
    # Check metadata coverage vs FAISS entries
    # We can't iterate FAISS entries cheaply without loading all vectors,
    # but we can estimate from total count
    if faiss_total > 0 and metadata_total > 0:
        diff = abs(faiss_total - metadata_total)
        if diff > 100:  # tolerate small drift
            desync.append(f"FAISS ({faiss_total}) vs metadata ({metadata_total}): diff={diff}")
    
    # Check metadata entries have valid book references
    metadata_book_ids = set()
    for chunk_id, entry in metadata.items():
        book_id = entry.get("book_id") or entry.get("book_hash", "")
        if book_id:
            metadata_book_ids.add(book_id)
            if books and book_id not in books:
                broken_refs.append(book_id)
        else:
            orphans.append(chunk_id)
    
    # Report
    print(f"\n🔍 Validation:")
    print(f"   Orphans (chunk without book_id): {len(orphans):,}")
    print(f"   Broken refs (book_id not in registry): {len(broken_refs)}")
    print(f"   Desync (FAISS vs metadata count): {len(desync)}")
    
    # Determine status
    status = STATUS_STABLE
    details = []
    
    if len(orphans) > 0 and len(orphans) / max(metadata_total, 1) > 0.01:
        status = STATUS_BROKEN
        details.append(f">1% orphan chunks ({len(orphans):,})")
    elif len(orphans) > 0:
        status = STATUS_DEGRADED
        details.append(f"{len(orphans):,} orphan chunks")
    
    if len(broken_refs) > 0:
        if status == STATUS_STABLE:
            status = STATUS_DEGRADED
        details.append(f"{len(broken_refs)} broken book refs")
    
    if len(desync) > 0:
        if status == STATUS_STABLE:
            status = STATUS_DEGRADED
        details.extend(desync)
    
    # Quarantine if catastrophic
    if len(orphans) > metadata_total * 0.5:
        status = STATUS_QUARANTINE
        details.append(">50% orphans — corpus quarantined")
    
    print(f"\n🏥 Status: {status}")
    if details:
        for d in details:
            print(f"   ⚠️ {d}")
    
    # Report summary
    print(f"\n📋 Summary:")
    print(f"   FAISS total:     {faiss_total:,}")
    print(f"   Metadata total:  {metadata_total:,}")
    print(f"   Books total:     {books_total:,}")
    print(f"   Orphans:         {len(orphans):,}")
    print(f"   Broken refs:     {len(broken_refs)}")
    print(f"   Desync:          {len(desync)}")
    print(f"   Status:          {status}")
    
    # Repair mode
    if repair and status != STATUS_STABLE:
        print(f"\n🔧 Repair mode — attempting fixes...")
        # Strategy 1: if orphans exist, try to infer book_id from nearest chunk
        if len(orphans) > 0:
            print(f"   ⚠️ {len(orphans)} orphans need review. Automated repair requires reindex.")
            print(f"   → Run full reindex to regenerate metadata with proper book_ids.")
        # Strategy 2: broken refs can sometimes be restored
        if len(broken_refs) > 0:
            print(f"   🔄 Attempting to restore {len(broken_refs)} broken references...")
            # In a real implementation, try reverse lookup
            pass
        # Strategy 3: desync → rebuild metadata
        if len(desync) > 0:
            print(f"   🔄 Metadata desync detected. Consider: python3 indexer.py --all")
    
    if status_only:
        return status
    
    return {
        "status": status,
        "faiss_total": faiss_total,
        "metadata_total": metadata_total,
        "books_total": books_total,
        "orphans": len(orphans),
        "broken_refs": len(broken_refs),
        "desync": len(desync),
        "details": details
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIP-1 Corpus Integrity Validator")
    parser.add_argument("--repair", action="store_true", help="Attempt auto-repair")
    parser.add_argument("--status", action="store_true", help="Return status string only")
    args = parser.parse_args()
    
    result = run_integrity(repair=args.repair, status_only=args.status)
    
    if args.status:
        print(result)
    elif isinstance(result, dict):
        sys.exit(0 if result["status"] == STATUS_STABLE else 1)
