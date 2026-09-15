#!/usr/bin/env python3
"""
Main entry point for the 5G Core MCP Callback Server.

This runs the MCP server component that allows external clients
to query the stored event data via MCP tools.

The Flask server for receiving callbacks should be run separately:
  python callbackServer.py

Or use the startServer.py script to run both together.
"""
import logging
import sys

from config import config
from callbackServer import mcp

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Start the MCP server."""
    logger.info("=" * 60)
    logger.info("Starting 5G Core MCP Server")
    logger.info(f"Listening on {config.MCP_HOST}:{config.MCP_PORT}")
    logger.info(f"Transport: {config.MCP_TRANSPORT}")
    logger.info("=" * 60)
    
    try:
        mcp.run(
            transport=config.MCP_TRANSPORT,
            host=config.MCP_HOST,
            port=config.MCP_PORT
        )
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"MCP server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
