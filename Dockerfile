FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY engine/requirements.txt /app/engine/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r engine/requirements.txt
RUN pip install --no-cache-dir mcp watchdog fastapi uvicorn

# Copy code
COPY engine/ /app/engine/
COPY entrypoint.sh /app/entrypoint.sh

# Copy reader
COPY reader/ /app/reader/

# Set executables
RUN chmod +x /app/engine/scripts/mcp_server.py /app/entrypoint.sh

# books/ mounted at runtime via volume (not baked in)
ENTRYPOINT ["/app/entrypoint.sh"]
