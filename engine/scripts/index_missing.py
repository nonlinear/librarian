#!/usr/bin/env python3
"""Index the two missing papers that need clean EPUB regeneration."""
import sys, os, json, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # engine/ for config

from zipfile import ZipFile
from bs4 import BeautifulSoup
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import get_config
from text_extraction import chunk_text

_cfg = get_config()
BOOKS = str(_cfg.corpus_path)
FAISS = str(_cfg.index_path)
STATE = str(_cfg.index_state_path)
MODELS = str(_cfg.models_dir)
_BOOKS_PREFIX = BOOKS.rstrip("/") + "/"

def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            d = json.load(f)
            if "metadata" not in d: d["metadata"] = []
            return d
    return {"books": {}, "metadata": [], "file_cache": {}}

def save(state):
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)

def extract_text(epub_path):
    texts = []
    with ZipFile(epub_path) as z:
        for name in z.namelist():
            if name.endswith((".xhtml", ".html", ".htm")):
                soup = BeautifulSoup(z.read(name), "html.parser")
                t = soup.get_text(separator="\n", strip=True)
                if t: texts.append(t)
    return "\n\n".join(texts)

state = load()
if os.path.exists(FAISS):
    index = faiss.read_index(FAISS)
else:
    print(f"⚠️ No index at {FAISS}; starting fresh (empty IndexFlatIP).")
    index = faiss.IndexFlatIP(384)
model = SentenceTransformer("BAAI/bge-small-en-v1.5", cache_folder=MODELS)

papers = [
    (f"{_BOOKS_PREFIX}literary-machines.epub", "Nelson — Literary Machines"),
    (f"{_BOOKS_PREFIX}_papers/ihde-technology-and-the-lifeworld.epub", "Ihde — Technology and the Lifeworld"),
]

for path, label in papers:
    if not os.path.exists(path):
        print(f"SKIP {label}: not found at {path}")
        continue
    
    with open(path, "rb") as f:
        h = hashlib.sha256(f.read(1024*1024)).hexdigest()[:16]
    
    if h in state["books"]:
        print(f"SKIP {label}: already indexed ({state['books'][h]['chunk_count']} chunks)")
        continue
    
    print(f"INDEX {label}...", end=" ", flush=True)
    full = extract_text(path)
    if not full.strip():
        print("no text")
        continue
    
    chunks = chunk_text(full, size=800, overlap=100)
    if not chunks:
        print("no chunks")
        continue
    
    print(f"{len(chunks)} chunks, embedding...", end=" ", flush=True)
    embs = model.encode(chunks, convert_to_numpy=True)
    
    start = index.ntotal
    ids = np.arange(start, start + len(chunks), dtype=np.int64)
    index.add_with_ids(embs, ids)
    
    state["books"][h] = {
        "path": path.replace(_BOOKS_PREFIX, ""),
        "indexed_at": time.time(),
        "chunk_range": [start, index.ntotal],
        "chunk_count": len(chunks),
        "format": "epub",
    }
    
    for i in range(len(chunks)):
        state["metadata"].append({
            "chunk_id": f"ch_{h}_{i}",
            "book_hash": h,
            "index": start + i,
            "text": chunks[i],
        })
    
    print(f"DONE [{start}..{index.ntotal})")

faiss.write_index(index, FAISS)
save(state)
print(f"\nFINAL: {len(state['books'])} books, {index.ntotal} chunks")
