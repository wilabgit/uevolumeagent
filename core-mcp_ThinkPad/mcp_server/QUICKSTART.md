# Quick Start Guide

## Prerequisites

Make sure you have `uv` installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or if you use Homebrew:
```bash
brew install uv
```

Verify the installation:
```bash
uv --version  # Should show uv version
uv python --version  # Should show Python 3.10
```

## 1. Setup Environment

Run the setup script:
```bash
chmod +x setup-uv.sh
./setup-uv.sh
```

Or manually sync dependencies:
```bash
uv sync --all-extras
```

## 2. Configure (Optional)

Copy the example config:
```bash
cp .env.example .env
```

Edit `.env` if you need non-default settings:
```bash
FLASK_PORT=8081
MCP_PORT=8080
LOG_LEVEL=INFO
```

## 3. Run the Server

### Using Make (Recommended)
```bash
make run
```

### Using UV Directly
```bash
uv run python3 startServer.py
```

### Running Components Separately

Terminal 1 (Flask Callback Server):
```bash
make run-flask
# or
uv run python3 callbackServer.py
```

Terminal 2 (MCP Server):
```bash
make run-mcp
# or
uv run python3 main.py
```

## 4. Test the Server

Using Make:
```bash
make test
```

Using UV directly:
```bash
uv run python3 test_api.py
```

Expected output:
```
============================================================
5G Core MCP Callback Server - API Tests
============================================================
Target: http://localhost:8081

[TEST] Health Check
  Status: 200
  Response: {'status': 'healthy'}
  ✓ PASSED

[TEST] POST Event Notification
  Status: 200
  Response: {'status': 'ok', 'notifId': 'test-notif-001'}
  ✓ PASSED
...
============================================================
Results: 6/6 tests passed
✓ ALL TESTS PASSED
============================================================
```

## 5. Verify APIs Are Working

### Check Health
```bash
curl http://localhost:8081/callbacks/health
```

### Send Test Event
```bash
curl -X POST http://localhost:8081/callbacks/volume \
  -H "Content-Type: application/json" \
  -d '{
    "notifId": "test-001",
    "eventNotifs": [{
      "supi": "208950000000031",
      "event": "USAGE_REPORT",
      "timeStamp": "1709987000",
      "customized_data": {
        "Usage Report": {
          "Volume": {
            "Uplink": 1000,
            "Downlink": 2000,
            "Total": 3000
          },
          "Duration": 10,
          "Trigger": "Periodic"
        }
      }
    }]
  }'
```

### Get Statistics
```bash
curl http://localhost:8081/callbacks/stats
```

### Get All Reports
```bash
curl http://localhost:8081/callbacks/data
```

## 6. Use MCP Tools

If MCP client is configured correctly, you can use the tools:

```
get_ue_volume(ue_supi="208950000000031")
list_all_ues()
get_statistics()
get_latest_report(ue_supi="208950000000031")
get_ue_count()
```

## File Structure

- `callbackServer.py` - Flask app (receives events)
- `main.py` - MCP server (provides tools)
- `startServer.py` - Combined launcher (recommended)
- `config.py` - Configuration management
- `data_store.py` - Thread-safe data storage
- `mcp_tools.py` - MCP tool definitions
- `test_api.py` - Test suite
- `README.md` - Full documentation
- `REFACTORING_SUMMARY.md` - What was improved
- `Makefile` - Common commands
- `.env.example` - Configuration reference

## Ports

- **Flask Server**: 8081 (receives SMF callbacks)
- **MCP Server**: 8080 (provides tools)

If these ports conflict, change them in `.env`:
```bash
FLASK_PORT=9081
MCP_PORT=9080
```

## Common Commands

```bash
# Show all available commands
make help

# Install/sync dependencies
make install

# Run the server
make run

# Run specific server
make run-flask
make run-mcp

# Development
make test          # Run tests
make lint          # Check code style
make format        # Format code
make type-check    # Type checking
make clean         # Clean up cache files

# Update dependencies
make update
```

## Logs

By default, logs show INFO level and above. For more detail:

```bash
LOG_LEVEL=DEBUG uv run python3 startServer.py
```

## Troubleshooting

### UV not found?
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH if needed (follow installation instructions)
```

### Module not found error?
```bash
# Make sure you're in the right directory
cd /home/federico/oai-cn5g-fed-master/callback-mcp-server

# Reinstall/sync dependencies
uv sync --all-extras
```

### Port already in use?
```bash
# Find what's using the port
lsof -i :8081  # Flask
lsof -i :8080  # MCP

# Kill it
kill -9 <PID>
```

### Server won't start?
```bash
# Check Python version
uv python --version  # Should be 3.10

# Check dependencies
uv pip list | grep -E "fastmcp|flask|httpx"

# Run with debug
LOG_LEVEL=DEBUG uv run python3 startServer.py
```

## UV Tips

### Create a fresh virtual environment
```bash
uv venv --python 3.10
```

### Show what packages are installed
```bash
uv pip list
```

### Lock dependencies without installing
```bash
uv lock
```

### Running commands in the UV environment
All `uv run` commands automatically use the project's virtual environment:
```bash
uv run python3 callbackServer.py
uv run pip list
uv run python3 -m pytest
```

## Next Steps

1. Check [Makefile](Makefile) for more commands
2. Read [README.md](README.md) for full API documentation
3. Check [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for improvements
4. Configure SMF to send callbacks to `http://YOUR_HOST:8081/callbacks/volume`
5. Integrate MCP clients to query stored data via tools

