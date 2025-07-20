"""
Football Data Fetcher for retrieving data from various football APIs.
"""

import os
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
from dataclasses import dataclass

from ..util.logging_config import get_logger

logger = get_logger('football_data_fetcher')

@dataclass
class MatchData:
    """Data structure for a football match."""
    id: int
    date: str
    season: str
    league: str
    home_team: str
    away_team: str
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    home_odds_wd: Optional[float] = None
    away_odds_wd: Optional[float] = None
    home_rating: Optional[float] = None
    away_rating: Optional[float] = None
    home_errors: Optional[int] = None
    away_errors: Optional[int] = None
    home_red_cards: Optional[int] = None
    away_red_cards: Optional[int] = None
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None

class FootballDataFetcher:
    """
    Fetches football data from multiple API sources.
    
    Supports:
    - football-data.org (free tier)
    - RapidAPI football endpoints
    - Custom API endpoints
    """
    
    def __init__(self, config: Dict[str, str] = None):
        """
        Initialize the fetcher with API configurations.
        
        :param config: Dictionary containing API keys and configurations
        """
        self.config = config or {}
        self.session = requests.Session()
        
        # Set up default headers
        self.session.headers.update({
            'User-Agent': 'SoccerPredictor/1.0',
            'Accept': 'application/json'
        })
        
        # API endpoints and configurations
        self.apis = {
            'football_data_org': {
                'base_url': 'https://api.football-data.org/v4',
                'headers': {'X-Auth-Token': self.config.get('FOOTBALL_DATA_API_KEY', '')},
                'free_competitions': [2021],  # Premier League
                'rate_limit': 10  # requests per minute for free tier
            },
            'rapidapi': {
                'base_url': 'https://api-football-v1.p.rapidapi.com/v3',
                'headers': {
                    'X-RapidAPI-Key': self.config.get('RAPIDAPI_KEY', ''),
                    'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
                },
                'rate_limit': 100  # depends on subscription
            },
            'footystats': {
                'base_url': 'https://api.footystats.org/v2',
                'headers': {
                    'X-API-KEY': self.config.get('FOOTYSTATS_API_KEY', ''),
                    'Accept': 'application/json'
                },
                'rate_limit': 500  # requests per day for free tier
            }
        }
        
        # Rate limiting
        self._last_request_times = {}
        self._request_counts = {}
    
    def fetch_premier_league_fixtures(self, season: str = "2024") -> List[MatchData]:
        """
        Fetch Premier League fixtures for a given season.
        
        :param season: Season year (e.g., "2024" for 2024-25 season)
        :return: List of MatchData objects
        """
        logger.info(f"Fetching Premier League fixtures for season {season}")
        
        # Try multiple APIs in order of preference
        apis_to_try = [
            ('footystats', self._fetch_from_footystats),
            ('football_data_org', self._fetch_from_football_data_org),
            ('rapidapi', self._fetch_from_rapidapi)
        ]
        
        for api_name, fetch_method in apis_to_try:
            try:
                matches = fetch_method(season)
                if matches:
                    logger.info(f"Successfully fetched {len(matches)} matches from {api_name}")
                    return matches
            except Exception as e:
                logger.warning(f"Failed to fetch from {api_name}: {e}")
                continue
        
        # All APIs failed, return demo data
        logger.warning("All APIs failed, using demo data")
        return self._get_demo_data()
    
    def _fetch_from_football_data_org(self, season: str) -> List[MatchData]:
        """Fetch data from football-data.org API."""
        url = f"{self.apis['football_data_org']['base_url']}/competitions/2021/matches"
        headers = self.apis['football_data_org']['headers']
        
        params = {
            'season': season,
            'status': 'FINISHED,SCHEDULED,LIVE'
        }
        
        response = self.session.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        matches = []
        
        for match in data.get('matches', []):
            match_data = MatchData(
                id=match['id'],
                date=match['utcDate'][:10],  # Extract date only
                season=season,
                league="Premier League",
                home_team=match['homeTeam']['name'],
                away_team=match['awayTeam']['name'],
                home_goals=match['score']['fullTime']['home'],
                away_goals=match['score']['fullTime']['away']
            )
            matches.append(match_data)
        
        logger.info(f"Fetched {len(matches)} matches from football-data.org")
        return matches
    
    def _fetch_from_rapidapi(self, season: str) -> List[MatchData]:
        """Fetch data from RapidAPI football endpoint."""
        url = f"{self.apis['rapidapi']['base_url']}/fixtures"
        headers = self.apis['rapidapi']['headers']
        
        # Premier League ID in RapidAPI
        league_id = 39
        
        params = {
            'league': league_id,
            'season': season
        }
        
        response = self.session.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        matches = []
        
        for fixture in data.get('response', []):
            match_data = MatchData(
                id=fixture['fixture']['id'],
                date=fixture['fixture']['date'][:10],
                season=season,
                league="Premier League",
                home_team=fixture['teams']['home']['name'],
                away_team=fixture['teams']['away']['name'],
                home_goals=fixture['goals']['home'],
                away_goals=fixture['goals']['away']
            )
            matches.append(match_data)
        
        logger.info(f"Fetched {len(matches)} matches from RapidAPI")
        return matches
    
    def _fetch_from_footystats(self, season: str) -> List[MatchData]:
        """Fetch data from FootyStats API."""
        self._wait_for_rate_limit('footystats')
        
        url = f"{self.apis['footystats']['base_url']}/league-matches"
        headers = self.apis['footystats']['headers']
        
        # FootyStats uses league ID for Premier League
        params = {
            'league_id': 2,  # Premier League
            'season_id': self._get_footystats_season_id(season)
        }
        
        response = self.session.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        matches = []
        
        if 'data' in data:
            for match in data['data']:
                # Extract match details
                home_team = match.get('home_name', '')
                away_team = match.get('away_name', '')
                match_date = match.get('date_unix', '')
                
                # Convert Unix timestamp to date
                if match_date:
                    match_date = datetime.fromtimestamp(int(match_date)).strftime('%Y-%m-%d')
                
                match_data = MatchData(
                    id=match.get('id', 0),
                    date=match_date,
                    season=season,
                    league="Premier League",
                    home_team=home_team,
                    away_team=away_team,
                    home_goals=match.get('home_goals'),
                    away_goals=match.get('away_goals'),
                    home_odds_wd=match.get('odds_home_win_draw'),
                    away_odds_wd=match.get('odds_away_win_draw'),
                    home_rating=match.get('home_team_rating', 75.0),
                    away_rating=match.get('away_team_rating', 75.0),
                    home_errors=match.get('home_errors', 0),
                    away_errors=match.get('away_errors', 0),
                    home_red_cards=match.get('home_red_cards', 0),
                    away_red_cards=match.get('away_red_cards', 0),
                    home_shots=match.get('home_shots', 0),
                    away_shots=match.get('away_shots', 0)
                )
                matches.append(match_data)
        
        logger.info(f"Fetched {len(matches)} matches from FootyStats")
        return matches
    
    def _get_footystats_season_id(self, season: str) -> int:
        """Convert year to FootyStats season ID."""
        year = int(season)
        # FootyStats season mapping (this may need adjustment based on their API)
        season_mapping = {
            2025: 2025, 2024: 2024, 2023: 2023, 2022: 2022, 2021: 2021,
            2020: 2020, 2019: 2019, 2018: 2018, 2017: 2017, 2016: 2016,
            2015: 2015, 2014: 2014, 2013: 2013, 2012: 2012, 2011: 2011
        }
        return season_mapping.get(year, year)
    
    def _wait_for_rate_limit(self, api_name: str):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        
        if api_name not in self._last_request_times:
            self._last_request_times[api_name] = current_time
            self._request_counts[api_name] = 0
            return
        
        # Get rate limit for this API
        rate_limit = self.apis[api_name]['rate_limit']
        
        # Simple rate limiting: wait 1 second between requests for high-volume APIs
        if api_name in ['footystats', 'rapidapi']:
            time_since_last = current_time - self._last_request_times[api_name]
            if time_since_last < 1.0:  # Wait at least 1 second
                time.sleep(1.0 - time_since_last)
        
        self._last_request_times[api_name] = time.time()
        self._request_counts[api_name] = self._request_counts.get(api_name, 0) + 1
    
    def fetch_historical_data_bulk(self, start_year: int = 2020, end_year: int = 2025) -> Dict[str, List[MatchData]]:
        """
        Fetch historical data for multiple seasons efficiently.
        
        :param start_year: Starting year
        :param end_year: Ending year
        :return: Dictionary mapping season to matches
        """
        logger.info(f"Fetching bulk historical data from {start_year} to {end_year}")
        
        all_data = {}
        
        for year in range(start_year, end_year + 1):
            season = str(year)
            logger.info(f"Fetching data for season {season}")
            
            try:
                matches = self.fetch_premier_league_fixtures(season)
                all_data[season] = matches
                logger.info(f"Fetched {len(matches)} matches for season {season}")
                
                # Small delay between seasons to be respectful to APIs
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to fetch data for season {season}: {e}")
                all_data[season] = []
        
        total_matches = sum(len(matches) for matches in all_data.values())
        logger.info(f"Bulk fetch complete: {total_matches} total matches across {len(all_data)} seasons")
        
        return all_data
    
    def _get_demo_data(self) -> List[MatchData]:
        """Generate demo data when APIs are unavailable."""
        logger.warning("Using demo data - APIs unavailable")
        
        teams = [
            "Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United",
            "Tottenham", "Newcastle", "Brighton", "Aston Villa", "West Ham",
            "Crystal Palace", "Fulham", "Wolves", "Everton", "Brentford",
            "Nottingham Forest", "Bournemouth", "Sheffield United", "Burnley", "Luton Town"
        ]
        
        matches = []
        for i in range(50):  # Generate 50 demo matches
            home_team = teams[i % len(teams)]
            away_team = teams[(i + 1) % len(teams)]
            
            if home_team != away_team:
                match_data = MatchData(
                    id=1000 + i,
                    date=(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                    season="2024",
                    league="Premier League",
                    home_team=home_team,
                    away_team=away_team,
                    home_goals=2,
                    away_goals=1,
                    home_odds_wd=1.8,
                    away_odds_wd=2.1,
                    home_rating=75.5,
                    away_rating=72.3,
                    home_errors=2,
                    away_errors=3,
                    home_red_cards=0,
                    away_red_cards=0,
                    home_shots=12,
                    away_shots=8
                )
                matches.append(match_data)
        
        return matches
    
    def fetch_team_statistics(self, team_name: str, season: str = "2024") -> Dict[str, Any]:
        """
        Fetch detailed statistics for a specific team.
        
        :param team_name: Name of the team
        :param season: Season year
        :return: Dictionary containing team statistics
        """
        try:
            # Try to fetch from available APIs
            return self._fetch_team_stats_football_data_org(team_name, season)
        except Exception as e:
            logger.warning(f"Failed to fetch team stats: {e}")
            # Return demo stats
            return {
                'team': team_name,
                'season': season,
                'matches_played': 20,
                'wins': 12,
                'draws': 5,
                'losses': 3,
                'goals_for': 35,
                'goals_against': 18,
                'rating': 75.5,
                'errors': 25,
                'red_cards': 2,
                'shots_total': 240
            }
    
    def _fetch_team_stats_football_data_org(self, team_name: str, season: str) -> Dict[str, Any]:
        """Fetch team statistics from football-data.org."""
        # First get team standings
        url = f"{self.apis['football_data_org']['base_url']}/competitions/2021/standings"
        headers = self.apis['football_data_org']['headers']
        
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        for standing in data.get('standings', [{}])[0].get('table', []):
            if standing['team']['name'] == team_name:
                return {
                    'team': team_name,
                    'season': season,
                    'matches_played': standing['playedGames'],
                    'wins': standing['won'],
                    'draws': standing['draw'],
                    'losses': standing['lost'],
                    'goals_for': standing['goalsFor'],
                    'goals_against': standing['goalsAgainst'],
                    'rating': 75.0,  # Default rating
                    'errors': 20,    # Default errors
                    'red_cards': 2,  # Default red cards
                    'shots_total': 200  # Default shots
                }
        
        raise ValueError(f"Team {team_name} not found in standings")
    
    def test_api_connections(self) -> Dict[str, bool]:
        """
        Test connections to all configured APIs.
        
        :return: Dictionary showing which APIs are working
        """
        results = {}
        
        # Test football-data.org
        try:
            url = f"{self.apis['football_data_org']['base_url']}/competitions"
            response = self.session.get(url, headers=self.apis['football_data_org']['headers'])
            results['football_data_org'] = response.status_code == 200
        except Exception:
            results['football_data_org'] = False
        
        # Test RapidAPI
        try:
            url = f"{self.apis['rapidapi']['base_url']}/status"
            response = self.session.get(url, headers=self.apis['rapidapi']['headers'])
            results['rapidapi'] = response.status_code == 200
        except Exception:
            results['rapidapi'] = False
        
        return results