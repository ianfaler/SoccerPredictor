"""
Football Data Fetcher for retrieving data from various football APIs.
"""

import os
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

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
            }
        }
    
    def fetch_premier_league_fixtures(self, season: str = "2024") -> List[MatchData]:
        """
        Fetch Premier League fixtures for a given season.
        
        :param season: Season year (e.g., "2024" for 2024-25 season)
        :return: List of MatchData objects
        """
        try:
            # Try football-data.org first (free)
            return self._fetch_from_football_data_org(season)
        except Exception as e:
            logger.warning(f"Failed to fetch from football-data.org: {e}")
            try:
                # Fallback to RapidAPI
                return self._fetch_from_rapidapi(season)
            except Exception as e2:
                logger.error(f"Failed to fetch from RapidAPI: {e2}")
                # Return demo/mock data as last resort
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