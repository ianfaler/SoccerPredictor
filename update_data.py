#!/usr/bin/env python3
"""
Command-line tool for updating football data and testing API endpoints.
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from soccerpredictor.api.api_manager import APIManager
from soccerpredictor.api.api_server import run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from environment variables."""
    config = {
        'FOOTBALL_DATA_API_KEY': os.getenv('FOOTBALL_DATA_API_KEY', ''),
        'RAPIDAPI_KEY': os.getenv('RAPIDAPI_KEY', ''),
    }
    
    # Check if .env file exists and load it
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        config.update({
            'FOOTBALL_DATA_API_KEY': os.getenv('FOOTBALL_DATA_API_KEY', config['FOOTBALL_DATA_API_KEY']),
            'RAPIDAPI_KEY': os.getenv('RAPIDAPI_KEY', config['RAPIDAPI_KEY']),
        })
    
    return config

def update_data_command(args):
    """Handle data update command."""
    config = load_config()
    api_manager = APIManager(config)
    
    seasons = args.seasons if args.seasons else None
    
    logger.info("Starting data update...")
    summary = api_manager.update_data(seasons)
    
    # Pretty print the summary
    print("\n" + "="*60)
    print("DATA UPDATE SUMMARY")
    print("="*60)
    print(f"Updated at: {summary['updated_at']}")
    print(f"Seasons: {', '.join(summary['seasons'])}")
    print(f"Total matches processed: {summary['total_matches']}")
    print(f"New matches added: {summary['new_matches']}")
    print(f"Existing matches updated: {summary['updated_matches']}")
    
    if summary['errors']:
        print(f"\nErrors ({len(summary['errors'])}):")
        for error in summary['errors']:
            print(f"  - {error}")
    else:
        print("\nNo errors occurred.")
    
    print("="*60)
    
    # Get database stats
    stats = api_manager.get_database_stats()
    if 'error' not in stats:
        print("\nDATABASE STATISTICS")
        print("-"*30)
        print(f"Total teams: {stats.get('total_teams', 0)}")
        print(f"Total fixtures: {stats.get('total_fixtures', 0)}")
        
        if stats.get('fixtures_by_season'):
            print("\nFixtures by season:")
            for season, count in stats['fixtures_by_season'].items():
                print(f"  {season}: {count} matches")
        
        if stats.get('last_updated'):
            print(f"\nLast updated: {stats['last_updated']}")

def test_endpoints_command(args):
    """Handle test endpoints command."""
    config = load_config()
    api_manager = APIManager(config)
    
    logger.info("Testing all endpoints...")
    results = api_manager.test_endpoints()
    
    print("\n" + "="*60)
    print("ENDPOINT TEST RESULTS")
    print("="*60)
    print(f"Test timestamp: {results['timestamp']}")
    print(f"Overall status: {'✅ PASS' if results['overall_status'] else '❌ FAIL'}")
    
    # Database test
    db_result = results['database']
    status_icon = "✅" if db_result['status'] == 'ok' else "❌"
    print(f"\nDatabase: {status_icon} {db_result['status'].upper()}")
    print(f"  Message: {db_result['message']}")
    if 'tables' in db_result:
        print(f"  Tables: {', '.join(db_result['tables'])}")
    
    # API connections test
    print(f"\nAPI Connections:")
    for api_name, status in results['api_connections'].items():
        status_icon = "✅" if status else "❌"
        print(f"  {api_name}: {status_icon} {'CONNECTED' if status else 'FAILED'}")
    
    # Data fetch test
    fetch_result = results['data_fetch']
    status_icon = "✅" if fetch_result['status'] == 'ok' else "❌"
    print(f"\nData Fetch: {status_icon} {fetch_result['status'].upper()}")
    print(f"  Message: {fetch_result['message']}")
    if 'sample_match' in fetch_result and fetch_result['sample_match']:
        sample = fetch_result['sample_match']
        print(f"  Sample: {sample['home_team']} vs {sample['away_team']} ({sample['date']})")
    
    print("="*60)

def server_command(args):
    """Handle server command."""
    logger.info(f"Starting API server on {args.host}:{args.port}")
    run_server(host=args.host, port=args.port, debug=args.debug)

def stats_command(args):
    """Handle stats command."""
    config = load_config()
    api_manager = APIManager(config)
    
    stats = api_manager.get_database_stats()
    
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    if 'error' in stats:
        print(f"Error: {stats['error']}")
        return
    
    print(f"Total teams: {stats.get('total_teams', 0)}")
    print(f"Total fixtures: {stats.get('total_fixtures', 0)}")
    
    if stats.get('fixtures_by_season'):
        print(f"\nFixtures by season:")
        for season, count in sorted(stats['fixtures_by_season'].items()):
            print(f"  {season}: {count} matches")
    
    if stats.get('last_updated'):
        print(f"\nLast updated: {stats['last_updated']}")
    
    print("="*60)

def setup_env_command(args):
    """Handle environment setup command."""
    env_file = Path('.env')
    
    print("Setting up environment configuration...")
    print("\nYou can obtain API keys from:")
    print("- Football Data API: https://www.football-data.org/client/register")
    print("- RapidAPI: https://rapidapi.com/")
    
    football_api_key = input("\nEnter Football Data API key (optional): ").strip()
    rapidapi_key = input("Enter RapidAPI key (optional): ").strip()
    
    env_content = f"""# Football API Configuration
# Get your free API key from https://www.football-data.org/client/register
FOOTBALL_DATA_API_KEY={football_api_key}

# RapidAPI Configuration
# Get your API key from https://rapidapi.com/
RAPIDAPI_KEY={rapidapi_key}
"""
    
    env_file.write_text(env_content)
    print(f"\nConfiguration saved to {env_file}")
    print("You can edit this file later to update your API keys.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Football Data Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_data.py update --seasons 2024 2023
  python update_data.py test
  python update_data.py server --port 5000
  python update_data.py stats
  python update_data.py setup-env
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Update data command
    update_parser = subparsers.add_parser('update', help='Update football data from APIs')
    update_parser.add_argument(
        '--seasons', nargs='*', 
        help='Seasons to update (e.g., 2024 2023). If not specified, updates current season.'
    )
    update_parser.set_defaults(func=update_data_command)
    
    # Test endpoints command
    test_parser = subparsers.add_parser('test', help='Test all API endpoints and database connectivity')
    test_parser.set_defaults(func=test_endpoints_command)
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start the REST API server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    server_parser.add_argument('--port', type=int, default=5000, help='Server port (default: 5000)')
    server_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    server_parser.set_defaults(func=server_command)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.set_defaults(func=stats_command)
    
    # Setup environment command
    setup_parser = subparsers.add_parser('setup-env', help='Setup environment configuration')
    setup_parser.set_defaults(func=setup_env_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()