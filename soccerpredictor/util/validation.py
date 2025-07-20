"""
Input validation utilities for SoccerPredictor API
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from marshmallow import Schema, fields, validate, ValidationError

class SeasonValidator:
    """Validator for season parameters"""
    
    @staticmethod
    def validate_season(season: str) -> bool:
        """Validate season format (4-digit year)"""
        if not season:
            return False
        return bool(re.match(r'^\d{4}$', season)) and 2010 <= int(season) <= 2030

    @staticmethod
    def validate_season_list(seasons: List[str]) -> bool:
        """Validate list of seasons"""
        if not seasons or len(seasons) > 10:  # Reasonable limit
            return False
        return all(SeasonValidator.validate_season(s) for s in seasons)

class PaginationValidator:
    """Validator for pagination parameters"""
    
    @staticmethod
    def validate_limit(limit: int) -> int:
        """Validate and sanitize limit parameter"""
        if limit is None:
            return 100
        return max(1, min(limit, 1000))  # Between 1 and 1000
    
    @staticmethod
    def validate_offset(offset: int) -> int:
        """Validate and sanitize offset parameter"""
        if offset is None:
            return 0
        return max(0, offset)  # Non-negative

class TeamValidator:
    """Validator for team names"""
    
    VALID_TEAM_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s_\-\.]+$')
    
    @staticmethod
    def validate_team_name(team_name: str) -> bool:
        """Validate team name format"""
        if not team_name or len(team_name) > 50:
            return False
        return bool(TeamValidator.VALID_TEAM_NAME_PATTERN.match(team_name))

# Marshmallow schemas for request validation
class FixturesQuerySchema(Schema):
    """Schema for fixtures query parameters"""
    season = fields.Str(validate=validate.Regexp(r'^\d{4}$'), missing=None)
    team = fields.Str(validate=validate.Length(max=50), missing=None)
    limit = fields.Int(validate=validate.Range(min=1, max=1000), missing=100)
    offset = fields.Int(validate=validate.Range(min=0), missing=0)

class DataUpdateSchema(Schema):
    """Schema for data update requests"""
    seasons = fields.List(
        fields.Str(validate=validate.Regexp(r'^\d{4}$')),
        validate=validate.Length(max=10),
        missing=None
    )
    force_update = fields.Bool(missing=False)

class APIKeyConfigSchema(Schema):
    """Schema for API configuration validation"""
    FOOTBALL_DATA_API_KEY = fields.Str(validate=validate.Length(min=10), missing='')
    RAPIDAPI_KEY = fields.Str(validate=validate.Length(min=10), missing='')

def validate_request_data(schema: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate request data against schema
    
    :param schema: Marshmallow schema
    :param data: Request data
    :return: Validated data
    :raises: ValidationError if validation fails
    """
    try:
        return schema.load(data)
    except ValidationError as e:
        raise ValidationError(f"Validation failed: {e.messages}")

def sanitize_sql_input(value: str) -> str:
    """
    Sanitize input for SQL queries (additional safety layer)
    
    :param value: Input value
    :return: Sanitized value
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove potentially dangerous characters
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    sanitized = value
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()

def validate_api_keys(config: Dict[str, str]) -> Dict[str, bool]:
    """
    Validate API key configuration
    
    :param config: Configuration dictionary
    :return: Dictionary of API key validity
    """
    schema = APIKeyConfigSchema()
    
    try:
        validated_config = schema.load(config)
        return {
            'football_data_org': bool(validated_config.get('FOOTBALL_DATA_API_KEY')),
            'rapidapi': bool(validated_config.get('RAPIDAPI_KEY'))
        }
    except ValidationError:
        return {
            'football_data_org': False,
            'rapidapi': False
        }

def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate date range
    
    :param start_date: Start date in YYYY-MM-DD format
    :param end_date: End date in YYYY-MM-DD format
    :return: True if valid range
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return start <= end
    except ValueError:
        return False