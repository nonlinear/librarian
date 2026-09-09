#!/bin/bash
# ── Librarian Daily Reindex ──
# Runs inside the librarian container to re-index all books.
# Signals the HTTP server via SIGHUP on completion.
# Safe to run daily — only rebuilds if new books are detected.

# Run the init_index check first — it's fast if nothing changed
docker exec librarian python3 /app/engine/scripts/init_index.py 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "[librarian-cron] Index rebuild FAILED (exit $EXIT_CODE)"
    # OPTIONAL: Add alert here (email, push, etc.)
    # For now, just log it — Docker healthcheck will catch if container goes unhealthy
    exit $EXIT_CODE
fi

echo "[librarian-cron] Index check OK $(date)"
