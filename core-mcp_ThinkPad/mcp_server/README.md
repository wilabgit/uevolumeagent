# 5G Core MCP Callback Server

A dual-server application for handling 5G Core network SMF (Session Management Function) Event Exposure callbacks with MCP (Model Context Protocol) tool access.

## Overview

This project provides:

1. **Flask HTTP Server** - Receives USAGE_REPORT events from the SMF
2. **MCP Server** - Provides tool-based access to stored event data
3. **Thread-Safe Data Store** - In-memory storage with configurable capacity and UE indexing

## Features

- ✅ Receive and validate SMF event notifications
- ✅ Thread-safe in-memory data storage with automatic cleanup
- ✅ MCP tools for querying stored data
- ✅ Comprehensive logging and error handling
- ✅ Environment-based configuration
- ✅ Health check and statistics endpoints
- ✅ RESTful API for data retrieval

## Quick Start

### Installation

#### Using UV (Recommended)

First, install `uv` if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then sync the project:
```bash
cd callback-mcp-server
uv sync --all-extras
```

Or use the provided setup script:
```bash
chmod +x setup-uv.sh
./setup-uv.sh
```

#### Using pip

```bash
cd callback-mcp-server
pip install -e .
```

### Running the Server

```bash (using UV (recommended))
python3 run_callbackMCPServer.py
```
or:

```bash
uv run python3 startServer.py
```

Using make:
```bash
make run
```

Using Python directly:
```bash
python3 startServer.py
```

## Configuration

Configuration is managed via environment variables. Create a `.env` file or set them directly:

```bash
# Flask settings
FLASK_HOST=0.0.0.0
FLASK_PORT=8081
FLASK_DEBUG=False

# MCP settings
MCP_HOST=0.0.0.0
MCP_PORT=8080
MCP_TRANSPORT=http

# Server identification
MCP_SERVER_NAME=5g-core-mcp

# Logging
LOG_LEVEL=INFO

# Data storage
MAX_REPORTS=10000
```

## API Endpoints

### Flask Server (Callback Receiver)

#### POST `/callbacks/volume`
Receives SMF event notifications.

**Request body:**
```json
{
  "notifId": "string",
  "eventNotifs": [
    {
      "supi": "208950000000031",
      "event": "QOS_MON",
      "timeStamp": "1234567890",
      "customized_data": {
        "Usage Report": {
          "Volume": {
            "Uplink": 1000,
            "Downlink": 2000,
            "Total": 3000
          },
          "Duration": 10,
          "Trigger": "Periodic Reporting"
        }
      }
    }
  ]
}
```

**Response:**
```json
{
  "status": "ok",
  "notifId": "string"
}
```

#### GET `/callbacks/data`
Retrieve all stored reports.

**Response:**
```json
{
  "count": 42,
  "reports": [...]
}
```

#### GET `/callbacks/stats`
Get storage statistics.

**Response:**
```json
{
  "total_reports": 42,
  "total_ues": 5,
  "max_reports": 10000,
  "ues": ["208950000000031", "208950000000032", ...]
}
```

#### GET `/callbacks/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## MCP Tools

The MCP server provides the following tools:

### `get_ue_volume(ue_supi: str) -> str`
Get usage volume data for a specific UE.

**Parameters:**
- `ue_supi`: The SUPI (Subscription Permanent Identifier) of the UE

**Example call:**
```bash
mcp call get_ue_volume '{"ue_supi": "208950000000031"}'
```

### `list_all_ues() -> str`
List all UEs with stored reports.

### `get_statistics() -> str`
Get overall statistics about stored reports.

### `get_latest_report(ue_supi: str) -> str`
Get the most recent report for a specific UE.

### `get_ue_count() -> str`
Get the count of UEs with stored reports.

## Project Structure

