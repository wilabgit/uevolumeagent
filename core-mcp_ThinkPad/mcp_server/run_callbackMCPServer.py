#!/usr/bin/env python3
"""
Simple launcher for the 5G Core MCP Callback Server.
Runs: uv run python3 startServer.py
"""

import subprocess
import sys
import os


def main():
    """Launch the server using uv."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 60)
    print("5G Core MCP Callback Server Launcher")
    print("=" * 60)
    print(f"Working directory: {script_dir}")
    print("Starting: uv run python3 startServer.py")
    print("=" * 60)
    print()
    
    try:
        # Run the command
        process = subprocess.Popen(
            ["uv", "run", "python3", "startServer.py"],
            cwd=script_dir
        )
        
        # Wait for process to complete
        return_code = process.wait()
        
        print()
        print("=" * 60)
        if return_code == 0:
            print("✓ Server stopped normally")
        else:
            print(f"✗ Server stopped with exit code: {return_code}")
        print("=" * 60)
        
        return return_code
        
    except FileNotFoundError:
        print("✗ ERROR: 'uv' command not found")
        print("Please install UV first:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        return 1
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
        return 0
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
