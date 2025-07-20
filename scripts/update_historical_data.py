#!/usr/bin/env python3
"""
Historical Data Update Script for SoccerPredictor

This script updates the database with historical Premier League data
from 2020-2025 using multiple API sources.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from dotenv import load_dotenv

from soccerpredictor.api.api_manager import APIManager
from soccerpredictor.util.logging_config import setup_logging, get_logger

def main():
    """Main function for historical data update."""
    parser = argparse.ArgumentParser(
        description="Update SoccerPredictor with historical Premier League data"
    )
    parser.add_argument(
        '--start-year', 
        type=int, 
        default=2020,
        help='Starting year for data update (default: 2020)'
    )
    parser.add_argument(
        '--end-year', 
        type=int, 
        default=2025,
        help='Ending year for data update (default: 2025)'
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force update existing data'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(log_level=args.log_level)
    
    # Load environment variables
    load_dotenv()
    
    logger.info("="*80)
    logger.info("🏆 SOCCERPREDICTOR HISTORICAL DATA UPDATE")
    logger.info("="*80)
    logger.info(f"📅 Year range: {args.start_year} - {args.end_year}")
    logger.info(f"🔄 Force update: {args.force}")
    logger.info(f"🔍 Dry run: {args.dry_run}")
    logger.info(f"📊 Log level: {args.log_level}")
    logger.info("-"*80)
    
    # Validate year range
    current_year = datetime.now().year
    if args.start_year > current_year or args.end_year > current_year + 1:
        logger.error(f"Invalid year range. Maximum year is {current_year + 1}")
        return 1
    
    if args.start_year > args.end_year:
        logger.error("Start year cannot be greater than end year")
        return 1
    
    # Check API configuration
    config = {
        'FOOTBALL_DATA_API_KEY': os.getenv('FOOTBALL_DATA_API_KEY', ''),
        'RAPIDAPI_KEY': os.getenv('RAPIDAPI_KEY', ''),
        'FOOTYSTATS_API_KEY': os.getenv('FOOTYSTATS_API_KEY', ''),
    }
    
    # Check if at least one API key is configured
    configured_apis = [k for k, v in config.items() if v]
    if not configured_apis:
        logger.warning("⚠️  No API keys configured. Will use demo data only.")
        logger.info("To configure API keys:")
        logger.info("1. Copy .env.example to .env")
        logger.info("2. Add your API keys to the .env file")
        logger.info("3. Re-run this script")
    else:
        logger.info(f"✅ Configured APIs: {configured_apis}")
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        seasons = [str(year) for year in range(args.start_year, args.end_year + 1)]
        logger.info(f"Would update data for seasons: {seasons}")
        return 0
    
    try:
        # Initialize API manager
        api_manager = APIManager(config)
        
        # Generate list of seasons
        seasons = [str(year) for year in range(args.start_year, args.end_year + 1)]
        
        logger.info(f"🚀 Starting update for {len(seasons)} seasons...")
        
        # Update data
        summary = api_manager.update_data(seasons, force_update=args.force)
        
        # Display results
        logger.info("="*80)
        logger.info("📊 UPDATE SUMMARY")
        logger.info("="*80)
        logger.info(f"✅ Total matches processed: {summary['total_matches']}")
        logger.info(f"🆕 New matches added: {summary['new_matches']}")
        logger.info(f"🔄 Existing matches updated: {summary['updated_matches']}")
        logger.info(f"⏭️  Matches skipped: {summary['skipped_matches']}")
        
        if summary['errors']:
            logger.warning(f"⚠️  Errors encountered: {len(summary['errors'])}")
            for error in summary['errors'][:5]:  # Show first 5 errors
                logger.warning(f"   - {error}")
            if len(summary['errors']) > 5:
                logger.warning(f"   ... and {len(summary['errors']) - 5} more errors")
        else:
            logger.info("✅ No errors encountered")
        
        # Get database statistics
        try:
            db_stats = api_manager.get_database_stats()
            logger.info("-"*80)
            logger.info("📈 DATABASE STATISTICS")
            logger.info("-"*80)
            logger.info(f"Teams: {db_stats.get('total_teams', 'N/A')}")
            logger.info(f"Fixtures: {db_stats.get('total_fixtures', 'N/A')}")
            
            if 'fixtures_by_season' in db_stats:
                logger.info("Fixtures by season:")
                for season, count in sorted(db_stats['fixtures_by_season'].items()):
                    logger.info(f"  {season}: {count} matches")
                    
        except Exception as e:
            logger.warning(f"Could not retrieve database statistics: {e}")
        
        logger.info("="*80)
        logger.info("🎉 Historical data update completed successfully!")
        logger.info("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Historical data update failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)