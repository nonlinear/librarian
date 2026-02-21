#!/bin/bash
# Wrapper para iniciar watchdog com logging

cd /Users/nfrota/Documents/librarian

# Create logs directory if it doesn't exist
mkdir -p engine/logs

echo "🚀 Starting Librarian Watchdog at $(date)" >> engine/logs/watchdog.log
echo "===========================================" >> engine/logs/watchdog.log

# -u forces unbuffered output so logs appear immediately
/opt/homebrew/bin/python3.11 -u engine/scripts/watch_library.py >> engine/logs/watchdog.log 2>> engine/logs/watchdog.error.log
