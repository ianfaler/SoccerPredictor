# Football Data API Documentation

## Overview

The SoccerPredictor API system provides comprehensive endpoints for fetching, managing, and serving football data. The system supports multiple data sources and provides both REST API endpoints and command-line tools for data management.

## Features

- **Multi-source data fetching**: Supports football-data.org, RapidAPI, and fallback demo data
- **REST API server**: Flask-based API with comprehensive endpoints
- **Database management**: SQLite database with automatic schema creation
- **Data synchronization**: Automatic updates from external APIs
- **Command-line tools**: Easy-to-use CLI for data management
- **Health monitoring**: Comprehensive endpoint testing and monitoring

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment (Optional)

```bash
# Setup API keys interactively
python update_data.py setup-env

# Or create .env file manually:
echo "FOOTBALL_DATA_API_KEY=your_key_here" > .env
echo "RAPIDAPI_KEY=your_key_here" >> .env
```

### 3. Initialize and Update Data

```bash
# Test all endpoints
python update_data.py test

# Update football data
python update_data.py update

# Start API server
python update_data.py server --port 5000
```

### 4. Alternative: Use Main Script

```bash
# Start API server with data update
python main.py api --update-data --port 5000

# Start visualization (existing functionality)
python main.py vis --port 8050
```

## API Endpoints

### Health and Status

#### `GET /api/health`
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0"
}
```

#### `GET /api/status`
Comprehensive system status including database, API connections, and data fetch capabilities.

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "overall_status": true,
  "database": {
    "status": "ok",
    "message": "Database structure is valid",
    "tables": ["Teams", "TeamStats", "Fixtures"]
  },
  "api_connections": {
    "football_data_org": true,
    "rapidapi": false
  },
  "data_fetch": {
    "status": "ok",
    "message": "Successfully fetched 50 matches",
    "sample_match": {
      "home_team": "Arsenal",
      "away_team": "Chelsea",
      "date": "2024-01-15"
    }
  }
}
```

### Data Management

#### `POST /api/data/update`
Update football data from external APIs.

**Request Body:**
```json
{
  "seasons": ["2024", "2023"]  // Optional, defaults to current season
}
```

**Response:**
```json
{
  "updated_at": "2024-01-15T10:30:00.000Z",
  "seasons": ["2024"],
  "total_matches": 380,
  "new_matches": 25,
  "updated_matches": 5,
  "errors": []
}
```

#### `GET /api/data/stats`
Get database statistics.

**Response:**
```json
{
  "total_teams": 20,
  "total_fixtures": 760,
  "fixtures_by_season": {
    "2023": 380,
    "2024": 380
  },
  "last_updated": "2024-01-15T10:30:00.000Z"
}
```

### Teams

#### `GET /api/teams`
Get list of all teams in the database.

**Response:**
```json
{
  "teams": [
    {
      "id": 1,
      "name": "Arsenal",
      "full_name": "Arsenal",
      "matches_count": 38
    }
  ],
  "total_count": 20
}
```

### Fixtures

#### `GET /api/fixtures`
Get fixtures with optional filtering and pagination.

