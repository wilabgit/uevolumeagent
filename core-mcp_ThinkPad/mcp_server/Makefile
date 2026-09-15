.PHONY: help install sync lock run test lint format clean

help:
	@echo "5G Core MCP Server - uv Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install project dependencies (creates venv)"
	@echo "  make sync         - Sync dependencies to lock file"
	@echo "  make lock         - Update lock file"
	@echo ""
	@echo "Running:"
	@echo "  make run          - Run both servers (Flask + MCP)"
	@echo "  make run-flask    - Run Flask server only"
	@echo "  make run-mcp      - Run MCP server only"
	@echo ""
	@echo "Development:"
	@echo "  make test         - Run API tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code with black"
	@echo "  make type-check   - Run type checking with mypy"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Remove cache and compiled files"
	@echo "  make update       - Update dependencies to latest versions"
	@echo ""

install:
	uv sync --all-extras

sync:
	uv sync --all-extras

lock:
	uv lock --upgrade

run:
	uv run python3 startServer.py

run-flask:
	uv run python3 callbackServer.py

run-mcp:
	uv run python3 main.py

test:
	uv run python3 test_api.py

lint:
	uv run flake8 callbackServer.py config.py data_store.py mcp_tools.py main.py startServer.py

format:
	uv run black callbackServer.py config.py data_store.py mcp_tools.py main.py startServer.py test_api.py

type-check:
	uv run mypy callbackServer.py config.py data_store.py mcp_tools.py main.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

update:
	uv lock --upgrade

.DEFAULT_GOAL := help