```
callback-mcp-server/
├── callbackServer.py    # Flask HTTP server for receiving callbacks
├── main.py             # MCP server entry point
├── startServer.py      # Combined entry point (both servers)
├── config.py           # Configuration management
├── data_store.py       # Thread-safe data storage
├── mcp_tools.py        # MCP tool definitions
├── pyproject.toml      # Project metadata and dependencies
├── README.md           # This file
└── .env                # Environment configuration (create as needed)
```

## Data Model

### Event Notification Structure
```python
{
  "notifId": str,
  "eventNotifs": [
    {
      "supi": str,
      "event": str,
      "timeStamp": int,
      "customized_data": {
        "Usage Report": {
          "Volume": {
            "Uplink": int,
            "Downlink": int,
            "Total": int
          },
          "Duration": int,
          "Trigger": str
        }
      }
    }
  ]
}
```

## Thread Safety

The application uses thread-safe data structures:
- `threading.Lock` for data store access
- Thread-safe list operations
- Immutable snapshots for reads

Multiple concurrent requests can safely access the data store simultaneously.

## Logging

Logs are configured at the module level using Python's `logging` module. Configure the log level via the `LOG_LEVEL` environment variable:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

Example output:
```
2024-03-09 14:23:45,123 [INFO] callbackServer: 📩 Received QOS_MON for UE 208950000000031 (ID: notifSMF)
2024-03-09 14:23:45,124 [DEBUG] callbackServer:   ↳ Uplink:   1000 bytes
2024-03-09 14:23:45,124 [DEBUG] callbackServer:   ↳ Downlink: 2000 bytes
```

## Error Handling

The server handles various error scenarios:
- Invalid JSON in requests (400 Bad Request)
- Missing required fields (400 Bad Request)
- Malformed event notifications (400 Bad Request)
- Server errors (500 Internal Server Error)

All errors return JSON responses with descriptive error messages.

## Development

### Running Tests

```bash
# Using UV
uv run python3 test_api.py

# Using Make
make test

# Using Python directly
python3 test_api.py
```

### Code Quality

```bash
# Using Make (recommended)
make lint         # Check code style
make format       # Format code with black
make type-check   # Type checking with mypy

# Using UV directly
uv run flake8 *.py
uv run black *.py
uv run mypy callbackServer.py
```

### Managing Dependencies

```bash
# Sync dependencies from lock file
uv sync

# Update lock file with latest versions
uv lock --upgrade

# Show installed packages
uv pip list

# Add a new dependency (experimental)
uv pip install package-name
```

### Useful Make Commands

```bash
make help          # Show all available commands
make install       # Install/sync dependencies
make run           # Run both servers
make run-flask     # Run Flask server only
make run-mcp       # Run MCP server only
make test          # Run tests
make clean         # Clean up cache files
```

## Troubleshooting

### Port Already in Use
If you get "Address already in use" error:
```bash
# Find process using port
lsof -i :8080  # for MCP
lsof -i :8081  # for Flask

# Kill the process
kill -9 <PID>
```

### Module Import Errors
Make sure you're running from the project directory and dependencies are installed:
```bash
cd callback-mcp-server
pip install -e .
```

### Connection Refused
Verify both servers are running on the configured hosts/ports:
```bash
# Check Flask server
curl http://localhost:8081/callbacks/health

# Check MCP server (if using HTTP transport)
curl http://localhost:8080/
```

## Performance Notes

- **Memory Usage**: The data store uses ~1MB per 100 stored reports (estimated)
- **Max Reports**: Default is 10,000. Adjust via `MAX_REPORTS` env var
- **Concurrency**: Thread-safe design supports multiple concurrent requests
- **Throughput**: Flask server can handle hundreds of requests/sec per core

## License

See LICENSE file for details.

## Contributing

Please follow these guidelines:
1. Write clear, descriptive commit messages
2. Add docstrings to all functions
3. Use type hints for function parameters and returns
4. Add tests for new features
5. Update this README with any user-facing changes

## Support

For issues, questions, or suggestions, please create an issue in the repository.
