"""
Squeeze Gateway CLI - Commands implementation
"""

import os
import sys
import json
import asyncio
import signal
import subprocess
from pathlib import Path
from typing import Optional
import httpx

from .utils import (
    logger,
    print_banner,
    print_success,
    print_error,
    print_info,
    print_warning,
    format_number,
    format_percentage,
    ensure_config_dir,
    get_config_file,
    check_gateway_running,
    save_gateway_pid,
    clear_gateway_pid,
)


async def install_command(args) -> int:
    """Install and configure Squeeze Gateway"""
    print_banner()
    print_info("Installing Squeeze Gateway CLI...")

    # Create config directory
    config_dir = ensure_config_dir()
    print_success(f"Configuration directory: {config_dir}")

    # Create default config file
    config_file = get_config_file()

    if config_file.exists() and not args.force:
        print_warning(f"Configuration already exists at {config_file}")
        print_info("Use --force to overwrite")
        return 1

    default_config = """# Squeeze Gateway Configuration

[gateway]
host = "127.0.0.1"
port = 8082
upstream = "https://generativelanguage.googleapis.com"

[optimization]
# Compression mode: auto, cpp, llm, off
default_mode = "auto"

# Thinking level: auto, low, medium, high, "-" (don't interfere)
default_thinking = "auto"

# Enable LLM compression for prompts >= N characters
llm_compression_threshold = 2000

[api]
# Set your Gemini API key
# You can also use GEMINI_API_KEY environment variable
gemini_api_key = ""

[models]
default = "gemini-3.6-flash"

[logging]
# Log level: DEBUG, INFO, WARNING, ERROR
level = "INFO"
metrics_file = "logs/metrics.jsonl"
"""

    config_file.write_text(default_config)
    print_success(f"Created configuration file: {config_file}")

    # Create logs directory
    logs_dir = Path.cwd() / "logs"
    logs_dir.mkdir(exist_ok=True)
    print_success(f"Created logs directory: {logs_dir}")

    print("\n" + "="*60)
    print_success("Installation complete!")
    print("\nNext steps:")
    print("  1. Configure your Gemini API key:")
    print(f"     sqz config set api_key YOUR_API_KEY")
    print("\n  2. Start the gateway:")
    print(f"     sqz start")
    print("\n  3. Try interactive chat:")
    print(f"     sqz chat")
    print("="*60 + "\n")

    return 0


async def config_command(args) -> int:
    """Manage configuration"""
    import tomli
    import tomli_w

    config_file = get_config_file()

    if not config_file.exists():
        print_error("Configuration not found. Run 'sqz install' first.")
        return 1

    # Load config
    with open(config_file, 'rb') as f:
        config = tomli.load(f)

    if args.config_action == 'list':
        # List all configuration
        print("📋 Current configuration:\n")
        print(tomli_w.dumps(config))
        return 0

    elif args.config_action == 'get':
        # Get specific value
        keys = args.key.split('.')
        value = config
        try:
            for key in keys:
                value = value[key]
            print(value)
            return 0
        except KeyError:
            print_error(f"Configuration key not found: {args.key}")
            return 1

    elif args.config_action == 'set':
        # Set specific value
        if args.key == 'api_key':
            if 'api' not in config:
                config['api'] = {}
            config['api']['gemini_api_key'] = args.value
        else:
            keys = args.key.split('.')
            target = config
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            target[keys[-1]] = args.value

        # Save config
        with open(config_file, 'wb') as f:
            tomli_w.dump(config, f)

        print_success(f"Configuration updated: {args.key} = {args.value}")
        return 0

    return 0


async def start_command(args) -> int:
    """Start gateway server"""

    if check_gateway_running():
        print_warning("Gateway is already running")
        print_info("Use 'sqz stop' to stop it first")
        return 1

    print_info(f"Starting Squeeze Gateway on {args.host}:{args.port}...")

    # Find server.py in current directory or parent
    server_path = None
    for path in [Path.cwd() / "server.py", Path(__file__).parent.parent / "server.py"]:
        if path.exists():
            server_path = path
            break

    if not server_path:
        print_error("server.py not found")
        print_info("Make sure you're in the Squeeze Gateway directory")
        return 1

    # Start server
    if args.daemon:
        # Background mode
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "server:app",
             "--host", args.host, "--port", str(args.port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=server_path.parent
        )
        save_gateway_pid(process.pid)
        print_success(f"Gateway started in background (PID: {process.pid})")
        print_info(f"Gateway URL: http://{args.host}:{args.port}")
        print_info("Use 'sqz status' to check health")
        print_info("Use 'sqz stop' to stop the gateway")
    else:
        # Foreground mode
        print_info("Starting in foreground mode (Ctrl+C to stop)...")
        print_info(f"Gateway URL: http://{args.host}:{args.port}\n")

        try:
            process = subprocess.run(
                [sys.executable, "-m", "uvicorn", "server:app",
                 "--host", args.host, "--port", str(args.port)],
                cwd=server_path.parent
            )
            return process.returncode
        except KeyboardInterrupt:
            print("\n\n⚡ Gateway stopped")
            return 0

    return 0


