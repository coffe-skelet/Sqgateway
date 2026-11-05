"""API keys management for SKgate CLI"""

import json
from pathlib import Path
from typing import Dict, Optional

from .utils import (
    ensure_config_dir,
    print_error,
    print_info,
    print_success,
    print_warning,
)


def get_keys_file() -> Path:
    """Get path to keys storage file"""
    return ensure_config_dir() / "keys.json"


def load_keys() -> Dict[str, Dict[str, str]]:
    """Load all stored API keys"""
    keys_file = get_keys_file()
    if not keys_file.exists():
        return {}

    try:
        with keys_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print_error(f"Failed to load keys: {e}")
        return {}


def save_keys(keys: Dict[str, Dict[str, str]]) -> bool:
    """Save API keys to file"""
    keys_file = get_keys_file()
    try:
        with keys_file.open("w", encoding="utf-8") as f:
            json.dump(keys, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        print_error(f"Failed to save keys: {e}")
        return False


def list_keys() -> int:
    """List all stored API keys"""
    keys = load_keys()

    if not keys:
        print_info("No API keys stored")
        print_info("Add a key with: sqz keys add <name> <key>")
        return 0

    print("\n" + "="*60)
    print("  STORED API KEYS")
    print("="*60)

    active_key = keys.get("_active")

    for name, data in keys.items():
        if name == "_active":
            continue

        key_value = data.get("key", "")
        provider = data.get("provider", "gemini")
        masked_key = mask_key(key_value)

        status = "  [ACTIVE]" if name == active_key else ""
        print(f"\n  {name}{status}")
        print(f"    Provider: {provider}")
        print(f"    Key: {masked_key}")

        if "description" in data:
            print(f"    Description: {data['description']}")

    print("\n" + "="*60)

    if active_key:
        print(f"\n  Currently active: {active_key}")
    else:
        print("\n  No active key selected")
        print("  Select with: sqz keys select <name>")

    print()
    return 0


def mask_key(key: str) -> str:
    """Mask API key for display"""
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


def add_key(name: str, key: str, provider: str = "gemini", description: str = "") -> int:
    """Add a new API key"""
    if not name or not key:
        print_error("Name and key are required")
        return 1

    keys = load_keys()

    if name in keys and name != "_active":
        print_warning(f"Key '{name}' already exists")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print_info("Cancelled")
            return 0

    keys[name] = {
        "key": key,
        "provider": provider,
        "description": description,
        "added": str(Path(__file__).stat().st_mtime)
    }

    if save_keys(keys):
        print_success(f"API key '{name}' added successfully")

        # Auto-select if it's the first key
        if len([k for k in keys if k != "_active"]) == 1:
            keys["_active"] = name
            save_keys(keys)
            print_info(f"Automatically selected '{name}' as active key")

        return 0
    return 1


def remove_key(name: str) -> int:
    """Remove an API key"""
    if not name:
        print_error("Key name is required")
        return 1

    keys = load_keys()

    if name not in keys or name == "_active":
        print_error(f"Key '{name}' not found")
        return 1

    # Confirm deletion
    print_warning(f"Remove API key '{name}'?")
    response = input("Are you sure? (y/N): ").strip().lower()
    if response != 'y':
        print_info("Cancelled")
        return 0

    del keys[name]

    # Clear active if this was the active key
    if keys.get("_active") == name:
        keys["_active"] = None
        print_warning("Active key removed. Select another with: sqz keys select <name>")

    if save_keys(keys):
        print_success(f"API key '{name}' removed")
        return 0
    return 1


def select_key(name: str) -> int:
    """Select active API key"""
    if not name:
        print_error("Key name is required")
        return 1

    keys = load_keys()

    if name not in keys or name == "_active":
        print_error(f"Key '{name}' not found")
        print_info("Available keys:")
        for key_name in keys:
            if key_name != "_active":
                print(f"  - {key_name}")
        return 1

    keys["_active"] = name

    if save_keys(keys):
        print_success(f"Selected '{name}' as active API key")

        # Update config.toml with active key
        try:
            from .commands import load_config
            import tomli_w
            from .utils import get_config_file

            config = load_config()
            config.setdefault("api", {})["gemini_api_key"] = keys[name]["key"]

            with get_config_file().open("wb") as f:
                tomli_w.dump(config, f)

            print_info("Configuration updated")
        except Exception as e:
            print_warning(f"Could not update config: {e}")

        return 0
    return 1


def show_key(name: str) -> int:
    """Show details of a specific API key"""
    if not name:
        print_error("Key name is required")
        return 1

    keys = load_keys()

    if name not in keys or name == "_active":
        print_error(f"Key '{name}' not found")
        return 1

    data = keys[name]
    active_key = keys.get("_active")

    print("\n" + "="*60)
    print(f"  API KEY: {name}")
    print("="*60)
    print(f"\n  Status: {'ACTIVE' if name == active_key else 'Inactive'}")
    print(f"  Provider: {data.get('provider', 'gemini')}")
    print(f"  Key: {mask_key(data.get('key', ''))}")

    if "description" in data:
        print(f"  Description: {data['description']}")

    print("\n  To view full key, edit: " + str(get_keys_file()))
    print("\n" + "="*60 + "\n")

    return 0


def get_active_key() -> Optional[str]:
    """Get the currently active API key value"""
    keys = load_keys()
    active_name = keys.get("_active")

    if not active_name or active_name not in keys:
        return None

    return keys[active_name].get("key")
