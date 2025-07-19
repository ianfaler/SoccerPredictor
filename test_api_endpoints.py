#!/usr/bin/env python3
"""
Comprehensive test script for all SoccerPredictor API endpoints.
"""

import requests
import json
import time
import sys
from typing import Dict, Any
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000/api"
TIMEOUT = 30

def colored_print(message: str, color: str = "white") -> None:
    """Print colored messages."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{message}{colors['reset']}")

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, 
                 expected_status: int = 200) -> bool:
    """Test a single API endpoint."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            colored_print(f"❌ Unsupported method: {method}", "red")
            return False
        
        if response.status_code == expected_status:
            colored_print(f"✅ {method} {endpoint} - {response.status_code}", "green")
            
            # Try to parse JSON and show sample data
            try:
                json_data = response.json()
                if isinstance(json_data, dict):
                    # Show first few keys for overview
                    keys = list(json_data.keys())[:3]
                    colored_print(f"   Sample keys: {keys}", "blue")
                    
                    # Show specific data based on endpoint
                    if "fixtures" in json_data and json_data["fixtures"]:
                        first_fixture = json_data["fixtures"][0]
                        colored_print(f"   Sample fixture: {first_fixture.get('home_team', 'N/A')} vs {first_fixture.get('away_team', 'N/A')}", "blue")
                    elif "teams" in json_data and json_data["teams"]:
                        team_count = len(json_data["teams"])
                        colored_print(f"   Teams count: {team_count}", "blue")
                    elif "status" in json_data:
                        colored_print(f"   Status: {json_data['status']}", "blue")
                        
            except json.JSONDecodeError:
                colored_print(f"   Response: {response.text[:100]}...", "blue")
            
            return True
        else:
            colored_print(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}", "red")
            colored_print(f"   Response: {response.text[:200]}", "red")
            return False
            
    except requests.exceptions.RequestException as e:
        colored_print(f"❌ {method} {endpoint} - Connection error: {e}", "red")
        return False

def main():
    """Run comprehensive API endpoint tests."""
    colored_print("=" * 60, "yellow")
    colored_print("🏆 SOCCERPREDICTOR API ENDPOINT TESTS", "yellow")
    colored_print("=" * 60, "yellow")
    colored_print(f"Testing API at: {API_BASE_URL}", "white")
    colored_print(f"Test started: {datetime.now().isoformat()}", "white")
    print()
    
    # Track test results
    tests = []
    
    # Test 1: Health Check
    colored_print("1. Health Check", "yellow")
    tests.append(test_endpoint("GET", "/health"))
    print()
    
    # Test 2: System Status
    colored_print("2. System Status", "yellow")
    tests.append(test_endpoint("GET", "/status"))
    print()
    
    # Test 3: Data Statistics
    colored_print("3. Data Statistics", "yellow")
    tests.append(test_endpoint("GET", "/data/stats"))
    print()
    
    # Test 4: Teams List
    colored_print("4. Teams List", "yellow")
    tests.append(test_endpoint("GET", "/teams"))
    print()
    
    # Test 5: Fixtures (with pagination)
    colored_print("5. Fixtures (Limited)", "yellow")
    tests.append(test_endpoint("GET", "/fixtures?limit=5"))
    print()
    
    # Test 6: All Fixtures
    colored_print("6. All Fixtures", "yellow")
    tests.append(test_endpoint("GET", "/fixtures"))
    print()
    
    # Test 7: Fixtures by Season
    colored_print("7. Fixtures by Season (2024)", "yellow")
    tests.append(test_endpoint("GET", "/fixtures?season=2024"))
    print()
    
    # Test 8: Data Update (POST)
    colored_print("8. Data Update (POST)", "yellow")
    update_data = {"seasons": ["2024"]}
    tests.append(test_endpoint("POST", "/data/update", update_data))
    print()
    
    # Test 9: Invalid Endpoint
    colored_print("9. Invalid Endpoint (Expected 404)", "yellow")
    tests.append(test_endpoint("GET", "/nonexistent", expected_status=404))
    print()
    
    # Summary
    colored_print("=" * 60, "yellow")
    colored_print("📊 TEST SUMMARY", "yellow")
    colored_print("=" * 60, "yellow")
    
    passed = sum(tests)
    total = len(tests)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    colored_print(f"Total tests: {total}", "white")
    colored_print(f"Passed: {passed}", "green")
    colored_print(f"Failed: {total - passed}", "red")
    colored_print(f"Success rate: {success_rate:.1f}%", "yellow")
    
    if success_rate >= 80:
        colored_print("\n🎉 API ENDPOINTS ARE WORKING CORRECTLY! 🎉", "green")
    else:
        colored_print("\n⚠️  SOME ENDPOINTS NEED ATTENTION! ⚠️", "red")
    
    colored_print(f"\nTest completed: {datetime.now().isoformat()}", "white")
    colored_print("=" * 60, "yellow")
    
    return success_rate >= 80

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        colored_print("\n\n❌ Tests interrupted by user", "red")
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n\n❌ Test suite failed: {e}", "red")
        sys.exit(1)