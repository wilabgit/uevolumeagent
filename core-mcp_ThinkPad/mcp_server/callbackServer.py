#!/usr/bin/env python3
"""
5G Core SMF Event Exposure (Nsmf_EventExposure) Callback Server

This script provides:
1. HTTP server for receiving USAGE_REPORT events from the SMF (Flask)
2. MCP server for accessing stored event data via tools
3. Thread-safe in-memory data storage with configurable capacity
"""
import logging
import requests
import threading
from typing import Dict, Any
from flask import Flask, request, jsonify
from datetime import datetime, timezone

from config import config
from fastmcp import FastMCP
from mcp_tools import register_mcp_tools

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

from data_store import data_store

# Initialize Flask app
app = Flask(__name__)

# Initialize MCP server
mcp = FastMCP(config.MCP_SERVER_NAME)

# Register MCP tools
register_mcp_tools(mcp)

# Event to track if SMF has sent callbacks to this server
received_smf_callback = threading.Event()


def validate_event_notification(data: Dict[str, Any]) -> bool:
    """Validate incoming event notification structure.
    
    Args:
        data: The incoming JSON data
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required top-level fields
        if "notifId" not in data or "eventNotifs" not in data:
            logger.warning("Missing required fields: notifId or eventNotifs")
            return False
        
        # Check eventNotifs is a list with at least one entry
        if not isinstance(data["eventNotifs"], list) or len(data["eventNotifs"]) == 0:
            logger.warning("eventNotifs is empty or not a list")
            return False
        
        # Check first event has required fields
        event = data["eventNotifs"][0]
        required_fields = ["supi", "event", "timeStamp", "customized_data"]
        for field in required_fields:
            if field not in event:
                logger.warning(f"Missing required field in event: {field}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


@app.route("/callbacks/volume", methods=["POST"])
def volume_callback():
    """Handle POST notifications from the SMF.
    
    Expected format:
    {
        "notifId": "string",
        "eventNotifs": [
            {
                "supi": "string",
                "event": "string",
                "timeStamp": "string",
                "customized_data": {...}
            }
        ]
    }
    """
    try:
        data = request.get_json(force=True)
        
        # Validate the incoming data
        if not validate_event_notification(data):
            return jsonify({"error": "Invalid notification format"}), 400
        
        # Extract event data
        notif_id = data["notifId"]
        event_notif = data["eventNotifs"][0]
        supi = str(event_notif["supi"])
        event_type = event_notif["event"]
        ts = int(event_notif.get("timeStamp", 0))
        
        # Add notif_id to the event notification for storage
        event_notif["notif_id"] = notif_id
        
        try:
            usage_data = event_notif.get("customized_data", {}).get("Usage Report", {})
            nop_total=usage_data.get("NoP", {}).get("Total", 0)
            uplink = usage_data.get("Volume", {}).get("Uplink", 0)
            downlink = usage_data.get("Volume", {}).get("Downlink", 0)
            total = usage_data.get("Volume", {}).get("Total", 0)
        except (KeyError, TypeError) as e:
            logger.warning(f"Could not extract usage data: {e}")
            uplink = downlink = total = 0
        
        # Log the received event
        timestamp_str = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        logger.info(f"📩 Received {event_type} for UE {supi} (ID: {notif_id})")
        logger.debug(f"  ↳ Uplink:   {uplink} bytes")
        logger.debug(f"  ↳ Downlink: {downlink} bytes")
        logger.info(f"  ↳ Nop_total: {nop_total}   Total: {total} bytes")
        logger.debug(f"  ↳ Timestamp: {timestamp_str}")
        
        # Store the notification
        data_store.add_report(event_notif)
        
        # Signal that we received a callback from SMF
        received_smf_callback.set()
        
        totalue1=0
        totalue2=0
        if supi == "imsi-001010000000001":
            totalue1=total
            datavolume_ues={"ue1": totalue1, "ue2": totalue2}
        if supi == "imsi-001010000000002":
            totalue2=total
            datavolume_ues={"ue1": totalue1, "ue2": totalue2}
        try:
            # Optionally, send data to EIF or other systems here
            send_to_eif(datavolume_ues)
            pass
        except Exception as e:
            logger.error(f"Failed to send data to EIF: {e}")
            
        return jsonify({"status": "ok", "notifId": notif_id}), 200
    
    except ValueError as e:
        logger.error(f"Invalid JSON in request: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        logger.error(f"Failed to process incoming event: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def send_to_eif(datavolume):
    BASE_URL = "http://localhost:5101"  # Replace with actual EIF base URL
    ENDPOINT = "/eif/upfdatavolume"

    url = f"{BASE_URL}{ENDPOINT}"

    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }

    payload = {
        "datavolume": datavolume
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    return response
 
@app.route("/callbacks/data", methods=["GET"])
def get_all_data():
    """Get all stored event reports.
    
    Returns:
        JSON list of all stored reports
    """
    try:
        reports = data_store.get_all_reports()
        return jsonify({"count": len(reports), "reports": reports}), 200
    except Exception as e:
        logger.error(f"Error retrieving data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/callbacks/stats", methods=["GET"])
def get_statistics():
    """Get statistics about stored data.
    
    Returns:
        JSON with statistics
    """
    try:
        stats = data_store.get_statistics()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/callbacks/health", methods=["GET"])
def health_check():
    """Health check endpoint.
    
    Returns:
        JSON status
    """
    return jsonify({"status": "healthy"}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting 5G Core MCP Callback Server")
    logger.info(config)
    logger.info("=" * 60)
    
    # Run Flask app (MCP runs in a separate process via main.py)
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
        use_reloader=False  # Important: disable reloader when using threads
    )
