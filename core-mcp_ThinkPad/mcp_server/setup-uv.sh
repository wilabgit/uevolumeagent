#!/usr/bin/env bash
# Install and setup script for UV environment
# This script initializes the uv environment for the 5G Core MCP Server

set -e

echo "================================"
echo "5G Core MCP Server - UV Setup"
echo "================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed!"
    echo ""
    echo "Install uv using:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

echo "✓ uv found: $(uv --version)"
echo ""

# Show Python version
echo "✓ Python version: $(python3 --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --all-extras

echo ""
echo "✓ Dependencies installed successfully!"
echo ""

# Show available commands
echo "Next steps:"
echo ""
echo "1. Run the server:"
echo "   make run"
echo ""
echo "2. Or use uv directly:"
echo "   uv run python3 startServer.py"
echo ""
echo "3. In another terminal, run tests:"
echo "   uv run python3 test_api.py"
echo ""
echo "For more options, run:"
echo "   make help"
echo ""
