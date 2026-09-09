#!/bin/bash
set -e

# ── Instance paths from config/env (Boundary: engine knows no instance paths) ──
LIBRARIAN_BOOKS="${LIBRARIAN_BOOKS:-/app/books}"
MODELS_DIR="${LIBRARIAN_MODELS:-/app/engine/models}"
EMBEDDING_MODEL="${LIBRARIAN_MODEL:-BAAI/bge-small-en-v1.5}"
# Export so every child (init_index, watcher, http server) reads the resolved
# paths from env via the ConfigResolver. No inline `VAR=... python3` prefixes —
# bash mishandles them when the value is an absolute path.
export LIBRARIAN_BOOKS LIBRARIAN_MODELS LIBRARIAN_MODEL EMBEDDING_MODEL MODELS_DIR

# ── Embedding Model ──
if [ ! -d "$MODELS_DIR/models--BAAI--bge-small-en-v1.5" ]; then
    echo "Downloading embedding model ($EMBEDDING_MODEL)..."
    # First boot needs to fetch the model, so force ONLINE for this download even if
    # the compose sets TRANSFORMERS_OFFLINE / HF_OFFLINE (which is for steady-state
    # runs where the model is already cached). Otherwise a fresh BYOBook instance
    # cannot install (first boot download is blocked -> restart loop).
    HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE= HF_DATASETS_OFFLINE= \
      python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('$EMBEDDING_MODEL', cache_folder='$MODELS_DIR')"
    echo "Model downloaded successfully."
else
    echo "Embedding model already present."
fi

# ── Self-Healing Index ──
# Idempotent: if index exists and is valid, runs instantly.
# If missing/corrupted, rebuilds from scratch with checkpoint/retry.
echo ""
echo "========================================"
echo "🔍 Checking FAISS index (self-healing)..."
echo "========================================"
MAX_RETRIES=3
RETRY_DELAY=30
for i in $(seq 1 $MAX_RETRIES); do
    if python3 -c "import os,sys; from pathlib import Path; sys.path.insert(0,'/app/engine/scripts'); sys.path.insert(0,'/app/engine'); import config; c=config.get_config(); print('init_index:', c.index_path)" && python3 /app/engine/scripts/init_index.py; then
        echo "✅ Index check passed."
        break
    else
        echo "❌ Index check failed (attempt $i/$MAX_RETRIES)."
        if [ $i -lt $MAX_RETRIES ]; then
            echo "   Retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        else
            echo "   ⚠️  Continuing anyway — HTTP server will start with empty index."
        fi
    fi
done
echo ""

# ── File Watcher (auto-detect new books) ──
echo "Starting file watcher..."
python3 /app/engine/scripts/watcher.py &
WATCHER_PID=$!
echo "Watcher started (PID: $WATCHER_PID)"

# ── HTTP MCP Server (foreground) ──
echo "Starting HTTP MCP server on port ${LIBRARIAN_READER_PORT:-8088}..."
# Resolved paths are exported at the top (no inline `VAR=$VAR python3` prefix —
# bash errors when the assignment value is an absolute /app/... path).
exec python3 /app/engine/scripts/librarian_http.py
