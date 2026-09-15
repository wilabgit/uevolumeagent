#!/usr/bin/env python3
"""
Combined entry point: runs both Flask and MCP servers together.

Startup behavior:
1. Starts Flask HTTP server to receive event callbacks from the SMF
2. Starts MCP server to provide tool-based access to stored data
3. Waits for SMF to send a callback (5 second timeout)
4. If no callback is received within timeout, registers callback URL with SMF

Environment variables:
  - FLASK_HOST (default: 0.0.0.0)
  - FLASK_PORT (default: 8085)
  - MCP_HOST (default: 0.0.0.0)
  - MCP_PORT (default: 8086)
  - LOG_LEVEL (default: INFO)
  - FLASK_DEBUG (default: False)
  - STORAGE_TYPE (default: postgresql)
  - DB_HOST (default: localhost)
  - DB_PORT (default: 5432)
  - DB_USER (default: postgres)
  - DB_PASSWORD (default: postgres)
  - DB_NAME (default: callback_server)
  - SMF_BASE_URL (default: "http://192.168.70.133:8080/nsmf_event-exposure/v1/subscriptions")
  - SMF_PAYLOAD (default: JSON string with subscription details)
  - HTTP_VERSION (default: 2)
"""
import logging
import threading
import sys
import signal
from config import config

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

from callbackServer import app, mcp, received_smf_callback
from request2SMF import make_http_request


shutdown_event = threading.Event()
SMF_REGISTRATION_TIMEOUT = 10  # seconds - wait this long for Flask to receive SMF callback

def run_flask():
    """Run Flask server in current thread."""
    while not shutdown_event.is_set():
        logger.info(f"Flask server starting on {config.FLASK_HOST}:{config.FLASK_PORT}")
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.FLASK_DEBUG,
            use_reloader=False
        )
    logger.info("Flask server shutting down...")

def run_mcp():
    """Run MCP server in current thread."""
    while not shutdown_event.is_set():
        logger.info(f"MCP server starting on {config.MCP_HOST}:{config.MCP_PORT}")
        mcp.run(
            transport=config.MCP_TRANSPORT,
            host=config.MCP_HOST,
            port=config.MCP_PORT
        )
    logger.info("MCP server shutting down...")


def main():
    """Start both servers in separate threads."""
    logger.info("=" * 60)
    logger.info("Starting 5G Core MCP Callback Server (Combined)")
    logger.info(config)
    logger.info("=" * 60)
    
    # Create and start server threads
    flask_thread = threading.Thread(target=run_flask, name="Flask-Server", daemon=False)
    mcp_thread = threading.Thread(target=run_mcp, name="MCP-Server", daemon=False)
    
    try:
        flask_thread.start()
        mcp_thread.start()
        
        # Wait for Flask to receive a callback from SMF within the timeout period
        logger.info(f"Waiting {SMF_REGISTRATION_TIMEOUT}s for SMF callback...")
        if not received_smf_callback.wait(timeout=SMF_REGISTRATION_TIMEOUT):
            # No callback received within timeout - notify SMF of callback URL
            logger.warning(f"No SMF callback received within {SMF_REGISTRATION_TIMEOUT}s")
            logger.info("Requesting SMF to register callback URL...")
            tmp=make_http_request(
                url=config.SMF_BASE_URL,
                httpversion=config.HTTP_VERSION,
                method="POST",
                data=config.SMF_PAYLOAD
            )
            logger.info(f"SMF registration response: {tmp}")
        else:
            logger.info("✓ SMF callback received - no registration needed")
        
    except KeyboardInterrupt:
        shutdown_event.set()
        # Wait for threads to complete
        flask_thread.join()
        mcp_thread.join()
        logger.info("Shutting down servers...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running servers: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
