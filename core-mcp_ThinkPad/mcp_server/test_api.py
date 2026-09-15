#!/usr/bin/env python3
"""
Test script for the 5G Core MCP Callback Server.

Tests both the Flask API and data store functionality.
"""
import requests
import json
import time
from datetime import datetime, timezone

# Configuration
FLASK_URL = "http://localhost:8081"
TEST_SUPI = "208950000000031"

# Sample event notification
SAMPLE_EVENT = {
    "notifId": "test-notif-001",
    "eventNotifs": [
        {
            "supi": TEST_SUPI,
            "event": "USAGE_REPORT",
            "timeStamp": str(int(datetime.now(timezone.utc).timestamp())),
            "pduSeId": 1,
            "customized_data": {
                "Usage Report": {
                    "Duration": 10,
                    "Trigger": "Periodic Reporting",
                    "UR-SEQN": 1,
                    "Volume": {
                        "Downlink": 2048,
                        "Total": 4096,
                        "Uplink": 2048
                    }
                }
            }
        }
    ]
}


def test_health_check():
    """Test the health check endpoint."""
    print("\n[TEST] Health Check")
    try:
        response = requests.get(f"{FLASK_URL}/callbacks/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        assert response.status_code == 200
        print("  ✓ PASSED")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_post_event():
    """Test posting an event notification."""
    print("\n[TEST] POST Event Notification")
    try:
        response = requests.post(
            f"{FLASK_URL}/callbacks/volume",
            json=SAMPLE_EVENT,
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        assert response.status_code == 200
        print("  ✓ PASSED")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_get_stats():
    """Test getting statistics."""
    print("\n[TEST] GET Statistics")
    try:
        response = requests.get(f"{FLASK_URL}/callbacks/stats")
        print(f"  Status: {response.status_code}")
        stats = response.json()
        print(f"  Total Reports: {stats.get('total_reports')}")
        print(f"  Total UEs: {stats.get('total_ues')}")
        assert response.status_code == 200
        print("  ✓ PASSED")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_get_all_data():
    """Test retrieving all data."""
    print("\n[TEST] GET All Data")
    try:
        response = requests.get(f"{FLASK_URL}/callbacks/data")
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Report Count: {data.get('count')}")
        assert response.status_code == 200
        print("  ✓ PASSED")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_invalid_event():
    """Test posting an invalid event."""
    print("\n[TEST] POST Invalid Event (should fail)")
    try:
        invalid_event = {
            "notifId": "test-notif-invalid",
            "eventNotifs": []  # Empty list - should fail
        }
        response = requests.post(
            f"{FLASK_URL}/callbacks/volume",
            json=invalid_event,
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        assert response.status_code == 400
        print("  ✓ PASSED (correctly rejected)")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_invalid_json():
    """Test posting invalid JSON."""
    print("\n[TEST] POST Invalid JSON (should fail)")
    try:
        response = requests.post(
            f"{FLASK_URL}/callbacks/volume",
            data="{ invalid json }",
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        assert response.status_code == 400
        print("  ✓ PASSED (correctly rejected)")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("5G Core MCP Callback Server - API Tests")
    print("=" * 60)
    print(f"Target: {FLASK_URL}")
    
    # Wait a moment for server startup
    time.sleep(1)
    
    tests = [
        test_health_check,
        test_post_event,
        test_get_stats,
        test_get_all_data,
        test_invalid_event,
        test_invalid_json,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"Test execution error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {total - passed} test(s) failed")
    
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