**Query Parameters:**
- `season` (string, optional): Filter by season (e.g., "2024")
- `team` (string, optional): Filter by team name
- `limit` (integer, optional): Number of results to return (default: 100)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "fixtures": [
    {
      "id": 12345,
      "date": "2024-01-15",
      "season": 2024,
      "league": "Premier League",
      "home_team": "Arsenal",
      "away_team": "Chelsea",
      "home_goals": 2,
      "away_goals": 1,
      "home_odds_wd": 1.8,
      "away_odds_wd": 2.1
    }
  ],
  "pagination": {
    "total_count": 760,
    "limit": 100,
    "offset": 0,
    "has_more": true
  }
}
```

### Predictions

#### `GET /api/predictions`
Get current predictions from the trained model.

**Response:**
```json
{
  "model_dir": "/path/to/model",
  "predictions": {
    "test": {
      "matches_count": 30,
      "data_available": true
    },
    "predict": {
      "matches_count": 4,
      "data_available": true
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Configuration

#### `GET /api/config`
Get API configuration information (without sensitive data).

**Response:**
```json
{
  "apis_configured": {
    "football_data_org": true,
    "rapidapi": false
  },
  "features": {
    "data_update": true,
    "predictions": true,
    "visualizations": true,
    "live_data": true
  }
}
```

## Command Line Interface

### Available Commands

#### `python update_data.py update [--seasons SEASONS...]`
Update football data from external APIs.

```bash
# Update current season
python update_data.py update

# Update specific seasons
python update_data.py update --seasons 2024 2023
```

#### `python update_data.py test`
Test all API endpoints and database connectivity.

```bash
python update_data.py test
```

#### `python update_data.py server [--host HOST] [--port PORT] [--debug]`
Start the REST API server.

```bash
# Start on default port 5000
python update_data.py server

# Start on custom port with debug mode
python update_data.py server --port 8000 --debug
```

#### `python update_data.py stats`
Show database statistics.

```bash
python update_data.py stats
```

#### `python update_data.py setup-env`
Interactive setup of environment configuration.

```bash
python update_data.py setup-env
```

## Data Sources

### Football Data API (football-data.org)
- **Free tier**: 10 requests per minute
- **Coverage**: Premier League, major European leagues
- **Registration**: https://www.football-data.org/client/register

### RapidAPI Football
- **Rate limits**: Varies by subscription
- **Coverage**: Worldwide football data
- **Registration**: https://rapidapi.com/

### Demo Data Fallback
When external APIs are unavailable, the system generates realistic demo data to ensure functionality.

## Database Schema

### Teams Table
```sql
CREATE TABLE Teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### TeamStats Table
```sql
CREATE TABLE TeamStats (
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
);
```

### Fixtures Table
```sql
CREATE TABLE Fixtures (
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
);
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Football Data API Configuration
FOOTBALL_DATA_API_KEY=your_free_api_key_here

# RapidAPI Configuration
RAPIDAPI_KEY=your_rapidapi_key_here
```

### API Rate Limits

- **Football Data API**: 10 requests/minute (free tier)
- **RapidAPI**: Varies by subscription plan
- **Automatic fallback**: Demo data when APIs are unavailable

## Integration Examples

### Python Integration

```python
from soccerpredictor.api.api_manager import APIManager

# Initialize with configuration
config = {
    'FOOTBALL_DATA_API_KEY': 'your_key',
    'RAPIDAPI_KEY': 'your_key'
}
api_manager = APIManager(config)

# Update data
summary = api_manager.update_data(['2024'])
print(f"Added {summary['new_matches']} new matches")

# Test endpoints
results = api_manager.test_endpoints()
print(f"Overall status: {results['overall_status']}")

# Get database stats
stats = api_manager.get_database_stats()
print(f"Total fixtures: {stats['total_fixtures']}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:5000/api/health

# Get system status
curl http://localhost:5000/api/status

# Update data
curl -X POST http://localhost:5000/api/data/update \
  -H "Content-Type: application/json" \
  -d '{"seasons": ["2024"]}'

# Get fixtures for Arsenal
curl "http://localhost:5000/api/fixtures?team=Arsenal&limit=10"

# Get database statistics
curl http://localhost:5000/api/data/stats
```

## Error Handling

### Common Error Responses

```json
{
  "error": "Error description",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (endpoint doesn't exist)
- `500`: Internal Server Error

## Performance Considerations

- **Database indexing**: Optimized indexes on frequently queried columns
- **Response compression**: Automatic gzip compression for API responses
- **Rate limiting**: Respects external API rate limits
- **Caching**: Database-level caching for frequently accessed data

## Monitoring and Logging

### Logs
The system logs important events:
- Data updates and synchronization
- API errors and fallbacks
- Database operations
- Server startup and shutdown

### Health Monitoring
Use the `/api/status` endpoint to monitor:
- Database connectivity
- External API availability
- Data freshness
- Overall system health

## Troubleshooting

### Common Issues

1. **Database not found**
   - Run `python update_data.py test` to initialize
   - Check file permissions in `data/` directory

2. **API keys not working**
   - Verify keys in `.env` file
   - Check API provider documentation
   - Test with `python update_data.py test`

3. **No data returned**
   - Run `python update_data.py update` to fetch data
   - Check API rate limits
   - Review logs for error messages

4. **Server won't start**
   - Check if port is already in use
   - Verify all dependencies are installed
   - Check firewall settings

### Debug Mode

Start the server in debug mode for detailed error information:

```bash
python update_data.py server --debug
```

## Support and Contributing

For issues, feature requests, or contributions, please refer to the project documentation and issue tracker.