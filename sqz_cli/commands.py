"""Squeeze Gateway CLI command implementations."""

import json
import os
from pathlib import Path

import httpx

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from .runtime import (
    find_pid_on_port,
    start_server_process,
    stop_gateway,
    stop_server_process,
    wait_until_healthy,
    write_json,
)
from .utils import (
    clear_gateway_pid,
    ensure_config_dir,
    format_number,
    format_percentage,
    get_config_file,
    get_gateway_state,
    print_banner,
    print_error,
    print_info,
    print_success,
    print_warning,
    save_gateway_pid,
    check_gateway_running,
    process_is_alive,
)
from . import keys as keys_module


def load_config() -> dict:
    """Load the TOML config, returning empty defaults when it is absent."""
    path = get_config_file()
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def config_value(key: str, default=None):
    """Read a dotted key from the TOML config."""
    value = load_config()
    for segment in key.split("."):
        if not isinstance(value, dict) or segment not in value:
            return default
        value = value[segment]
    return value


def gateway_url(host: str | None = None, port: int | None = None) -> str:
    """Build a consistently formatted gateway URL."""
    state = get_gateway_state()
    host = host or state.get("host") or config_value("gateway.host", "127.0.0.1")
    port = port or state.get("port") or config_value("gateway.port", 8082)
    return f"http://{host}:{port}"


def configured_gateway_endpoint() -> tuple[str, int]:
    """Return the running endpoint when available, otherwise the config values."""
    state = get_gateway_state()
    host = state.get("host") or config_value("gateway.host", "127.0.0.1")
    port = int(state.get("port") or config_value("gateway.port", 8082))
    return str(host), port



async def config_command(args) -> int:
    """Read and update the user TOML configuration."""
    import tomli_w

    config_file = get_config_file()
    if not config_file.exists():
        print_error("Configuration not found. Run 'sqz install' first.")
        return 1

    config = load_config()
    action = args.config_action or "list"

    if action == "list":
        print("Current configuration:\n")
        display = {section: dict(values) for section, values in config.items()}
        api = display.get("api", {})
        if api.get("gemini_api_key"):
            api["gemini_api_key"] = "<configured>"
        print(tomli_w.dumps(display))
        return 0

    if action == "get":
        key = "api.gemini_api_key" if args.key == "api_key" else args.key
        value = config
        try:
            for segment in key.split("."):
                value = value[segment]
        except (KeyError, TypeError):
            print_error(f"Configuration key not found: {args.key}")
            return 1
        if key == "api.gemini_api_key" and value:
            value = "<configured>"
        print(value)
        return 0

    if action == "set":
        key = "api.gemini_api_key" if args.key == "api_key" else args.key
        value = args.value
        if key != "api.gemini_api_key":
            try:
                value = tomllib.loads(f"value = {value}")["value"]
            except tomllib.TOMLDecodeError:
                pass

        target = config
        segments = key.split(".")
        for segment in segments[:-1]:
            child = target.setdefault(segment, {})
            if not isinstance(child, dict):
                print_error(f"Cannot set {args.key}: {segment} is not a section")
                return 1
            target = child
        target[segments[-1]] = value
        with config_file.open("wb") as handle:
            tomli_w.dump(config, handle)

        shown = "<configured>" if key == "api.gemini_api_key" else value
        print_success(f"Configuration updated: {args.key} = {shown}")
        return 0

    print_error(f"Unknown config action: {action}")
    return 1


async def install_command(args) -> int:
    """Create the user configuration without deleting existing values."""
    import tomli_w

    print_banner()
    config_file = get_config_file()
    ensure_config_dir()
    if config_file.exists() and not args.force:
        print_info(f"Configuration already exists: {config_file}")
        print_info("Use --force to replace it with defaults")
        return 0

    config = {
        "gateway": {
            "host": "127.0.0.1",
            "port": 8082,
            "upstream": "https://generativelanguage.googleapis.com/v1beta",
        },
        "optimization": {
            "default_mode": "auto",
            "default_thinking": "auto",
            "llm_compression_threshold": 2000,
        },
        "api": {"gemini_api_key": ""},
        "models": {"default": "gemini-2.5-flash"},
        "logging": {"level": "INFO", "metrics_file": "logs/metrics.jsonl"},
    }
    with config_file.open("wb") as handle:
        tomli_w.dump(config, handle)
    print_success(f"Created configuration file: {config_file}")
    print_info(f"Config directory: {ensure_config_dir()}")
    print("\nNext steps:")
    print("  sqz config set api_key YOUR_GEMINI_KEY")
    print("  sqz start --daemon")
    print("  sqz chat")
    return 0