async def stop_command(args) -> int:
    """Stop gateway server"""

    if not check_gateway_running():
        print_info("Gateway is not running")
        return 0

    pid_file = ensure_config_dir() / 'gateway.pid'
    pid = int(pid_file.read_text().strip())

    print_info(f"Stopping gateway (PID: {pid})...")

    try:
        os.kill(pid, signal.SIGTERM)
        print_success("Gateway stopped")
        clear_gateway_pid()
        return 0
    except OSError as e:
        print_error(f"Failed to stop gateway: {e}")
        clear_gateway_pid()
        return 1


async def status_command(args) -> int:
    """Check gateway status"""

    print("🔍 Checking Squeeze Gateway status...\n")

    # Check if process is running
    is_running = check_gateway_running()

    if is_running:
        pid_file = ensure_config_dir() / 'gateway.pid'
        pid = int(pid_file.read_text().strip())
        print_success(f"Gateway process running (PID: {pid})")
    else:
        print_error("Gateway process not running")
        print_info("Start with: sqz start")
        return 1

    # Try to connect to gateway
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8082/health", timeout=2.0)
            data = response.json()

            print_success("Gateway API responding")
            print(f"\n📊 Gateway Health:")
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Version: {data.get('version', 'unknown')}")
            print(f"  API Key: {'✅ Configured' if data.get('key_configured') else '❌ Not configured'}")
            print(f"  Uptime: {data.get('uptime', 'unknown')}")

            # Get stats
            stats_response = await client.get("http://127.0.0.1:8082/api/summary")
            stats = stats_response.json()

            if stats.get('stats'):
                s = stats['stats']
                print(f"\n📈 Statistics:")
                print(f"  Total requests: {format_number(s.get('requests', 0))}")
                print(f"  Tokens saved: {format_number(s.get('net_tokens_saved', 0))}")
                print(f"  Savings: {format_percentage(s.get('savings_pct', 0))}")
                print(f"  Avg latency: {s.get('avg_latency_ms', 0):.0f}ms")

            return 0

    except Exception as e:
        print_error(f"Cannot connect to gateway API: {e}")
        print_info("Gateway may be starting up or on different port")
        return 1


async def chat_command(args) -> int:
    """Interactive chat mode"""
    from .chat import InteractiveChat

    print_banner()

    # Check if gateway is running
    if not check_gateway_running():
        print_warning("Gateway is not running. Starting it now...")
        start_args = type('obj', (object,), {
            'host': '127.0.0.1',
            'port': 8082,
            'daemon': True
        })()
        await start_command(start_args)
        await asyncio.sleep(2)  # Wait for startup

    chat = InteractiveChat(
        model=args.model,
        mode=args.mode,
        thinking=args.thinking
    )

    return await chat.run()


async def stats_command(args) -> int:
    """View optimization statistics"""

    print("📊 Squeeze Gateway Statistics\n")

    try:
        async with httpx.AsyncClient() as client:
            # Get summary
            summary = await client.get("http://127.0.0.1:8082/api/summary")
            data = summary.json()

            s = data.get('stats', {})

            print("=" * 60)
            print("OVERALL STATISTICS")
            print("=" * 60)
            print(f"Total Requests:       {format_number(s.get('requests', 0))}")
            print(f"Tokens Saved:         {format_number(s.get('net_tokens_saved', 0))}")
            print(f"Savings Rate:         {format_percentage(s.get('savings_pct', 0))}")
            print(f"Average Latency:      {s.get('avg_latency_ms', 0):.0f}ms")
            print()

            # Get recent requests
            metrics = await client.get(f"http://127.0.0.1:8082/metrics?limit={args.limit}")
            requests = metrics.json()

            if requests:
                print("=" * 60)
                print(f"RECENT REQUESTS (last {len(requests)})")
                print("=" * 60)
                print(f"{'Mode':<8} {'Input':<8} {'Baseline':<8} {'Saved':<8} {'Think':<8} {'Time':<8}")
                print("-" * 60)

                for r in requests:
                    mode = r.get('mode_label', '-')
                    input_tok = r.get('input', 0)
                    baseline = r.get('baseline', 0)
                    saved = r.get('saved', 0)
                    think = r.get('thought', 0)
                    latency = r.get('latency_ms', 0) / 1000

                    print(f"{mode:<8} {input_tok:<8} {baseline:<8} {saved:<8} {think:<8} {latency:<8.1f}s")

            print()

            # Export if requested
            if args.export:
                args.export.write_text(json.dumps(data, indent=2))
                print_success(f"Statistics exported to: {args.export}")

            return 0

    except Exception as e:
        print_error(f"Failed to fetch statistics: {e}")
        print_info("Make sure gateway is running: sqz start")
        return 1
