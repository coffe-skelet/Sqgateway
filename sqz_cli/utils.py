"""
Squeeze Gateway CLI - Utility functions
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional


# Configure logger
logger = logging.getLogger('sqz')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def get_config_dir() -> Path:
    """Get configuration directory path"""
    return Path.home() / '.sqz'


def get_config_file() -> Path:
    """Get main configuration file path"""
    return get_config_dir() / 'config.toml'


def get_gateway_pid_file() -> Path:
    """Get gateway PID file path"""
    return get_config_dir() / 'gateway.pid'


def ensure_config_dir() -> Path:
    """Ensure configuration directory exists"""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def print_banner():
    """Print CLI banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗ ██████╗ ██╗   ██╗███████╗███████╗███████╗███████╗ ║
║   ██╔════╝██╔═══██╗██║   ██║██╔════╝██╔════╝╚══███╔╝██╔════╝ ║
║   ███████╗██║   ██║██║   ██║█████╗  █████╗    ███╔╝ █████╗   ║
║   ╚════██║██║▄▄ ██║██║   ██║██╔══╝  ██╔══╝   ███╔╝  ██╔══╝   ║
║   ███████║╚██████╔╝╚██████╔╝███████╗███████╗███████╗███████╗ ║
║   ╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝╚══════╝ ║
║                                                               ║
║              GATEWAY — LLM Token Optimizer                   ║
║                     v0.3.0 • 2026                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

    Reduce LLM token consumption by 30-60% without quality loss
    Interactive terminal agent • Transparent proxy • Real-time stats

"""
    print(banner)


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}", file=sys.stderr)


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")


def format_number(n: int) -> str:
    """Format number with thousands separators"""
    return f"{n:,}"


def format_percentage(value: float) -> str:
    """Format percentage value"""
    return f"{value:.1f}%"


def format_bytes(size: int) -> str:
    """Format byte size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def check_gateway_running() -> bool:
    """Check if gateway server is running"""
    pid_file = get_gateway_pid_file()

    if not pid_file.exists():
        return False

    try:
        pid = int(pid_file.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        # Process doesn't exist or invalid PID
        if pid_file.exists():
            pid_file.unlink()
        return False


def save_gateway_pid(pid: int):
    """Save gateway process PID"""
    pid_file = get_gateway_pid_file()
    pid_file.write_text(str(pid))


def clear_gateway_pid():
    """Clear gateway PID file"""
    pid_file = get_gateway_pid_file()
    if pid_file.exists():
        pid_file.unlink()
