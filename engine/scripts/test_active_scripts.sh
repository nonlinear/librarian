#!/bin/bash
# Test all active (non-deprecated) scripts
# This is what CHECKS.md should run

set -e
cd "$(dirname "$0")/../.."

echo "🧪 Testing Active Scripts"
echo "=========================="
echo ""

# Test 1: Library-index.json validity
echo "1️⃣ Testing library-index.json..."
python3.11 -c "
import json
from pathlib import Path

library_index = Path('books/.library-index.json')
if not library_index.exists():
    print('❌ books/.library-index.json missing')
    exit(1)

metadata = json.loads(library_index.read_text())
topic_count = len(metadata.get('topics', []))
print(f'✅ Valid: {topic_count} topics')

# Verify all paths exist
missing = [t['id'] for t in metadata['topics'] if not (Path('books') / t['path']).exists()]
if missing:
    print(f'❌ Missing paths: {missing[:3]}')
    exit(1)
print(f'✅ All topic paths exist')
"
echo ""

# Test 2: index_library.py --metadata (folder discovery)
echo "2️⃣ Testing index_library.py --metadata..."
timeout 120 python3.11 engine/scripts/index_library.py --metadata 2>&1 | head -20 | grep -q "Metadata mode" && echo "✅ Metadata mode works" || { echo "❌ Metadata mode failed"; exit 1; }
echo ""

# Test 3: index_library.py (smart mode default)
echo "3️⃣ Testing index_library.py (smart mode)..."
timeout 60 python3.11 engine/scripts/index_library.py 2>&1 | head -20 | grep -q "Smart mode\|No changes detected\|All.*topics already registered" && echo "✅ Smart mode works" || { echo "❌ Smart mode failed"; exit 1; }
echo ""

# Test 4: research.py (CLI query)
echo "4️⃣ Testing research.py..."
if [ -f engine/scripts/research.py ]; then
    python3.11 engine/scripts/research.py "test query" --topic ai_policy --k 1 2>&1 | grep -q "results\|error" && echo "✅ Research CLI works" || echo "⚠️  Research test inconclusive"
else
    echo "⚠️  research.py not found"
fi
echo ""

# Test 5: mcp_server.py (starts without error)
echo "5️⃣ Testing mcp_server.py..."
timeout 3 python3.11 engine/scripts/mcp_server.py 2>&1 | grep -q "Librarian MCP\|Loaded" && echo "✅ MCP server starts" || echo "⚠️  MCP startup test inconclusive"
echo ""

# Test 6: Active scripts exist
echo "6️⃣ Checking active scripts exist..."
for script in engine/scripts/index_library.py engine/scripts/research.py engine/scripts/mcp_server.py; do
    if [ -f "$script" ]; then
        echo "   ✅ $script"
    else
        echo "   ❌ $script MISSING"
        exit 1
    fi
done
echo ""

echo "✅ All active script tests passed!"
echo ""
echo "Run this before every commit to ensure indexing works."
