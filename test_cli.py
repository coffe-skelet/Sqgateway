#!/usr/bin/env python3
"""
Quick test script for Squeeze Gateway CLI
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: list, description: str):
    """Run command and report result"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("""
================================================================
        Squeeze Gateway CLI - Quick Test Suite
================================================================
""")

    # Check Python version
    print(f"Python version: {sys.version}")

    # Check if sqz_cli module exists
    sqz_cli_dir = Path(__file__).parent / "sqz_cli"
    if not sqz_cli_dir.exists():
        print("❌ sqz_cli module not found")
        return 1

    print(f"[OK] sqz_cli module found at: {sqz_cli_dir}")

    # Test imports
    print("\n" + "="*60)
    print("Testing: Python imports")
    print("="*60)

    try:
        sys.path.insert(0, str(Path(__file__).parent))

        print("Importing sqz_cli.utils...")
        from sqz_cli.utils import print_banner, get_config_dir
        print("[OK] utils imported")

        print("Importing sqz_cli.commands...")
        from sqz_cli.commands import install_command
        print("[OK] commands imported")

        print("Importing sqz_cli.chat...")
        from sqz_cli.chat import InteractiveChat
        print("[OK] chat imported")

        print("\n[OK] All imports successful!")

    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test CLI entry point
    tests = [
        ([sys.executable, "-m", "sqz_cli.main", "--version"], "CLI version check"),
        ([sys.executable, "-m", "sqz_cli.main", "--help"], "CLI help"),
    ]

    passed = 0
    failed = 0

    for cmd, desc in tests:
        if run_command(cmd, desc):
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"[OK] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print("="*60)

    if failed == 0:
        print("\n[SUCCESS] All tests passed! CLI is ready to use.")
        print("\nNext steps:")
        print("  1. Install the package:")
        print("     pip install -e .")
        print("  2. Run setup:")
        print("     sqz install")
        print("  3. Configure API key:")
        print("     sqz config set api_key YOUR_KEY")
        print("  4. Start gateway:")
        print("     sqz start")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
