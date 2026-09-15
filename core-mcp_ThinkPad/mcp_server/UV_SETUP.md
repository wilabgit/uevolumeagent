# UV Environment Setup - Summary

✅ UV environment has been successfully configured for the 5G Core MCP Callback Server.

## What Was Added

### 1. UV Configuration (`pyproject.toml`)
- Added `[tool.uv]` section with UV-specific settings
- Added `[tool.setuptools]` section to properly declare all modules
- Configured UV as the managed package manager

### 2. Makefile
A comprehensive Makefile with convenient targets:
- **Setup**: `make install`, `make sync`, `make lock`
- **Running**: `make run`, `make run-flask`, `make run-mcp`
- **Development**: `make test`, `make lint`, `make format`, `make type-check`
- **Maintenance**: `make clean`, `make update`

Run `make help` to see all available commands.

### 3. Setup Script (`setup-uv.sh`)
An automated setup script that:
- Checks for UV installation
- Displays Python version
- Installs all dependencies with `uv sync --all-extras`
- Shows next steps

Run with: `./setup-uv.sh`

### 4. Documentation Updates
- **QUICKSTART.md** - Updated with UV-specific instructions
- **README.md** - Added UV usage examples and development commands

## Prerequisites

Install UV (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:
```bash
uv --version  # Should show uv version
uv python --version  # Should show Python 3.10
```

## Quick Start

### Method 1: Using Setup Script
```bash
./setup-uv.sh
```

### Method 2: Using Make
```bash
make install
make run
```

### Method 3: Using UV Directly
```bash
uv sync --all-extras
uv run python3 startServer.py
```

## Common Tasks

### Install/Update Dependencies
```bash
make install          # Install from lock file
make update           # Update to latest versions
uv lock --upgrade     # Update lock file manually
```

### Run the Server
```bash
make run              # Run both servers
make run-flask        # Flask only
make run-mcp          # MCP only
uv run python3 startServer.py  # Direct run without Make
```

### Development
```bash
make test             # Run API tests
make lint             # Check code style
make format           # Format code
make type-check       # Type checking
make clean            # Clean cache files
```

### Check Dependencies
```bash
uv pip list           # Show installed packages
uv lock               # Show lock file contents
```

## Project Structure

```
callback-mcp-server/
├── .python-version          # Python version (3.10)
├── pyproject.toml          # Project config + UV settings
├── uv.lock                 # Dependency lock file
├── Makefile                # UV-friendly make targets
├── setup-uv.sh             # Automated setup script
│
├── callbackServer.py       # Flask HTTP server
├── main.py                 # MCP server entry point
├── startServer.py          # Combined launcher
│
├── config.py               # Configuration management
├── data_store.py           # Thread-safe data storage
├── mcp_tools.py            # MCP tool definitions
├── test_api.py             # API tests
│
├── README.md               # Full documentation
├── QUICKSTART.md           # Quick start guide
├── REFACTORING_SUMMARY.md  # Refactoring details
└── .env.example            # Configuration reference
```

## Virtual Environment

UV automatically creates and manages a virtual environment in `.venv/` directory. You don't need to manually create or activate it. All `uv run` commands use it automatically.

To manually work in the virtual environment:
```bash
# Activate (bash/zsh)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Run commands directly
python3 callbackServer.py

# Deactivate
deactivate
```

## Benefits of UV

1. **Speed**: 10-100x faster than pip/venv
2. **Simplicity**: No need to manually create/activate venvs
3. **Reproducibility**: Lock files ensure consistent environments
4. **Python Management**: Manages Python versions automatically
5. **Workspace Support**: Built-in monorepo support

## Troubleshooting

### UV not found
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Follow instructions to add to PATH
```

### Dependencies not syncing
```bash
rm uv.lock
uv sync --all-extras
```

### Port conflicts
```bash
# Change in .env or use environment variables
FLASK_PORT=9081 MCP_PORT=9080 uv run python3 startServer.py
```

### Python version mismatch
```bash
uv python --version  # Check current
cat .python-version  # Check required
# UV will handle mismatches automatically
```

## Next Steps

1. Run the server: `make run`
2. Run tests: `make test`
3. Check logs: `LOG_LEVEL=DEBUG make run`
4. Read [README.md](README.md) for full API documentation
5. Read [QUICKSTART.md](QUICKSTART.md) for detailed usage guide

## Additional Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV on GitHub](https://github.com/astral-sh/uv)
- [Python 3.10 Docs](https://docs.python.org/3.10/)

---

**Status**: ✅ UV environment fully configured and tested
**Last Updated**: March 9, 2026
