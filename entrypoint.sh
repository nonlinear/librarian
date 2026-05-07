#!/bin/bash
set -e

# Download embedding model if not present
if [ ! -d "/app/engine/models/models--BAAI--bge-small-en-v1.5" ]; then
    echo "Downloading embedding model (BAAI/bge-small-en-v1.5, ~130MB)..."
    python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5', cache_folder='/app/engine/models')"
    echo "Model downloaded successfully."
else
    echo "Embedding model already present."
fi

# T019: Start watcher in background (auto-detect new books)
echo "Starting file watcher..."
python3 /app/engine/scripts/watcher.py &
WATCHER_PID=$!
echo "Watcher started (PID: $WATCHER_PID)"

# Start reader web server in background (port 8088)
echo "Starting reader server..."
READER_PORT=8088 python3 /app/reader/server.py &
READER_PID=$!
echo "Reader started (PID: $READER_PID)"

# T020: Start MCP server with hot-reload support
echo "Starting MCP server (FAISS with hot-reload)..."
exec python3 /app/engine/scripts/mcp_server_faiss.py
