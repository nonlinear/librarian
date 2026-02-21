#!/bin/bash
# Librarian Skill Setup
# Downloads embedding model and installs dependencies

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🏴 Librarian Skill Setup"
echo

# 1. Install Python dependencies
echo "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r "${SKILL_DIR}/requirements.txt"
elif command -v pip &> /dev/null; then
    pip install -r "${SKILL_DIR}/requirements.txt"
else
    echo "❌ pip not found. Install Python 3.11+ first."
    exit 1
fi

# 2. Download embedding model
echo
echo "📚 Downloading embedding model (BAAI/bge-small-en-v1.5, ~130MB)..."
python3 - << 'PYTHON'
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path

# Set cache to skill/models/
skill_dir = Path(__file__).parent.resolve()
models_dir = skill_dir / "models"
models_dir.mkdir(exist_ok=True)
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(models_dir)

# Download model
print("Downloading model...")
model = SentenceTransformer('BAAI/bge-small-en-v1.5')
print(f"✓ Model saved to {models_dir}")
PYTHON

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "1. Add books to books/ folder (or symlink to parent project)"
echo "2. Test: ./librarian.sh 'test query' topic magick_chaos 3"
