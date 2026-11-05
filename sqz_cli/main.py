#!/usr/bin/env python3
"""
Squeeze Gateway CLI - Terminal Agent
Interactive CLI interface for LLM token optimization gateway
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional

from .commands import (
    install_command,
    config_command,
    start_command,
    stop_command,
    status_command,
    chat_command,
    stats_command,
)
from .utils import logger, print_banner


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        prog='sqz',
        description='Squeeze Gateway - LLM Token Optimization CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sqz install              # Install and configure gateway
  sqz start                # Start gateway server
  sqz chat                 # Interactive chat mode
  sqz stats                # View optimization statistics
  sqz config set api_key   # Configure API key

For more information: https://github.com/kirill-skoch/squeeze-gateway
"""
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.3.0'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--config-dir',
        type=Path,
        help='Custom config directory (default: ~/.sqz)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install and configure gateway')
    install_parser.add_argument('--force', action='store_true', help='Overwrite existing installation')

    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_subparsers = config_parser.add_subparsers(dest='config_action')

    config_get = config_subparsers.add_parser('get', help='Get configuration value')
    config_get.add_argument('key', help='Configuration key')

    config_set = config_subparsers.add_parser('set', help='Set configuration value')
    config_set.add_argument('key', help='Configuration key')
    config_set.add_argument('value', help='Configuration value')

    config_list = config_subparsers.add_parser('list', help='List all configuration')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start gateway server')
    start_parser.add_argument('--port', type=int, default=8082, help='Server port (default: 8082)')
    start_parser.add_argument('--host', default='127.0.0.1', help='Server host (default: 127.0.0.1)')
    start_parser.add_argument('--daemon', '-d', action='store_true', help='Run in background')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop gateway server')

    # Status command
    status_parser = subparsers.add_parser('status', help='Check gateway status')

    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat mode')
    chat_parser.add_argument('--model', default='gemini-3.6-flash', help='LLM model to use')
    chat_parser.add_argument('--mode', choices=['auto', 'cpp', 'llm', 'off'], default='auto', help='Compression mode')
    chat_parser.add_argument('--thinking', choices=['auto', 'low', 'medium', 'high', '-'], default='auto', help='Thinking level')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='View optimization statistics')
    stats_parser.add_argument('--limit', type=int, default=10, help='Number of recent requests to show')
    stats_parser.add_argument('--export', type=Path, help='Export stats to file')

    # Proxy command
    proxy_parser = subparsers.add_parser('proxy', help='Quick proxy setup for existing code')
    proxy_parser.add_argument('--port', type=int, default=8082, help='Proxy port')
    proxy_parser.add_argument('--show-url', action='store_true', help='Show proxy URL to use')

    return parser


async def main_async(args: argparse.Namespace) -> int:
    """Async main entry point"""

    if args.verbose:
        logger.setLevel('DEBUG')

    # Handle commands
    if args.command == 'install':
        return await install_command(args)

    elif args.command == 'config':
        return await config_command(args)

    elif args.command == 'start':
        return await start_command(args)

    elif args.command == 'stop':
        return await stop_command(args)

    elif args.command == 'status':
        return await status_command(args)

    elif args.command == 'chat':
        return await chat_command(args)

    elif args.command == 'stats':
        return await stats_command(args)

    else:
        # No command specified - show banner and help
        print_banner()
        parser.print_help()
        return 0


def main():
    """CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        exit_code = asyncio.run(main_async(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚡ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
