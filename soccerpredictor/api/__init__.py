"""
Soccer Predictor API module for fetching external football data.
"""

from .football_data_fetcher import FootballDataFetcher
from .api_manager import APIManager

__all__ = ['FootballDataFetcher', 'APIManager']