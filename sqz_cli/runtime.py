"""Operating-system and gateway process helpers."""

import json
import os
import subprocess
import sys
import time
import ctypes
from pathlib import Path
from typing import Optional

import httpx


def start_server_process(
    host: str,
    port: int,
    env: dict[str, str],
    log_path: Path,
    foreground: bool = False,
) -> subprocess.Popen:
    """Start the packaged gateway with uvicorn."""
    env = env.copy()
    package_root = str(Path(__file__).resolve().parent.parent)
    existing_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = package_root + (os.pathsep + existing_path if existing_path else "")
    command = [sys.executable, "-m", "sqz_cli.server"]
    env["GATEWAY_HOST"] = host
    env["GATEWAY_PORT"] = str(port)
    env["PYTHONUNBUFFERED"] = "1"
    if foreground:
        return subprocess.Popen(command, env=env)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("ab")
    kwargs = {
        "cwd": str(Path.home()),
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": log_file,
        "stderr": subprocess.STDOUT,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    return subprocess.Popen(command, **kwargs)


def wait_until_healthy(url: str, timeout: float = 30.0) -> Optional[dict]:
    """Poll the gateway until it is ready or the timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{url}/health", timeout=0.75)
            if response.status_code == 200:
                return response.json()
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(0.2)
    return None


def process_is_alive(pid: int) -> bool:
    """Return whether a process with the supplied PID exists."""
    if pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information, False, pid
        )
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        # Access denied still proves that the process exists.
        return ctypes.get_last_error() == 5
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_server_process(pid: int, timeout: float = 8.0) -> bool:
    """Stop a gateway process tree and wait until it exits."""
    if not process_is_alive(pid):
        return True
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.kill(pid, 15)
        except OSError:
            return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_is_alive(pid):
            return True
        time.sleep(0.15)
    return False


def stop_gateway(pid: int | None, port: int, url: str, timeout: float = 8.0) -> bool:
    """Stop the gateway tree and verify that its API actually went away."""
    candidates = []
    if pid:
        candidates.append(int(pid))
    port_pid = find_pid_on_port(port)
    if port_pid and port_pid not in candidates:
        candidates.append(port_pid)

    for candidate in candidates:
        stop_server_process(candidate, timeout=timeout)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if wait_until_healthy(url, timeout=0.2) is None:
            return True
        remaining_pid = find_pid_on_port(port)
        if remaining_pid and remaining_pid not in candidates:
            stop_server_process(remaining_pid, timeout=timeout)
        time.sleep(0.15)
    return False


def find_pid_on_port(port: int) -> Optional[int]:
    """Find the process listening on a TCP port."""
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        for line in result.stdout.splitlines():
            columns = line.split()
            if (
                len(columns) >= 5
                and columns[0].upper() == "TCP"
                and columns[1].endswith(f":{port}")
                and columns[3].upper() == "LISTENING"
            ):
                try:
                    return int(columns[4])
                except ValueError:
                    return None
        return None

    for command in (
        ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
        ["fuser", f"{port}/tcp"],
    ):
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=5, check=False
            )
        except (OSError, subprocess.SubprocessError):
            continue
        for value in result.stdout.split():
            if value.isdigit():
                return int(value)
    return None


def read_json(path: Path, default: Optional[dict] = None) -> dict:
    """Read a JSON object, returning the default for malformed files."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else (default or {})
    except (OSError, ValueError):
        return default or {}


def write_json(path: Path, value: dict) -> None:
    """Atomically write a small JSON state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)