def gateway_environment(host: str, port: int) -> dict[str, str]:
    """Merge TOML settings into the server process environment."""
    env = os.environ.copy()
    api_key = config_value("api.gemini_api_key", "") or env.get("GEMINI_API_KEY", "")
    upstream = config_value("gateway.upstream", env.get("GEMINI_UPSTREAM", ""))
    model = config_value("models.default", "gemini-2.5-flash")
    env["GATEWAY_PORT"] = str(port)
    env["SQZ_CONFIG_DIR"] = str(ensure_config_dir())
    env["GEMINI_MODEL"] = env.get("GEMINI_MODEL", model)
    if api_key:
        env["GEMINI_API_KEY"] = api_key
    if upstream:
        env["GEMINI_UPSTREAM"] = upstream
    return env


async def ensure_gateway(host: str, port: int) -> int:
    """Start a background gateway if it is not already available."""
    url = gateway_url(host, port)
    if wait_until_healthy(url, timeout=1.0):
        return 0
    if check_gateway_running():
        print_warning("A gateway process exists but is not responding; stopping it")
        pid = int((ensure_config_dir() / "gateway.pid").read_text().strip())
        stop_server_process(pid)
        clear_gateway_pid()

    env = gateway_environment(host, port)
    log_path = ensure_config_dir() / "gateway.log"
    process = start_server_process(host, port, env, log_path)
    save_gateway_pid(process.pid)
    write_json(ensure_config_dir() / "gateway.json", {
        "pid": process.pid, "host": host, "port": port,
    })
    health = wait_until_healthy(url)
    if not health:
        print_error("Gateway did not start. See: " + str(log_path))
        stop_server_process(process.pid)
        clear_gateway_pid()
        return 1
    return 0


async def start_command(args) -> int:
    """Start the packaged gateway in the foreground or background."""
    host = args.host or config_value("gateway.host", "127.0.0.1")
    port = args.port or int(config_value("gateway.port", 8082))
    url = gateway_url(host, port)

    if wait_until_healthy(url, timeout=1.0):
        print_info(f"Gateway is already running at {url}")
        return 0
    if check_gateway_running():
        print_warning("A gateway process is registered but not responding")
        print_info("Run 'sqz stop' and try again")
        return 1

    env = gateway_environment(host, port)
    if args.daemon:
        if await ensure_gateway(host, port):
            return 1
        state = get_gateway_state()
        print_success(f"Gateway started in background (PID: {state.get('pid')})")
        print_info(f"Gateway URL: {url}")
        print_info(f"Logs: {ensure_config_dir() / 'gateway.log'}")
        return 0

    print_info(f"Starting gateway at {url} (Ctrl+C to stop)")
    process = start_server_process(
        host, port, env, ensure_config_dir() / "gateway.log", foreground=True
    )
    try:
        return process.wait()
    except KeyboardInterrupt:
        stop_server_process(process.pid)
        print_info("Gateway stopped")
        return 0



async def stop_command(args) -> int:
    """Stop the registered gateway process."""
    state = get_gateway_state()
    pid = state.get("pid")
    url = gateway_url()
    if not pid and check_gateway_running():
        try:
            pid = int((ensure_config_dir() / "gateway.pid").read_text().strip())
        except (OSError, ValueError):
            pid = None
    if not pid:
        if wait_until_healthy(url, timeout=1.0):
            print_info(f"Gateway is running outside this config at {url}")
            print_info("Stop that process from the terminal where it was started")
            return 0
        print_info("Gateway is not running")
        return 0

    if not process_is_alive(int(pid)):
        port = int(state.get("port") or config_value("gateway.port", 8082))
        pid = find_pid_on_port(port)
        if pid:
            state["pid"] = pid
            write_json(ensure_config_dir() / "gateway.json", state)

    print_info(f"Stopping gateway (PID: {pid})...")
    port = int(state.get("port") or config_value("gateway.port", 8082))
    if stop_gateway(int(pid), port, url):
        clear_gateway_pid()
        print_success("Gateway stopped")
        return 0
    print_error("Gateway did not stop cleanly")
    return 1



