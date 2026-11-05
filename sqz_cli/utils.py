"""Shared CLI paths, state files and terminal output helpers."""

import logging
import os
import sys
from pathlib import Path

from .runtime import process_is_alive, read_json


logger = logging.getLogger("sqz")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

_config_dir_override: Path | None = None


def set_config_dir(path: Path | None) -> None:
    """Set the process-wide config override used by the global CLI option."""
    global _config_dir_override
    _config_dir_override = Path(path).expanduser().resolve() if path else None


def get_config_dir() -> Path:
    """Return the active configuration directory."""
    if _config_dir_override:
        return _config_dir_override
    configured = os.environ.get("SQZ_CONFIG_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / ".sqz"


def get_config_file() -> Path:
    return get_config_dir() / "config.toml"


def get_gateway_pid_file() -> Path:
    return get_config_dir() / "gateway.pid"


def get_gateway_state_file() -> Path:
    return get_config_dir() / "gateway.json"


def ensure_config_dir() -> Path:
    directory = get_config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def print_banner() -> None:
    """Print beautiful SKgate branded banner"""
    print("""
============================================================

      ███████╗██╗  ██╗ ██████╗  █████╗ ████████╗███████╗
      ██╔════╝██║ ██╔╝██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝
      ███████╗█████╔╝ ██║  ███╗███████║   ██║   █████╗
      ╚════██║██╔═██╗ ██║   ██║██╔══██║   ██║   ██╔══╝
      ███████║██║  ██╗╚██████╔╝██║  ██║   ██║   ███████╗
      ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝

           LLM Token Optimization Gateway
              Reduce token usage by 30-60%

============================================================
""")


def print_success(message: str) -> None:
    print(f"[OK] {message}")


def print_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)


def print_info(message: str) -> None:
    print(f"[INFO] {message}")


def print_warning(message: str) -> None:
    print(f"[WARN] {message}")


def format_number(value: int | float) -> str:
    return f"{value:,}"


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def check_gateway_running() -> bool:
    """Return whether the PID stored for the active config still exists."""
    pid_file = get_gateway_pid_file()
    try:
        pid = int(pid_file.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return False
    if process_is_alive(pid):
        return True
    pid_file.unlink(missing_ok=True)
    return False


def save_gateway_pid(pid: int) -> None:
    pid_file = get_gateway_pid_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(pid), encoding="ascii")


def get_gateway_state() -> dict:
    return read_json(get_gateway_state_file())


def clear_gateway_pid() -> None:
    get_gateway_pid_file().unlink(missing_ok=True)
    get_gateway_state_file().unlink(missing_ok=True)
