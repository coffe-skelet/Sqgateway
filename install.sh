#!/bin/bash
# SKgate CLI - Installation Script for Linux/macOS
# Автоматическая установка SKgate CLI

set -e

echo ""
echo "============================================================"
echo "           SKgate CLI - Installation Script"
echo "              LLM Token Optimization Gateway"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}[ERROR]${NC} pyproject.toml not found!"
    echo ""
    echo "Please run this script from the SKgate project directory:"
    echo "  cd /path/to/squeeze-gateway"
    echo "  ./install.sh"
    echo ""
    exit 1
fi

# Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo ""
    echo "Please install Python 3.10 or higher:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}[OK]${NC} Python $PYTHON_VERSION found"
echo ""

# Check pip
echo "[2/5] Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} pip not found, installing..."
    python3 -m ensurepip --upgrade
fi
echo -e "${GREEN}[OK]${NC} pip is available"
echo ""

# Upgrade pip
echo "[3/5] Upgrading pip to latest version..."
python3 -m pip install --upgrade pip --quiet
echo -e "${GREEN}[OK]${NC} pip upgraded"
echo ""

# Install package
echo "[4/5] Installing SKgate CLI..."
echo "This may take a minute..."
python3 -m pip install -e . --quiet
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Installation failed!"
    echo ""
    echo "Try manual installation:"
    echo "  pip3 install -e ."
    echo ""
    exit 1
fi
echo -e "${GREEN}[OK]${NC} SKgate CLI installed successfully"
echo ""

# Verify installation
echo "[5/5] Verifying installation..."
if ! command -v sqz &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} 'sqz' command not found in PATH"
    echo ""
    echo "You may need to add pip's bin directory to PATH:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Add this line to your shell config (~/.bashrc or ~/.zshrc)"
    echo ""
else
    echo -e "${GREEN}[OK]${NC} Installation verified"
    sqz --version
fi

echo ""
echo "============================================================"
echo "                  Installation Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Reload your shell or run:"
echo "     source ~/.bashrc  (or ~/.zshrc for zsh)"
echo ""
echo "  2. Initialize configuration:"
echo "     sqz install"
echo ""
echo "  3. Add your Gemini API key:"
echo "     sqz keys add mykey YOUR_GEMINI_API_KEY"
echo ""
echo "  4. Start the gateway:"
echo "     sqz start --daemon"
echo ""
echo "  5. Try interactive chat:"
echo "     sqz chat"
echo ""
echo "For help:"
echo "  sqz --help"
echo "  sqz keys --help"
echo ""
echo "Documentation:"
echo "  https://github.com/coffe-skelet/Sqgateway"
echo ""
echo "GitHub Pages (live demo):"
echo "  https://coffe-skelet.github.io/Sqgateway/"
echo ""
echo "============================================================"
echo ""
