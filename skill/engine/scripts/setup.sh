#!/usr/bin/env bash
# Setup script for Librarian MCP
# Supports: macOS, Linux, Windows (Git Bash/WSL)

set -e

# Get to repo root (parent of engine/scripts/)
cd "$(dirname "$0")/.."

echo "🔧 Librarian MCP - Setup"
echo "================================"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=Linux;;
    Darwin*)    PLATFORM=Mac;;
    CYGWIN*)    PLATFORM=Windows;;
    MINGW*)     PLATFORM=Windows;;
    *)          PLATFORM="UNKNOWN:${OS}"
esac

echo "📍 Detected platform: ${PLATFORM}"
echo ""

# Find Python 3.11+
PYTHON=""

if command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
elif command -v python3 &> /dev/null; then
    VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if (( $(echo "$VERSION >= 3.11" | bc -l) )); then
        PYTHON="python3"
    fi
fi

if [ -z "$PYTHON" ]; then
    echo "❌ Python 3.11+ not found"
    echo ""
    echo "Install Python 3.11+:"
    case "${PLATFORM}" in
        Mac)
            echo "  brew install python@3.11"
            ;;
        Linux)
            echo "  sudo apt install python3.11  # Debian/Ubuntu"
            echo "  sudo dnf install python3.11  # Fedora"
            ;;
        Windows)
            echo "  Download from: https://www.python.org/downloads/"
            ;;
    esac
    exit 1
fi

echo "✅ Found Python: $($PYTHON --version)"
echo ""

# Check pip
if ! $PYTHON -m pip --version &> /dev/null; then
    echo "❌ pip not found"
    echo "Install pip: curl https://bootstrap.pypa.io/get-pip.py | $PYTHON"
    exit 1
fi

echo "✅ Found pip: $($PYTHON -m pip --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
echo ""

$PYTHON -m pip install --upgrade pip --quiet

if [ -f "engine/requirements.txt" ]; then
    $PYTHON -m pip install -r engine/requirements.txt --quiet
    echo "✅ All dependencies installed"
else
    echo "❌ engine/requirements.txt not found"
    exit 1
fi

echo ""

# Download local embedding model
echo "📥 Downloading local embedding model..."
echo "   Model: BAAI/bge-small-en-v1.5 (~130MB)"
echo "   Location: engine/models/ (in project)"
echo ""

mkdir -p engine/models
$PYTHON -c "import os; os.environ['SENTENCE_TRANSFORMERS_HOME'] = 'engine/models'; from sentence_transformers import SentenceTransformer; model = SentenceTransformer('BAAI/bge-small-en-v1.5'); print('✅ Model downloaded to engine/models/')"

echo ""
echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add EPUB/PDF files to books/<topic>/"
echo "  2. Run: $PYTHON engine/scripts/generate_metadata.py"
echo "  3. Run: $PYTHON engine/scripts/indexer.py"
echo ""
