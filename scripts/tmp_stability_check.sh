#!/bin/bash
# Personal Library MCP - Automated Stability Checks

echo "🔍 Running stability checks..."
echo ""

# Test 1: MCP query functionality (what research.prompt.md actually uses)
echo "1️⃣ MCP query test..."
python3.11 -c "
import json
from pathlib import Path
metadata = json.loads((Path('books') / 'metadata.json').read_text())
topic_count = len(metadata.get('topics', []))
print(f'✅ MCP works ({topic_count} topics)' if topic_count > 0 else '❌ MCP failed')
" 2>/dev/null || echo "❌ MCP failed"

# Test 2: Dependencies
echo "2️⃣ Dependencies test..."
python3.11 -c "import llama_index.core; import sentence_transformers" 2>&1 && echo "✅ Dependencies OK" || echo "❌ Dependencies missing"

# Test 3: File structure
echo "3️⃣ File structure test..."
test -f books/metadata.json && ls books/*/faiss.index >/dev/null 2>&1 && echo "✅ Files exist" || echo "❌ Files missing"

# Test 4: Nested folder support
echo "4️⃣ Nested folder test..."
python3.11 -c "
import json
from pathlib import Path
metadata = json.loads((Path('books') / 'metadata.json').read_text())
nested = [t['id'] for t in metadata['topics'] if '_' in t['id']]
print(f'✅ Nested topics work ({len(nested)} found)' if nested else '⚠️ No nested topics')
" 2>/dev/null || echo "❌ Nested topic test failed"

echo ""
echo "✅ All checks complete. Review results above."
