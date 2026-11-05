# SKgate CLI - Installation Guide

Complete installation guide for SKgate CLI on Windows, Linux, and macOS.

## 📋 Prerequisites

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **pip** (usually comes with Python)
- **Git** (optional, for cloning repository)

---

## 🚀 Quick Install (Recommended)

### Windows (PowerShell/CMD)

```powershell
# 1. Clone repository
git clone https://github.com/coffe-skelet/Sqgateway.git
cd Sqgateway

# 2. Run installation script
install.bat

# 3. Restart PowerShell/CMD

# 4. Verify installation
sqz --version
```

### Linux / macOS (Bash/Zsh)

```bash
# 1. Clone repository
git clone https://github.com/coffe-skelet/Sqgateway.git
cd Sqgateway

# 2. Make script executable and run
chmod +x install.sh
./install.sh

# 3. Reload shell
source ~/.bashrc  # or ~/.zshrc for zsh

# 4. Verify installation
sqz --version
```

---

## 📦 Manual Installation

If the automatic script doesn't work, follow these steps:

### Step 1: Navigate to Project Directory

```bash
cd C:\path\to\Sqgateway  # Windows
cd /path/to/Sqgateway     # Linux/macOS
```

**Important:** Make sure you see `pyproject.toml` in the directory:
```bash
dir pyproject.toml   # Windows
ls pyproject.toml    # Linux/macOS
```

### Step 2: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 3: Install Package

```bash
python -m pip install -e .
```

**What this does:**
- `-e` = editable mode (install from source)
- `.` = current directory

### Step 4: Verify Installation

```bash
sqz --version
```

**If "sqz: command not found":**

Windows:
- Close and reopen PowerShell/CMD
- Or add to PATH: `%APPDATA%\Python\Python3X\Scripts`

Linux/macOS:
- Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`
- Add this to `~/.bashrc` or `~/.zshrc`

---

## ⚙️ Initial Setup

### 1. Initialize Configuration

```bash
sqz install
```

This creates `~/.sqz/config.toml` with default settings.

### 2. Add API Key

SKgate supports multiple API keys. Add your first one:

```bash
sqz keys add personal YOUR_GEMINI_API_KEY --description "My personal key"
```

**Get Gemini API key:** https://ai.google.dev/aistudio

### 3. Start Gateway

```bash
# Background mode (recommended)
sqz start --daemon

# Foreground mode (see logs)
sqz start
```

### 4. Test Chat

```bash
sqz chat
```

**Chat commands:**
- `/exit` - quit
- `/clear` - clear history
- `/stats` - show session stats
- `/mode auto` - change compression mode
- `/thinking low` - change thinking level

---

## 🔑 Managing API Keys

SKgate allows multiple API keys for different accounts/providers:

```bash
# List all keys
sqz keys list

# Add new key
sqz keys add work AIza... --provider gemini --description "Work account"

# Switch active key
sqz keys select work

# Show key details
sqz keys show personal

# Remove key
sqz keys remove old_key
```

**Active key** is automatically synced to `config.toml` and used by gateway.

---

## 📊 Available Commands

```bash
sqz --help           # Show all commands
sqz --version        # Show version

# Setup
sqz install          # Initialize configuration
sqz config list      # Show configuration
sqz config set KEY VALUE  # Set config value

# Gateway Management
sqz start            # Start gateway (foreground)
sqz start --daemon   # Start gateway (background)
sqz stop             # Stop gateway
sqz status           # Check gateway status

# API Keys
sqz keys list        # List all API keys
sqz keys add         # Add new API key
sqz keys select      # Select active key
sqz keys remove      # Remove API key

# Usage
sqz chat             # Interactive chat
sqz stats            # View statistics
sqz stats --export stats.json  # Export statistics
```

---

## 🐛 Troubleshooting

### Problem: "sqz: command not found"

**Solution (Windows):**
1. Close and reopen terminal
2. Run: `python -m sqz_cli.main --version`
3. If works, add Scripts folder to PATH

**Solution (Linux/macOS):**
```bash
# Find where sqz is installed
python3 -m pip show squeeze-gateway

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Problem: "pyproject.toml not found"

**Solution:**
You're in the wrong directory. Navigate to the project:
```bash
cd C:\path\to\Sqgateway
dir pyproject.toml  # Should see the file
```

### Problem: Gateway won't start

**Solution:**
```bash
# Check if port is in use
netstat -ano | findstr :8082  # Windows
lsof -i :8082                 # Linux/macOS

# Try different port
sqz start --port 8083
```

### Problem: Python not found

**Solution:**
1. Install Python 3.10+ from https://python.org
2. **Important:** Check "Add Python to PATH" during installation
3. Verify: `python --version`

### Problem: ModuleNotFoundError

**Solution:**
```bash
# Reinstall dependencies
pip install -e . --force-reinstall

# Or install manually
pip install fastapi uvicorn httpx python-dotenv tomli tomli-w
```

---

## 🎓 Usage Examples

### Example 1: Basic Chat

```bash
sqz start --daemon
sqz chat
> What is quantum entanglement?
```

### Example 2: Multiple API Keys

```bash
# Add keys for different purposes
sqz keys add personal AIza...123 --description "Personal projects"
sqz keys add work AIza...456 --description "Work projects"
sqz keys add testing AIza...789 --description "Testing"

# Switch between keys
sqz keys select work
sqz chat  # Uses work key

sqz keys select personal
sqz chat  # Uses personal key
```

### Example 3: Configuration

```bash
# Set default compression mode
sqz config set optimization.default_mode auto

# Set default thinking level
sqz config set optimization.default_thinking low

# View all settings
sqz config list
```

### Example 4: Statistics

```bash
# View optimization stats
sqz stats

# Last 20 requests
sqz stats --limit 20

# Export to file
sqz stats --export report.json
```

---

## 📚 Additional Resources

- **GitHub Repository:** https://github.com/coffe-skelet/Sqgateway
- **GitHub Pages (Demo):** https://coffe-skelet.github.io/Sqgateway/
- **Documentation:** See README.md, CLI_README.md, QUICKSTART.md
- **Issues:** https://github.com/coffe-skelet/Sqgateway/issues

---

## 🔄 Updating

```bash
# Pull latest changes
cd Sqgateway
git pull origin main

# Reinstall
python -m pip install -e . --force-reinstall

# Or use script
install.bat  # Windows
./install.sh # Linux/macOS
```

---

## ❓ Still Having Issues?

1. **Check Python version:** `python --version` (must be 3.10+)
2. **Check if in project directory:** `ls pyproject.toml`
3. **Try manual install:** `python -m pip install -e .`
4. **Check logs:** `~/.sqz/gateway.log`
5. **Open issue:** https://github.com/coffe-skelet/Sqgateway/issues

---

**Made with ❤️ by [@kirill_skoch](https://t.me/kirill_skoch)**  
**Version:** 0.4.0  
**Last Updated:** 2026-11-05
