#!/usr/bin/env python3
"""Populate the configured store with 50 reports for 50 distinct users."""
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_store import data_store


def create_report(user_index: int) -> Dict[str, Any]:
    """Create a synthetic usage report for a unique user."""
    supi = f"supi-user{user_index:02d}"
    return {
        "supi": supi,
        "notif_id": f"notif-{supi}-{user_index}",
        "event": "USAGE_REPORT",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customized_data": {
            "Usage Report": {
                    "Duration": 10,
                    "NoP": {
                        "Downlink": user_index * 10,
                        "Total": user_index * 20,
                        "Uplink": user_index * 10
                    },
                    "SEID": 1,
                    "Trigger": "Periodic Reporting",
                    "UR-SEQN": 127,
                    "Volume": {
                        "Downlink": user_index * 100,
                        "Total": user_index * 200,
                        "Uplink": user_index * 100
                    }
                },
                "event": "",
                "timeStamp": ""
            },
    }



def main() -> int:
    """Insert 50 reports for 50 distinct users."""
    count = 25
    print(f"Adding {count} reports to the {type(data_store).__name__} backend...")

    for index in range(25, 25+count+1):
        report = create_report(index)
        data_store.add_report(report)
        print(f"  Added report {index}/{count} for {report['supi']}")

    stats = data_store.get_statistics()
    print("\nPopulation complete.")
    print(f"Backend: {stats.get('storage_backend', type(data_store).__name__)}")
    print(f"Total reports now stored: {stats.get('total_reports')}")
    print(f"Unique users now stored: {stats.get('total_ues')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