async def status_command(args) -> int:
    """Print process health and optimization totals."""
    host, port = configured_gateway_endpoint()
    url = gateway_url(host, port)
    print(f"Checking Squeeze Gateway at {url}...\n")
    if not check_gateway_running() and not wait_until_healthy(url, timeout=1.0):
        print_error("Gateway process is not running")
        print_info("Start it with: sqz start --daemon")
        return 1

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(f"{url}/health")
            response.raise_for_status()
            health = response.json()
            print_success("Gateway API is responding")
            print(f"  Status:       {health.get('status', 'unknown')}")
            print(f"  Version:      {health.get('version', 'unknown')}")
            print(f"  Default model: {health.get('model', 'unknown')}")
            print(f"  API key:      {'configured' if health.get('key_configured') else 'not configured'}")

            summary = (await client.get(f"{url}/api/summary")).json()
            stats = summary.get("stats", {})
            print("\nOptimization:")
            print(f"  Requests:     {format_number(stats.get('requests', 0))}")
            print(f"  Tokens saved: {format_number(stats.get('net_tokens_saved', 0))}")
            print(f"  Savings:      {format_percentage(stats.get('savings_pct', 0))}")
            print(f"  Avg latency:  {stats.get('avg_latency_ms', 0):.0f} ms")
            return 0
    except Exception as exc:
        print_error(f"Cannot connect to gateway API: {exc}")
        print_info(f"Logs: {ensure_config_dir() / 'gateway.log'}")
        return 1



async def chat_command(args) -> int:
    """Run a one-shot prompt or the interactive terminal chat."""
    from .chat import InteractiveChat

    host, port = configured_gateway_endpoint()
    if await ensure_gateway(host, port):
        return 1

    chat = InteractiveChat(
        model=args.model or config_value("models.default", "gemini-2.5-flash"),
        mode=args.mode or config_value("optimization.default_mode", "auto"),
        thinking=args.thinking or config_value("optimization.default_thinking", "auto"),
        base_url=gateway_url(host, port),
    )
    if args.message:
        return await chat.run_once(" ".join(args.message))
    return await chat.run()



async def stats_command(args) -> int:
    """View optimization statistics."""
    url = gateway_url()
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            data = (await client.get(f"{url}/api/summary")).json()
            stats = data.get("stats", {})

            print("Squeeze Gateway Statistics\n")
            print("=" * 60)
            print("OVERALL STATISTICS")
            print("=" * 60)
            print(f"Total Requests:       {format_number(stats.get('requests', 0))}")
            print(f"Tokens Saved:         {format_number(stats.get('net_tokens_saved', 0))}")
            print(f"Savings Rate:         {format_percentage(stats.get('savings_pct', 0))}")
            print(f"Average Latency:      {stats.get('avg_latency_ms', 0):.0f}ms")

            requests = (await client.get(f"{url}/metrics", params={"limit": args.limit})).json()
            if requests:
                print("\n" + "=" * 60)
                print(f"RECENT REQUESTS (last {len(requests)})")
                print("=" * 60)
                print(f"{'Mode':<8} {'Input':<8} {'Baseline':<9} {'Saved':<8} {'Think':<8} {'Time':<8}")
                print("-" * 60)
                for row in requests:
                    print(
                        f"{row.get('mode_label', '-'):<8}"
                        f"{row.get('input', 0):<8}"
                        f"{row.get('baseline', 0):<9}"
                        f"{row.get('saved', 0):<8}"
                        f"{row.get('thought', 0):<8}"
                        f"{row.get('latency_ms', 0) / 1000:<8.1f}s"
                    )

            if args.export:
                args.export.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print_success(f"Statistics exported to: {args.export}")
            return 0
    except Exception as exc:
        print_error(f"Failed to fetch statistics: {exc}")
        print_info("Make sure gateway is running: sqz start --daemon")
        return 1


async def proxy_command(args) -> int:
    """Start the gateway and print its Gemini-compatible base URL."""
    host, port = configured_gateway_endpoint()
    host = args.host or host
    port = args.port or port
    if args.show_url:
        print(gateway_url(host, port))
        return 0

    start_args = type(
        "StartArgs", (), {"host": host, "port": port, "daemon": args.daemon}
    )
    result = await start_command(start_args)
    if result == 0:
        print_info(f"Gemini-compatible base URL: {gateway_url(host, port)}")
    return result


async def keys_command(args) -> int:
    """Manage API keys."""
    action = args.keys_action or "list"

    if action == "list":
        return keys_module.list_keys()

    elif action == "add":
        return keys_module.add_key(
            name=args.name,
            key=args.key,
            provider=args.provider,
            description=args.description
        )

    elif action == "remove":
        return keys_module.remove_key(args.name)

    elif action == "select":
        return keys_module.select_key(args.name)

    elif action == "show":
        return keys_module.show_key(args.name)

    else:
        print_error(f"Unknown keys action: {action}")
        return 1

