#!/bin/bash
# Activate virtual environment and set up environment
# Usage: source activate.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo "✓ Current directory: $(pwd)"
    echo ""
    echo "You can now run:"
    echo "  python3 scripts/test_vertex_ai_config.py"
    echo "  python3 main.py agent productspec --requirements 'Your requirements here'"
    echo ""
else
    echo "✗ Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi
