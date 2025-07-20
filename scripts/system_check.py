#!/usr/bin/env python3
"""
System Check Script for SoccerPredictor

This script performs a comprehensive health check of the entire system
to verify all fixes and improvements are working correctly.
"""

import sys
import os
from pathlib import Path
import subprocess
import sqlite3
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

def check_python_version():
    """Check Python version compatibility."""
    colored_print("🐍 Checking Python version...", "blue")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        colored_print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible", "green")
        return True
    else:
        colored_print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+", "red")
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    colored_print("📦 Checking dependencies...", "blue")
    
    required_packages = [
        'requests', 'pandas', 'numpy', 'flask', 'tensorflow', 
        'marshmallow', 'python-dotenv', 'flask-cors'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            colored_print(f"✅ {package}", "green")
        except ImportError:
            colored_print(f"❌ {package} - Not installed", "red")
            missing.append(package)
    
    return len(missing) == 0

def check_database():
    """Check database structure and integrity."""
    colored_print("🗄️  Checking database...", "blue")
    
    db_path = project_root / "data" / "soccer.db"
    if not db_path.exists():
        colored_print("❌ Database file not found", "red")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check required tables
        required_tables = ['Teams', 'TeamStats', 'Fixtures']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            if table in existing_tables:
                colored_print(f"✅ Table {table} exists", "green")
            else:
                colored_print(f"❌ Table {table} missing", "red")
                return False
        
        # Check data counts
        cursor.execute("SELECT COUNT(*) FROM Teams")
        team_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Fixtures")
        fixture_count = cursor.fetchone()[0]
        
        colored_print(f"📊 Teams: {team_count}, Fixtures: {fixture_count}", "blue")
        
        conn.close()
        return True
        
    except Exception as e:
        colored_print(f"❌ Database error: {e}", "red")
        return False

def check_api_configuration():
    """Check API configuration."""
    colored_print("🔑 Checking API configuration...", "blue")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_keys = {
        'FOOTBALL_DATA_API_KEY': os.getenv('FOOTBALL_DATA_API_KEY', ''),
        'RAPIDAPI_KEY': os.getenv('RAPIDAPI_KEY', ''),
        'FOOTYSTATS_API_KEY': os.getenv('FOOTYSTATS_API_KEY', ''),
    }
    
    configured_count = 0
    for key, value in api_keys.items():
        if value and len(value) > 10:
            colored_print(f"✅ {key} configured", "green")
            configured_count += 1
        else:
            colored_print(f"⚠️  {key} not configured", "yellow")
    
    if configured_count == 0:
        colored_print("⚠️  No API keys configured - will use demo data", "yellow")
    else:
        colored_print(f"✅ {configured_count}/3 API keys configured", "green")
    
    return True

def check_logging_system():
    """Test the logging system."""
    colored_print("📝 Testing logging system...", "blue")
    
    try:
        from soccerpredictor.util.logging_config import setup_logging, get_logger
        
        # Setup logging
        logger = setup_logging(log_level="INFO")
        
        # Test log messages
        logger.info("System check - logging test")
        logger.debug("Debug message test")
        logger.warning("Warning message test")
        
        # Check if log files are created
        logs_dir = project_root / "logs"
        if logs_dir.exists() and any(logs_dir.glob("*.log")):
            colored_print("✅ Logging system working", "green")
            return True
        else:
            colored_print("⚠️  Log files not found", "yellow")
            return True  # Still functional
            
    except Exception as e:
        colored_print(f"❌ Logging system error: {e}", "red")
        return False

def check_api_validation():
    """Test input validation system."""
    colored_print("🛡️  Testing input validation...", "blue")
    
    try:
        from soccerpredictor.util.validation import (
            SeasonValidator, PaginationValidator, TeamValidator,
            FixturesQuerySchema, validate_request_data
        )
        
        # Test season validation
        assert SeasonValidator.validate_season("2024") == True
        assert SeasonValidator.validate_season("invalid") == False
        
        # Test pagination validation
        assert PaginationValidator.validate_limit(50) == 50
        assert PaginationValidator.validate_limit(2000) == 1000  # Capped
        assert PaginationValidator.validate_offset(-1) == 0  # Non-negative
        
        # Test team validation
        assert TeamValidator.validate_team_name("Arsenal") == True
        assert TeamValidator.validate_team_name("Invalid/Team") == False
        
        # Test schema validation
        schema = FixturesQuerySchema()
        test_data = {'season': '2024', 'limit': 50}
        validated = validate_request_data(schema, test_data)
        assert validated['season'] == '2024'
        assert validated['limit'] == 50
        
        colored_print("✅ Input validation working", "green")
        return True
        
    except Exception as e:
        colored_print(f"❌ Validation error: {e}", "red")
        return False

def check_api_server():
    """Test API server functionality."""
    colored_print("🌐 Testing API server...", "blue")
    
    try:
        from soccerpredictor.api.api_server import create_app
        
        # Create test app
        app = create_app()
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                colored_print("✅ Health endpoint working", "green")
            else:
                colored_print(f"❌ Health endpoint failed: {response.status_code}", "red")
                return False
            
            # Test config endpoint
            response = client.get('/api/config')
            if response.status_code == 200:
                colored_print("✅ Config endpoint working", "green")
            else:
                colored_print(f"❌ Config endpoint failed: {response.status_code}", "red")
                return False
        
        return True
        
    except Exception as e:
        colored_print(f"❌ API server error: {e}", "red")
        return False

def check_data_fetcher():
    """Test data fetching capabilities."""
    colored_print("📡 Testing data fetcher...", "blue")
    
    try:
        from soccerpredictor.api.football_data_fetcher import FootballDataFetcher
        
        # Create fetcher with empty config (will use demo data)
        fetcher = FootballDataFetcher({})
        
        # Test API connection testing
        connections = fetcher.test_api_connections()
        if isinstance(connections, dict):
            colored_print("✅ API connection testing working", "green")
        else:
            colored_print("❌ API connection testing failed", "red")
            return False
        
        # Test demo data generation
        demo_data = fetcher._get_demo_data()
        if demo_data and len(demo_data) > 0:
            colored_print(f"✅ Demo data generation working ({len(demo_data)} matches)", "green")
        else:
            colored_print("❌ Demo data generation failed", "red")
            return False
        
        return True
        
    except Exception as e:
        colored_print(f"❌ Data fetcher error: {e}", "red")
        return False

def run_comprehensive_check():
    """Run all system checks."""
    colored_print("=" * 80, "yellow")
    colored_print("🏆 SOCCERPREDICTOR SYSTEM CHECK", "yellow")
    colored_print("=" * 80, "yellow")
    colored_print("Running comprehensive system validation...", "white")
    colored_print("-" * 80, "yellow")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("API Configuration", check_api_configuration),
        ("Logging System", check_logging_system),
        ("Input Validation", check_api_validation),
        ("API Server", check_api_server),
        ("Data Fetcher", check_data_fetcher),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        colored_print(f"\n🔍 {name}:", "white")
        try:
            if check_func():
                passed += 1
        except Exception as e:
            colored_print(f"❌ {name} failed with exception: {e}", "red")
    
    colored_print("\n" + "=" * 80, "yellow")
    colored_print("📊 SYSTEM CHECK RESULTS", "yellow")
    colored_print("=" * 80, "yellow")
    
    success_rate = (passed / total) * 100
    colored_print(f"Passed: {passed}/{total} ({success_rate:.1f}%)", "white")
    
    if success_rate >= 90:
        colored_print("🎉 SYSTEM IS PRODUCTION READY! 🎉", "green")
        status = "EXCELLENT"
    elif success_rate >= 75:
        colored_print("✅ System is mostly ready with minor issues", "green")
        status = "GOOD"
    elif success_rate >= 50:
        colored_print("⚠️  System has some issues that need attention", "yellow")
        status = "NEEDS_WORK"
    else:
        colored_print("❌ System has significant issues", "red")
        status = "CRITICAL"
    
    colored_print(f"\nSystem Status: {status}", "white")
    colored_print("=" * 80, "yellow")
    
    return success_rate >= 75

if __name__ == "__main__":
    try:
        success = run_comprehensive_check()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        colored_print("\n\n❌ System check interrupted", "red")
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n\n❌ System check failed: {e}", "red")
        sys.exit(1)