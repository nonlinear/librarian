#!/usr/bin/env python3
"""Index only the foundation papers, one at a time with error handling."""
import sys, os, time, json, hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # engine/ for config

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from text_extraction import extract_epub_paragraphs, extract_pdf_paragraphs, chunk_paragraphs

# Paths — resolved via config (Boundary: engine knows no instance paths)
from config import get_config
_cfg = get_config()
LIBRARY_ROOT = _cfg.corpus_path
MODELS_DIR = _cfg.models_dir
FAISS_INDEX_PATH = _cfg.index_path
METADATA_PATH = _cfg.metadata_path
INDEX_STATE_PATH = _cfg.index_state_path

PAPERS = [
    ("bush-as-we-may-think.epub", "Bush — As We May Think"),
    ("literary-machines.epub", "Nelson — Literary Machines"),
    ("w3c-annotation-model.epub", "W3C — Web Annotation Data Model"),
    ("w3c-open-annotation-paper.pdf", "W3C — Open Annotation Paper"),
    ("memento-paper.epub", "Memento — Time Travel for the Web"),
    ("memento-rfc7089.epub", "RFC 7089 — Memento Protocol"),
    ("persistent-annotations.epub", "Persistent Web Annotations"),
    ("winograd-understanding-computers-cognition.epub", "Winograd & Flores — Understanding Computers"),
    ("ihde-technology-and-the-lifeworld.epub", "Ihde — Technology and the Lifeworld"),
    ("taylor-organization-of-information.epub", "Taylor — Organization of Information"),
    ("frbr-functional-requirements.epub", "FRBR — Functional Requirements"),
]

def load_state():
    if INDEX_STATE_PATH.exists():
        with open(INDEX_STATE_PATH) as f:
            return json.load(f)
    return {"books": {}, "metadata": [], "file_cache": {}}

def save_state(state):
    INDEX_STATE_PATH.write_text(json.dumps(state, indent=2))

def load_faiss():
    if FAISS_INDEX_PATH.exists():
        return faiss.read_index(str(FAISS_INDEX_PATH))
    return faiss.IndexFlatIP(384)

def save_faiss(index):
    faiss.write_index(index, str(FAISS_INDEX_PATH))

def book_hash(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read(1024*1024)).hexdigest()[:16]

def main():
    state = load_state()
    faiss_index = load_faiss()
    model = SentenceTransformer("BAAI/bge-small-en-v1.5", cache_folder=str(MODELS_DIR))
    
    indexed_count = 0
    for fname, label in PAPERS:
        path = LIBRARY_ROOT / fname
        if not path.exists():
            print(f"⚠️  {label}: file not found")
            continue
        
        h = book_hash(path)
        if h in state["books"]:
            print(f"⬆️  {label}: already indexed ({state['books'][h]['chunk_count']} chunks)")
            continue
        
        print(f"📖 {label}...", end=" ", flush=True)
        try:
            ft = path.suffix.lstrip(".")
            if ft == "epub":
                paragraphs = extract_epub_paragraphs(str(path))
            elif ft == "pdf":
                paragraphs = extract_pdf_paragraphs(str(path))
            else:
                print(f"unsupported {ft}")
                continue
            
            chunks = chunk_paragraphs(paragraphs)
            if not chunks:
                print("no text extracted")
                continue
            
            # Extract text from chunk dicts
            texts = [c["text"] for c in chunks]
            
            print(f"{len(chunks)} chunks, embedding...", end=" ", flush=True)
            embs = model.encode(texts, convert_to_numpy=True)
            
            start = faiss_index.ntotal
            faiss_index.add(embs)
            
            state["books"][h] = {
                "path": str(path.relative_to(LIBRARY_ROOT) if LIBRARY_ROOT in path.parents else path),
                "indexed_at": time.time(),
                "chunk_range": [start, faiss_index.ntotal],
                "chunk_count": len(chunks),
                "format": ft,
            }
            
            for i, (chunk, emb) in enumerate(zip(chunks, embs)):
                state["metadata"].append({
                    "chunk_id": f"ch_{h}_{i}",
                    "book_hash": h,
                    "index": start + i,
                    "text": chunk["text"],
                })
            
            indexed_count += 1
            print(f"✅ [{start}..{faiss_index.ntotal})")
            
        except Exception as e:
            print(f"❌ {e}")
            continue
    
    print(f"\n💾 Saving ({indexed_count} new books)...", end=" ", flush=True)
    save_faiss(faiss_index)
    save_state(state)
    print("✅")
    
    total = len(state["books"])
    total_chunks = faiss_index.ntotal
    print(f"\n📊 Index: {total} books, {total_chunks} chunks")

if __name__ == "__main__":
    main()
