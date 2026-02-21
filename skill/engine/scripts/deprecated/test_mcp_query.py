import subprocess
import json

# JSON-RPC request for hexagram 53 in oracles
query = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "query_literature",
        "arguments": {
            "question": "Regarding oracles, what is hexagram 53?",
            "book_context": "oracles",
            "max_sources": 3,
            "return_snippets": True
        }
    }
}

# Start MCP server as subprocess and send query
proc = subprocess.Popen([
    "/opt/homebrew/bin/python3.11",
    "/Users/nfrota/Documents/literature/engine/scripts/literature_mcp_server.py"
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Send query
proc.stdin.write(json.dumps(query) + "\n")
proc.stdin.flush()

# Read response
response = proc.stdout.readline()
print("MCP Server Response:")
print(response)

# Terminate server
proc.terminate()
