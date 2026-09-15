#!/usr/bin/env python3
"""Regression test for deleting seeded user reports."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_store import data_store


def main() -> int:
    data_store.clear()

    for supi in ["supi-user01", "supi-user02", "supi-user03"]:
        data_store.add_report({
            "supi": supi,
            "notif_id": f"notif-{supi}",
            "event": "USAGE_REPORT",
            "timestamp": "2026-07-08T00:00:00+00:00",
            "customized_data": {},
        })

    removed = data_store.delete_reports_for_supis(["supi-user01", "supi-user02"])
    if removed != 2:
        print(f"Expected 2 removed reports, got {removed}")
        return 1

    stats = data_store.get_statistics()
    if stats.get("total_reports") != 1:
        print(f"Expected 1 remaining report, got {stats.get('total_reports')}")
        return 1

    if "supi-user03" not in stats.get("ues", []):
        print("Expected remaining UE to be present")
        return 1

    print("Cleanup test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
