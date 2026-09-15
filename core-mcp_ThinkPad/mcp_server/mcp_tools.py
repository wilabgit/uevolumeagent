"""MCP tools for managing 5G core notifications and reports.

This module exposes FastMCP tools for viewing and summarizing UE usage
notifications that have been stored by the callback server.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from config import config
from data_store import data_store

logger = logging.getLogger(__name__)


def format_usage_report(event_notif: Dict[str, Any]) -> str:
    """Format a usage report into a readable text block.

    The callback server can store event notifications either in raw form
    or as database rows where the actual notification is nested under
    "event_data".

    Args:
        event_notif: Event notification data, either raw or database format.

    Returns:
        A formatted string summary for display.
    """
    try:
        if "event_data" in event_notif:
            # Database row format - event_data contains the original notification.
            notif_id = event_notif.get("notif_id", "UNKNOWN")
            original_data = event_notif["event_data"]
            usage_data = original_data.get("customized_data", {}).get("Usage Report", {})
            event_type = event_notif.get("event", "UNKNOWN")
            supi = event_notif.get("supi", "UNKNOWN")
            timestamp_str = event_notif.get("timestamp", "UNKNOWN")
        else:
            # Raw notification format from the 5G core.
            notif_id = event_notif.get("notif_id", "UNKNOWN")
            usage_data = event_notif.get("customized_data", {}).get("Usage Report", {})
            event_type = event_notif.get("event", "UNKNOWN")
            supi = event_notif.get("supi", "UNKNOWN")
            ts = int(event_notif.get("timeStamp", 0))
            timestamp_str = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

        volume = usage_data.get("Volume", {})
        uplink = volume.get("Uplink", 0)
        downlink = volume.get("Downlink", 0)
        total = volume.get("Total", 0)
        total_nop = usage_data.get("NoP", {}).get("Total", 0)
        duration = usage_data.get("Duration", 0)
        trigger = usage_data.get("Trigger", "UNKNOWN")

        return f"""
Event Type:    {event_type}
Notif ID:      {notif_id}
SUPI:          {supi}
Timestamp:     {timestamp_str}
Duration:      {duration}s
Trigger:       {trigger}
Total NoP:     {total_nop}
Volume (bytes):
  ├─ Uplink:   {uplink}
  ├─ Downlink: {downlink}
  └─ Total:    {total}
"""
    except Exception as e:
        logger.error(f"Error formatting report: {e}")
        return f"Error formatting report: {e}"


def register_mcp_tools(mcp) -> None:
    """Register MCP tools on the FastMCP server.

    Each tool is an async callable that returns a text summary suitable
    for presentation by the assistant.
    """

    @mcp.tool()
    async def get_ue_volume(ue_supi: str, max_reports: int = 100) -> str:
        """Return many recent usage reports for a given UE.

        Args:
            ue_supi: The SUPI of the UE to query.
            max_reports: Maximum number of reports to return.

        Limits output size to avoid returning too many reports to the LLM.
        """
        reports = data_store.get_ue_reports(ue_supi, limit=max_reports)

        if not reports:
            return f"No usage data found for UE {ue_supi}."

        truncated_info = ""
        if len(reports) >= max_reports:
            truncated_info = (
                f"Showing latest {max_reports} reports for UE {ue_supi}. "
                "Older reports are omitted to avoid overloading the LLM.\n\n"
            )

        formatted = [format_usage_report(report) for report in reports]
        return f"{truncated_info}" + "\n---\n".join(formatted)

    @mcp.tool()
    async def list_all_ues() -> str:
        """List all UEs that currently have stored reports.

        Args:
            None
        """
        ues = data_store.get_ue_list()

        if not ues:
            return "No UEs with stored reports."

        ue_list = "\n".join([f"  • {ue}" for ue in sorted(ues)])
        return f"Found {len(ues)} UEs with reports:\n{ue_list}"

#     @mcp.tool()
#     async def get_statistics() -> str:
#         """Return overall statistics about stored report storage, not the reports themselves.

#         Args:
#             None
#         """
#         stats = data_store.get_statistics()
#         storage_type = stats.get('storage_backend', 'unknown').upper()
#         total_reports = stats.get('total_reports', 0)
#         total_ues = stats.get('total_ues', 0)
#         max_reports = stats.get('max_reports')

#         if max_reports is not None and max_reports > 0:
#             usage_percent = f"{total_reports / max_reports * 100:.1f}%"
#             capacity_line = f"  Max Capacity:  {max_reports}\n  Usage:         {usage_percent}"
#         else:
#             capacity_line = "  Storage Type:  Persistent Database (Unlimited)"

#         return f"""
# Storage Statistics ({storage_type}):
#   Total Reports: {total_reports}
#   Total UEs:     {total_ues}
# {capacity_line}
# """
    # @mcp.tool()
    # async def get_latest_report(ue_supi: str) -> str:
    #     """Return the most recent stored report for a UE.

    #     Args:
    #         ue_supi: The SUPI of the UE to query.
    #     """
    #     reports = data_store.get_ue_reports(ue_supi)
    #     logging.info(f"Retrieving latest report for UE {ue_supi}: found {len(reports)} reports")

    #     if not reports:
    #         return f"No reports found for UE {ue_supi}."

    #     latest = reports[-1]  # Assumes reports are ordered chronologically.
    #     return format_usage_report(latest)

    # Disabled duplicate tool. Re-enable only if two-report output is required.
    # @mcp.tool()
    # async def get_latest_reports(ue_supi: str) -> str:
    #     """Return the two most recent reports for a UE."""
    #     reports = data_store.get_ue_reports(ue_supi)
    #
    #     if not reports:
    #         return f"No reports found for UE {ue_supi}."
    #
    #     latest = reports[-2:]
    #     return "\n---\n".join([format_usage_report(l) for l in latest])

    @mcp.tool()
    async def get_latest_reports_for_all_ues() -> str:
        """Return the most recent stored report for every UE.

        Args:
            None
        """
        ues = data_store.get_ue_list()

        if not ues:
            return "No UEs with stored reports."

        sections = []
        for ue_supi in sorted(ues):
            reports = data_store.get_ue_reports(ue_supi)
            if not reports:
                continue

            latest = reports[-1]
            sections.append(f"UE: {ue_supi}\n{format_usage_report(latest)}")

        if not sections:
            return "No reports found for any UEs."

        return "\n---\n".join(sections)

    @mcp.tool()
    async def get_ue_count() -> str:
        """Return the total number of UEs with stored reports.

        Args:
            None
        """
        count = len(data_store.get_ue_list())
        return f"Total UEs with reports: {count}"

    logger.info("MCP tools registered successfully")
