"""
API Manager for handling data updates and database synchronization.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from .football_data_fetcher import FootballDataFetcher, MatchData
from ..util.constants import DATA_DIR, DB_FILE
from ..util.logging_config import get_logger

logger = get_logger('api_manager')

class APIManager:
    """
    Manages API data fetching, database updates, and data synchronization.
    """
    
    def __init__(self, config: Dict[str, str] = None):
        """
        Initialize the API manager.
        
        :param config: Configuration dictionary containing API keys
        """
        self.config = config or {}
        self.fetcher = FootballDataFetcher(config)
        self.db_path = Path(DATA_DIR) / DB_FILE
        
        # Ensure data directory exists
        Path(DATA_DIR).mkdir(exist_ok=True)
        
        # Initialize database if it doesn't exist
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create Teams table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create TeamStats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TeamStats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rating REAL DEFAULT 75.0,
                    errors INTEGER DEFAULT 0,
                    red_cards INTEGER DEFAULT 0,
                    shots INTEGER DEFAULT 0,
                    matches_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    goals_for INTEGER DEFAULT 0,
                    goals_against INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create Fixtures table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Fixtures (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL,
                    season INTEGER NOT NULL,
                    league TEXT NOT NULL,
                    homeTeamID INTEGER NOT NULL,
                    awayTeamID INTEGER NOT NULL,
                    home_goals INTEGER,
                    away_goals INTEGER,
                    oddsDC_1X REAL,
                    oddsDC_X2 REAL,
                    homeStatsID INTEGER,
                    awayStatsID INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (homeTeamID) REFERENCES Teams (id),
                    FOREIGN KEY (awayTeamID) REFERENCES Teams (id),
                    FOREIGN KEY (homeStatsID) REFERENCES TeamStats (id),
                    FOREIGN KEY (awayStatsID) REFERENCES TeamStats (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_date ON Fixtures (date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_season ON Fixtures (season)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_teams ON Fixtures (homeTeamID, awayTeamID)")
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def update_data(self, seasons: List[str] = None, force_update: bool = False) -> Dict[str, Any]:
        """
        Update database with latest football data.
        
        :param seasons: List of seasons to update (default: current season)
        :param force_update: Force update even if data exists
        :return: Summary of update operation
        """
        if seasons is None:
            current_year = datetime.now().year
            seasons = [str(current_year)]
        
        summary = {
            'updated_at': datetime.now().isoformat(),
            'seasons': seasons,
            'total_matches': 0,
            'new_matches': 0,
            'updated_matches': 0,
            'skipped_matches': 0,
            'force_update': force_update,
            'errors': []
        }
        
        try:
            # For bulk updates, use efficient bulk fetching
            if len(seasons) > 1:
                logger.info(f"Performing bulk update for {len(seasons)} seasons")
                start_year = min(int(s) for s in seasons)
                end_year = max(int(s) for s in seasons)
                
                bulk_data = self.fetcher.fetch_historical_data_bulk(start_year, end_year)
                
                for season in seasons:
                    matches = bulk_data.get(season, [])
                    season_summary = self._update_season_data_from_matches(season, matches, force_update)
                    summary['total_matches'] += season_summary['total_matches']
                    summary['new_matches'] += season_summary['new_matches']
                    summary['updated_matches'] += season_summary['updated_matches']
                    summary['skipped_matches'] += season_summary.get('skipped_matches', 0)
                    summary['errors'].extend(season_summary['errors'])
            else:
                # Single season update
                for season in seasons:
                    season_summary = self._update_season_data(season, force_update)
                    summary['total_matches'] += season_summary['total_matches']
                    summary['new_matches'] += season_summary['new_matches']
                    summary['updated_matches'] += season_summary['updated_matches']
                    summary['skipped_matches'] += season_summary.get('skipped_matches', 0)
                    summary['errors'].extend(season_summary['errors'])
            
            logger.info(f"Data update completed: {summary}")
            
        except Exception as e:
            error_msg = f"Failed to update data: {e}"
            logger.error(error_msg, exc_info=True)
            summary['errors'].append(error_msg)
        
        return summary
    
    def _update_season_data(self, season: str, force_update: bool = False) -> Dict[str, Any]:
        """Update data for a specific season."""
        summary = {
            'season': season,
            'total_matches': 0,
            'new_matches': 0,
            'updated_matches': 0,
            'skipped_matches': 0,
            'errors': []
        }
        
        try:
            # Fetch matches for the season
            matches = self.fetcher.fetch_premier_league_fixtures(season)
            return self._update_season_data_from_matches(season, matches, force_update)
            
        except Exception as e:
            error_msg = f"Failed to update season {season}: {e}"
            logger.error(error_msg, exc_info=True)
            summary['errors'].append(error_msg)
            return summary
    
    def _update_season_data_from_matches(self, season: str, matches: List[MatchData], force_update: bool = False) -> Dict[str, Any]:
        """Update season data from a list of matches."""
        summary = {
            'season': season,
            'total_matches': len(matches),
            'new_matches': 0,
            'updated_matches': 0,
            'skipped_matches': 0,
            'errors': []
        }
        
        if not matches:
            logger.warning(f"No matches found for season {season}")
            return summary
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            for match in matches:
                try:
                    # Check if fixture exists and skip if not forcing update
                    fixture_exists = self._fixture_exists(conn, match.id)
                    if fixture_exists and not force_update:
                        summary['skipped_matches'] += 1
                        continue
                    
                    # Ensure teams exist
                    home_team_id = self._ensure_team_exists(conn, match.home_team)
                    away_team_id = self._ensure_team_exists(conn, match.away_team)
                    
                    # Create or update team stats
                    home_stats_id = self._update_team_stats(conn, home_team_id, match.home_team, season)
                    away_stats_id = self._update_team_stats(conn, away_team_id, match.away_team, season)
                    
                    # Insert or update fixture
                    if fixture_exists:
                        self._update_fixture(conn, match, home_team_id, away_team_id, home_stats_id, away_stats_id)
                        summary['updated_matches'] += 1
                    else:
                        self._insert_fixture(conn, match, home_team_id, away_team_id, home_stats_id, away_stats_id)
                        summary['new_matches'] += 1
                
                except Exception as e:
                    error_msg = f"Failed to process match {match.id}: {e}"
                    logger.warning(error_msg)
                    summary['errors'].append(error_msg)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            error_msg = f"Failed to update season {season}: {e}"
            logger.error(error_msg, exc_info=True)
            summary['errors'].append(error_msg)
        
        return summary
    
    def _ensure_team_exists(self, conn: sqlite3.Connection, team_name: str) -> int:
        """Ensure team exists in database and return its ID."""
        cursor = conn.cursor()
        
        # Check if team exists
        cursor.execute("SELECT id FROM Teams WHERE name = ?", (team_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Insert new team
        cursor.execute(
            "INSERT INTO Teams (name, full_name) VALUES (?, ?)",
            (team_name, team_name)
        )
        return cursor.lastrowid
    
    def _update_team_stats(self, conn: sqlite3.Connection, team_id: int, team_name: str, season: str) -> int:
        """Update or create team statistics."""
        cursor = conn.cursor()
        
        try:
            # Fetch latest stats from API
            stats = self.fetcher.fetch_team_statistics(team_name, season)
            
            # Insert new stats record
            cursor.execute("""
                INSERT INTO TeamStats (
                    rating, errors, red_cards, shots, matches_played,
                    wins, draws, losses, goals_for, goals_against
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.get('rating', 75.0),
                stats.get('errors', 0),
                stats.get('red_cards', 0),
                stats.get('shots_total', 0),
                stats.get('matches_played', 0),
                stats.get('wins', 0),
                stats.get('draws', 0),
                stats.get('losses', 0),
                stats.get('goals_for', 0),
                stats.get('goals_against', 0)
            ))
            
            return cursor.lastrowid
            
        except Exception as e:
            logger.warning(f"Failed to fetch stats for {team_name}, using defaults: {e}")
            
            # Insert default stats
            cursor.execute("""
                INSERT INTO TeamStats (rating, errors, red_cards, shots)
                VALUES (75.0, 0, 0, 0)
            """)
            return cursor.lastrowid
    
    def _fixture_exists(self, conn: sqlite3.Connection, fixture_id: int) -> bool:
        """Check if fixture already exists in database."""
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Fixtures WHERE id = ?", (fixture_id,))
        return cursor.fetchone() is not None
    
    def _insert_fixture(self, conn: sqlite3.Connection, match: MatchData, 
                       home_team_id: int, away_team_id: int, 
                       home_stats_id: int, away_stats_id: int):
        """Insert new fixture into database."""
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Fixtures (
                id, date, season, league, homeTeamID, awayTeamID,
                home_goals, away_goals, oddsDC_1X, oddsDC_X2,
                homeStatsID, awayStatsID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match.id, match.date, int(match.season), match.league,
            home_team_id, away_team_id, match.home_goals, match.away_goals,
            match.home_odds_wd, match.away_odds_wd, home_stats_id, away_stats_id
        ))
    
    def _update_fixture(self, conn: sqlite3.Connection, match: MatchData,
                       home_team_id: int, away_team_id: int,
                       home_stats_id: int, away_stats_id: int):
        """Update existing fixture in database."""
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Fixtures SET
                date = ?, season = ?, league = ?, homeTeamID = ?, awayTeamID = ?,
                home_goals = ?, away_goals = ?, oddsDC_1X = ?, oddsDC_X2 = ?,
                homeStatsID = ?, awayStatsID = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            match.date, int(match.season), match.league, home_team_id, away_team_id,
            match.home_goals, match.away_goals, match.home_odds_wd, match.away_odds_wd,
            home_stats_id, away_stats_id, match.id
        ))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the current database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Count teams
            cursor.execute("SELECT COUNT(*) FROM Teams")
            stats['total_teams'] = cursor.fetchone()[0]
            
            # Count fixtures
            cursor.execute("SELECT COUNT(*) FROM Fixtures")
            stats['total_fixtures'] = cursor.fetchone()[0]
            
            # Count fixtures by season
            cursor.execute("SELECT season, COUNT(*) FROM Fixtures GROUP BY season ORDER BY season")
            stats['fixtures_by_season'] = dict(cursor.fetchall())
            
            # Latest update
            cursor.execute("SELECT MAX(updated_at) FROM Fixtures")
            stats['last_updated'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {'error': str(e)}
    
    def test_endpoints(self) -> Dict[str, Any]:
        """Test all API endpoints and database connectivity."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'database': self._test_database(),
            'api_connections': self.fetcher.test_api_connections(),
            'data_fetch': self._test_data_fetch()
        }
        
        # Overall status
        results['overall_status'] = all([
            results['database']['status'] == 'ok',
            any(results['api_connections'].values()),  # At least one API working
            results['data_fetch']['status'] == 'ok'
        ])
        
        return results
    
    def _test_database(self) -> Dict[str, Any]:
        """Test database connectivity and structure."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if all required tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('Teams', 'TeamStats', 'Fixtures')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            expected_tables = {'Teams', 'TeamStats', 'Fixtures'}
            missing_tables = expected_tables - set(tables)
            
            if missing_tables:
                return {
                    'status': 'error',
                    'message': f'Missing tables: {missing_tables}'
                }
            
            return {
                'status': 'ok',
                'message': 'Database structure is valid',
                'tables': tables
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Database error: {e}'
            }
    
    def _test_data_fetch(self) -> Dict[str, Any]:
        """Test data fetching capabilities."""
        try:
            # Try to fetch a small amount of data
            matches = self.fetcher.fetch_premier_league_fixtures("2024")
            
            if not matches:
                return {
                    'status': 'warning',
                    'message': 'No matches fetched, but no errors occurred'
                }
            
            return {
                'status': 'ok',
                'message': f'Successfully fetched {len(matches)} matches',
                'sample_match': {
                    'home_team': matches[0].home_team,
                    'away_team': matches[0].away_team,
                    'date': matches[0].date
                } if matches else None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Data fetch error: {e}'
            }