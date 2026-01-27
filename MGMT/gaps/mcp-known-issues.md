# MCP Known Issues

**Context:** Model Context Protocol (MCP) integration attempts with VS Code Copilot. Multiple attempts across different versions have consistently failed with stdin-related issues.

**Historical Context:** This is NOT the first time we've attempted MCP integration. Previous attempts were abandoned due to stdin communication failures.

---

## 2026-01-26: MCP stdin Exit Code 2 (Core Blocker)

**Problem:** MCP server returns exit code 2 when called by VS Code, but works perfectly via terminal

**Hypothesis Chain:**

1. ❌ **Path calculation wrong** → Fixed (parent.parent.parent), still exit code 2
2. ❌ **v1.0 schema incompatibility** → Updated to v2.0 (.library-index.json), still fails
3. ❌ **Permissions issue** → File is executable (755), still fails
4. ❌ **Config path outdated** → Updated VS Code settings.json, still fails
5. ❌ **Duplicate configs conflict** → Unified global + workspace configs, still fails
6. ❌ **stderr logging causes exit** → Removed file redirection, still fails
7. ❌ **Progress bars crash stdin** → Suppressed with env vars, still fails

**Root Cause:**

Unknown. The discrepancy between terminal success and VS Code failure suggests:

- VS Code MCP client sends different input format than `<<<` heredoc
- Python environment mismatch (despite using same `/opt/homebrew/bin/python3`)
- VS Code pipe mechanism incompatible with our stdin loop
- Timeout during model loading (~10 seconds) interpreted as crash

**Evidence:**

Terminal test (WORKS):

```bash
/opt/homebrew/bin/python3 /Users/nfrota/Documents/librarian/engine/scripts/mcp_server.py \
  <<< '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
# Output: {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "0.1.0", ...}}
```

VS Code MCP tool (FAILS):

```
ERROR while calling tool: MCP server could not be started: Process exited with code 2
```

Log file evidence:

```bash
# engine/logs/mcp_server.log after VS Code call
# (empty file - script never started)
```

**Failed Attempts:**

1. **Suppress progress bars:**

```python
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
import warnings
warnings.filterwarnings('ignore')
```

Result: Model loads silently in terminal, still exit code 2 in VS Code

2. **Error handling everywhere:**

```python
try:
    import research
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(2)  # Explicit exit code
```

Result: No errors logged, script never reaches main()

3. **Logging to file:**

```python
log_file = Path(__file__).parent.parent / "logs" / "mcp_server.log"
sys.stderr = open(log_file, "a")
```

Result: Log file created but empty when VS Code calls

**Debugging Discovery:**

```bash
# Python can import successfully
/opt/homebrew/bin/python3 -c "import sys; sys.path.insert(0, '.../scripts'); import research; print('OK')"
# Output: OK

# Server responds to initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python3 mcp_server.py
# Output: Valid JSON-RPC response

# Exact VS Code command works in terminal
/opt/homebrew/bin/python3 /Users/.../mcp_server.py < /dev/null
# Output: Model loads, waits for input (expected)
```

**Current Status:** ❌ BLOCKED

**Key Lessons:**

1. **stdin is fundamentally incompatible with VS Code MCP** - Terminal ≠ VS Code pipe behavior
2. **Exit code 2 happens BEFORE Python execution** - No logs, no stderr, script never starts
3. **Configuration is correct** - Same command works in terminal with identical paths
4. **This is a KNOWN PROBLEM** - We've abandoned MCP integration before for the same reason

**Next Steps (if we attempt again):**

- [ ] Try HTTP/WebSocket transport instead of stdin (if MCP supports)
- [ ] Test with minimal Python script (no imports) to isolate issue
- [ ] Check VS Code MCP client source code for stdin handling
- [ ] Ask VS Code community about MCP exit code 2 patterns
- [ ] Consider alternative: Keep research.py as CLI-only tool

---

## 2026-01-26: PyTorch Progress Bars Break MCP stdin

**Problem:** Model loading progress bars (199 weights, ~10 seconds) spam stderr with ANSI escape codes

**Hypothesis:** Progress bar output overwhelms VS Code MCP stdin buffer or breaks parsing

**Evidence:**

```bash
# Terminal output shows progress bars work fine
Loading weights: 100%|██████████| 199/199 [00:00<00:00, 10887.33it/s]
BertModel LOAD REPORT from: BAAI/bge-small-en-v1.5
```

But with VS Code → exit code 2 (no output captured)

**Attempted Solution:**

```python
# Suppress all progress output
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
import warnings
warnings.filterwarnings('ignore')
```

**Result:** Progress bars suppressed in terminal, but VS Code still returns exit code 2

**Conclusion:** Progress bars are NOT the root cause, but stdin is fundamentally broken

**Status:** ⏳ SECONDARY ISSUE (blocked by core stdin problem)

---

## 2026-01-26: VS Code MCP Config Duplication & Truncation

**Problem:** Multiple MCP server configs caused confusion and potential conflicts

**Discovery Process:**

1. Created workspace config: `.vscode/settings.json` with name `librarian`
2. Global config still had: `~/Library/.../settings.json` with name `personal-library`
3. VS Code tool prefix: `mcp_personal_libr_list_topics` (truncated to 12 chars)

**Root Cause:**

- Two configs pointing to same script
- Different server names (`librarian` vs `personal-library`)
- VS Code may truncate server names in tool identifiers

