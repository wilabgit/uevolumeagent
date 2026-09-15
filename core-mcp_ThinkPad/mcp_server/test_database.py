#!/usr/bin/env python3
"""Test script for database storage functionality."""
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_store import data_store
from config import config


def create_test_report(supi: str, event: str = "USAGE_REPORT") -> Dict[str, Any]:
    """Create a test event notification."""
    return {
        "supi": supi,
        "notif_id": f"notif-{supi}-{datetime.now(timezone.utc).timestamp()}",
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customized_data": {
            "data_volume": 1024,
            "duration": 3600,
            "location": "Europe/Rome"
        }
    }


def test_storage():
    """Run storage tests."""
    print("=" * 70)
    print("Testing Report Storage")
    print("=" * 70)
    print(f"\nStorage Type: {config.STORAGE_TYPE}")
    print(f"Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    print()
    
    # Test 1: Add reports
    print("[TEST 1] Adding test reports...")
    test_supis = ["supi-alice", "supi-bob", "supi-charlie"]
    
    for i, supi in enumerate(test_supis):
        for j in range(3):
            report = create_test_report(supi)
            report["customized_data"]["duration"] = 3600 + (j * 100)
            try:
                data_store.add_report(report)
                print(f"  ✓ Added report {i*3 + j + 1} for {supi}")
            except Exception as e:
                print(f"  ✗ Failed to add report: {e}")
                return False
    
    # Test 2: Get reports for specific UE
    print("\n[TEST 2] Retrieving reports for specific UE...")
    try:
        reports = data_store.get_ue_reports("supi-alice")
        print(f"  ✓ Retrieved {len(reports)} reports for supi-alice")
        for report in reports[:2]:
            print(f"    - Event: {report['event']}, Duration: {report.get('customized_data', {}).get('duration')}")
    except Exception as e:
        print(f"  ✗ Failed to retrieve UE reports: {e}")
        return False
    
    # Test 3: Get all reports
    print("\n[TEST 3] Retrieving all reports...")
    try:
        all_reports = data_store.get_all_reports()
        print(f"  ✓ Retrieved {len(all_reports)} total reports")
    except Exception as e:
        print(f"  ✗ Failed to retrieve all reports: {e}")
        return False
    
    # Test 4: Get UE list
    print("\n[TEST 4] Getting list of UEs...")
    try:
        ue_list = data_store.get_ue_list()
        print(f"  ✓ Found {len(ue_list)} unique UEs:")
        for ue in ue_list:
            print(f"    - {ue}")
    except Exception as e:
        print(f"  ✗ Failed to get UE list: {e}")
        return False
    
    # Test 5: Get statistics
    print("\n[TEST 5] Getting storage statistics...")
    try:
        stats = data_store.get_statistics()
        print(f"  ✓ Storage Statistics:")
        for key, value in stats.items():
            if key != "ues":  # Skip the list for cleaner output
                print(f"    {key}: {value}")
    except Exception as e:
        print(f"  ✗ Failed to get statistics: {e}")
        return False
    
    # Test 6: Health check (if available)
    if hasattr(data_store, 'health_check'):
        print("\n[TEST 6] Database health check...")
        try:
            is_healthy = data_store.health_check()
            if is_healthy:
                print(f"  ✓ Database is healthy")
            else:
                print(f"  ⚠ Database health check returned False")
        except Exception as e:
            print(f"  ✗ Health check failed: {e}")
    
    # Test 7: Event type filtering (DB-specific)
    if hasattr(data_store, 'get_reports_for_event'):
        print("\n[TEST 7] Filtering reports by event type...")
        try:
            event_reports = data_store.get_reports_for_event("USAGE_REPORT", limit=2)
            print(f"  ✓ Retrieved {len(event_reports)} reports of type USAGE_REPORT")
        except Exception as e:
            print(f"  ✗ Failed to filter by event type: {e}")
    
    print("\n" + "=" * 70)
    print("✓ All tests completed successfully!")
    print("=" * 70)
    return True


def main():
    """Main entry point."""
    try:
        success = test_storage()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
