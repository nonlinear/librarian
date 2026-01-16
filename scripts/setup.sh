#!/usr/bin/env bash
# Setup script for Personal Library MCP
# Supports: macOS, Linux, Windows (Git Bash/WSL)

set -e

# Get to repo root (parent of scripts/)
cd "$(dirname "$0")/.."

echo "🔧 Personal Library MCP - Setup"
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

if [ -f "requirements.txt" ]; then
    $PYTHON -m pip install -r requirements.txt --quiet
    echo "✅ All dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

echo ""

# Download local embedding model
echo "📥 Downloading local embedding model..."
echo "   Model: sentence-transformers/all-MiniLM-L6-v2 (~90MB)"
echo "   Location: models/ (in project)"
echo ""

mkdir -p models
$PYTHON -c "import os; os.environ['SENTENCE_TRANSFORMERS_HOME'] = 'models'; from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2'); print('✅ Model downloaded to models/')"

echo ""
echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add EPUB/PDF files to books/<topic>/"
echo "  2. Run: $PYTHON scripts/generate_metadata.py"
echo "  3. Run: $PYTHON scripts/indexer.py"
echo ""
