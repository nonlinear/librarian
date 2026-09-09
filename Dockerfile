FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY engine/requirements.txt /app/engine/requirements.txt
RUN pip install --no-cache-dir -r engine/requirements.txt
RUN pip install --no-cache-dir mcp watchdog fastapi uvicorn

COPY engine/ /app/engine/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/engine/scripts/mcp_server_faiss.py /app/engine/scripts/librarian_http.py /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