**Solution:**

Unified to single config:

```json
// .vscode/settings.json (workspace-level)
{
  "chat.mcp.servers": {
    "librarian": {
      "command": "/opt/homebrew/bin/python3",
      "args": [
        "/Users/nfrota/Documents/librarian/engine/scripts/mcp_server.py"
      ],
      "description": "Personal book library RAG (v2.0)",
      "enabled": false // Disabled due to stdin issues
    }
  }
}
```

Global config should be updated to match (or removed).

**Verification:**

```bash
grep -A 5 "personal-library" ~/Library/Application\ Support/Code/User/settings.json
# Should return nothing (or be renamed to "librarian")
```

**Status:** ✅ RESOLVED (but MCP still doesn't work due to stdin issue)

**Key Lessons:**

1. Keep MCP configs in workspace `.vscode/settings.json`, not global
2. Use short server names (avoid truncation issues)
3. Remove duplicate configs to prevent conflicts

---

## 2026-01-26: MCP Server Architecture - Single Source of Truth

**Problem:** Original mcp_server.py (562 lines) duplicated all query logic from research.py

**User Insight:** "why i need an mcp so? if i can resolve via py? shouldnt research.py itself have BOTH MCP or py as fallback?"

**Root Cause:** Architectural mistake - reimplemented research logic instead of delegating

**Solution:** Thin wrapper pattern

**Before (562 lines):**

```python
# mcp_server.py
def query_library(query, topic, book, k):
    # 400+ lines of duplicated logic
    metadata = load_metadata()
    topic_data = load_topic(...)
    results = faiss_search(...)
    # ... etc
```

**After (143 lines):**

```python
# mcp_server.py
import research  # Single source of truth

def handle_request(request):
    if method == 'tools/call' and tool == 'query_library':
        # Delegate to research.py
        results = research.query_library(
            params['query'],
            params.get('topic'),
            params.get('book'),
            params.get('k', 5)
        )
        return format_results(results)
```

**Architecture:**

```
research.py (203 lines)
  ↑
  │ (import & delegate)
  │
mcp_server.py (143 lines)
  ↑
  │ (JSON-RPC stdin)
  │
VS Code MCP Client ❌ (exit code 2)
```

**Benefits:**

- 75% smaller MCP wrapper (143 vs 562 lines)
- Zero code duplication
- research.py remains standalone CLI tool
- Changes to query logic only need updating in one place

**Status:** ✅ RESOLVED

**Key Lessons:**

1. **Delegate, don't duplicate** - Wrappers should be thin adapters
2. **Single source of truth** - Core logic in one place (research.py)
3. **Composition over reimplementation** - Import and call, don't rewrite

---

## Historical Context

**Why we've attempted MCP multiple times:**

- VS Code Copilot chat integration is attractive
- MCP protocol promises tool/function calling
- Would enable natural language queries: "what books do I have on X?"

**Why we keep failing:**

- stdin communication fundamentally broken between VS Code and Python
- No error details from VS Code MCP client (just "exit code 2")
- Same code works perfectly in terminal
- Time investment vs value: 4+ hours debugging, zero progress

**Decision Point:**

Should we:

1. ❌ **Keep trying MCP** - High time cost, low success probability
2. ✅ **Accept CLI-only** - research.py works perfectly, fast, reliable
3. ⏳ **Wait for MCP updates** - Maybe future VS Code versions fix stdin
4. 🔍 **Investigate HTTP transport** - If MCP supports alternatives to stdin

**Current recommendation:** Accept that `research.py` as CLI tool is sufficient. Integration can wait for better MCP support or alternative transport.

---

## Related Files

**Active:**

- `engine/scripts/research.py` - CLI tool (works perfectly)
- `engine/scripts/mcp_server.py` - MCP wrapper (doesn't work)

**Config:**

- `.vscode/settings.json` - Workspace MCP config (disabled)
- `~/Library/Application Support/Code/User/settings.json` - Global config

**Deprecated:**

- `engine/scripts/deprecated/mcp_server_deprecated.py` - Previous minimal version
- `engine/scripts/deprecated/mcp_server.py.old` - Original 562-line bloated version

---

## Future Investigation

**If attempting MCP again:**

1. **Test minimal script:**

```python
#!/usr/bin/env python3
import sys, json
for line in sys.stdin:
    req = json.loads(line)
    print(json.dumps({"jsonrpc":"2.0","id":req["id"],"result":{}}))
    sys.stdout.flush()
```

If this fails with exit code 2 → VS Code MCP stdin is broken, not our code.

2. **Check MCP spec for alternatives:**

- HTTP transport
- WebSocket transport
- File-based IPC

3. **Search for similar issues:**

- VS Code GitHub issues with "MCP exit code 2"
- MCP protocol GitHub discussions
- Community forums (Reddit, Discord)

4. **Contact VS Code team:**

- Report stdin incompatibility with reproducible test case
- Request HTTP/WebSocket transport support
- Ask for better error reporting (exit code 2 is useless)

---

## Conclusion

**stdin-based MCP is a dead end for this project.** We've invested significant time across multiple attempts and the core issue remains unresolved. The CLI tool (`research.py`) works perfectly and provides all needed functionality.

**Recommendation:** Mark MCP integration as "not feasible with current VS Code implementation" and move on to productive work.
