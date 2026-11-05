#!/bin/bash
# Installation script for Squeeze Gateway CLI

set -e

echo "=================================="
echo "Squeeze Gateway CLI - Installation"
echo "=================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "   Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python version: $PYTHON_VERSION"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip is not installed"
    exit 1
fi

echo "✅ pip is available"
echo ""

# Install package
echo "📦 Installing Squeeze Gateway..."
if [ -f "pyproject.toml" ]; then
    # Install from source
    pip3 install -e .
else
    # Install from PyPI
    pip3 install squeeze-gateway
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Initialize configuration:"
echo "     sqz install"
echo ""
echo "  2. Set your Gemini API key:"
echo "     sqz config set api_key YOUR_API_KEY"
echo ""
echo "  3. Start the gateway:"
echo "     sqz start"
echo ""
echo "  4. Try interactive chat:"
echo "     sqz chat"
echo ""
echo "For help: sqz --help"
echo "Documentation: https://github.com/kirill-skoch/squeeze-gateway"
echo ""
