"""
Flask REST API server for managing football data updates and providing endpoints.
"""

import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_compress import Compress
from flask_cors import CORS
from dotenv import load_dotenv
from marshmallow import ValidationError

from .api_manager import APIManager
from ..util.logging_config import get_logger, setup_logging
from ..util.validation import (
    FixturesQuerySchema, DataUpdateSchema, validate_request_data,
    PaginationValidator, SeasonValidator, TeamValidator, validate_api_keys
)

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging() if not get_logger().handlers else get_logger('api_server')

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
    
    # Enable compression and CORS
    Compress(app)
    CORS(app, origins=['http://localhost:3000', 'http://localhost:8080'])
    
    # Load API configuration from environment variables
    config = {
        'FOOTBALL_DATA_API_KEY': os.getenv('FOOTBALL_DATA_API_KEY', ''),
        'RAPIDAPI_KEY': os.getenv('RAPIDAPI_KEY', ''),
    }
    
    # Validate API keys
    api_key_status = validate_api_keys(config)
    if not any(api_key_status.values()):
        logger.warning("No valid API keys found. Application will use demo data only.")
    else:
        logger.info(f"API keys configured: {list(k for k, v in api_key_status.items() if v)}")
    
    # Initialize API manager
    api_manager = APIManager(config)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get comprehensive system status."""
        try:
            status = api_manager.test_endpoints()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/data/update', methods=['POST'])
    def update_data():
        """Update football data from external APIs."""
        try:
            data = request.get_json() or {}
            
            # Validate request data
            try:
                validated_data = validate_request_data(DataUpdateSchema(), data)
            except ValidationError as e:
                logger.warning(f"Invalid data update request: {e}")
                return jsonify({'error': str(e)}), 400
            
            seasons = validated_data.get('seasons')
            force_update = validated_data.get('force_update', False)
            
            logger.info(f"Starting data update for seasons: {seasons}, force: {force_update}")
            summary = api_manager.update_data(seasons, force_update)
            
            return jsonify(summary)
            
        except Exception as e:
            logger.error(f"Failed to update data: {e}", exc_info=True)
            return jsonify({
                'error': 'Internal server error during data update',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/data/stats', methods=['GET'])
    def get_data_stats():
        """Get database statistics."""
        try:
            stats = api_manager.get_database_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Failed to get data stats: {e}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/teams', methods=['GET'])
    def get_teams():
        """Get list of all teams in the database."""
        try:
            import sqlite3
            from ..util.constants import DATA_DIR, DB_FILE
            from pathlib import Path
            
            db_path = Path(DATA_DIR) / DB_FILE
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT t.id, t.name, t.full_name, COUNT(f.id) as matches_count
                FROM Teams t
                LEFT JOIN Fixtures f ON (t.id = f.homeTeamID OR t.id = f.awayTeamID)
                GROUP BY t.id, t.name, t.full_name
                ORDER BY t.name
            """)
            
            teams = []
            for row in cursor.fetchall():
                teams.append({
                    'id': row[0],
                    'name': row[1],
                    'full_name': row[2],
                    'matches_count': row[3]
                })
            
            conn.close()
            return jsonify({
                'teams': teams,
                'total_count': len(teams)
            })
            
        except Exception as e:
            logger.error(f"Failed to get teams: {e}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/fixtures', methods=['GET'])
    def get_fixtures():
        """Get fixtures with optional filtering."""
        try:
            import sqlite3
            from ..util.constants import DATA_DIR, DB_FILE
            from pathlib import Path
            
            # Get and validate query parameters
            query_params = {
                'season': request.args.get('season'),
                'team': request.args.get('team'),
                'limit': request.args.get('limit', 100, type=int),
                'offset': request.args.get('offset', 0, type=int)
            }
            
            try:
                validated_params = validate_request_data(FixturesQuerySchema(), query_params)
            except ValidationError as e:
                logger.warning(f"Invalid fixtures query: {e}")
                return jsonify({'error': str(e)}), 400
            
            season = validated_params.get('season')
            team = validated_params.get('team')
            limit = validated_params.get('limit', 100)
            offset = validated_params.get('offset', 0)
            
            db_path = Path(DATA_DIR) / DB_FILE
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Build query with optional filters
            base_query = """
                SELECT f.id, f.date, f.season, f.league,
                       t1.name as home_team, t2.name as away_team,
                       f.home_goals, f.away_goals, f.oddsDC_1X, f.oddsDC_X2
                FROM Fixtures f
                JOIN Teams t1 ON f.homeTeamID = t1.id
                JOIN Teams t2 ON f.awayTeamID = t2.id
            """
            
            conditions = []
            params = []
            
            if season:
                conditions.append("f.season = ?")
                params.append(season)
            
            if team:
                conditions.append("(t1.name = ? OR t2.name = ?)")
                params.extend([team, team])
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY f.date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(base_query, params)
            
            fixtures = []
            for row in cursor.fetchall():
                fixtures.append({
                    'id': row[0],
                    'date': row[1],
                    'season': row[2],
                    'league': row[3],
                    'home_team': row[4],
                    'away_team': row[5],
                    'home_goals': row[6],
                    'away_goals': row[7],
                    'home_odds_wd': row[8],
                    'away_odds_wd': row[9]
                })
            
            # Get total count for pagination
            count_query = "SELECT COUNT(*) FROM Fixtures f JOIN Teams t1 ON f.homeTeamID = t1.id JOIN Teams t2 ON f.awayTeamID = t2.id"
            if conditions:
                count_query += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(count_query, params[:-2])  # Remove limit and offset
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            return jsonify({
                'fixtures': fixtures,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to get fixtures: {e}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/predictions', methods=['GET'])
    def get_predictions():
        """Get current predictions from the model."""
        try:
            from ..util.common import get_latest_models_dir, get_prediction_file
            from ..util.enums import Dataset
            import pandas as pd
            import pickle
            
            # Get latest model directory
            model_dir = get_latest_models_dir("")
            
            predictions = {}
            
            # Load test and predict datasets
            for dataset in [Dataset.Test.value, Dataset.Predict.value]:
                try:
                    pred_file = get_prediction_file(model_dir, Dataset(dataset))
                    if pred_file.exists():
                        with open(pred_file, 'rb') as f:
                            data = pickle.load(f)
                            predictions[dataset] = {
                                'matches_count': len(data) if isinstance(data, (list, pd.DataFrame)) else 0,
                                'data_available': True
                            }
                    else:
                        predictions[dataset] = {
                            'matches_count': 0,
                            'data_available': False
                        }
                except Exception as e:
                    logger.warning(f"Failed to load {dataset} predictions: {e}")
                    predictions[dataset] = {
                        'matches_count': 0,
                        'data_available': False,
                        'error': str(e)
                    }
            
            return jsonify({
                'model_dir': str(model_dir),
                'predictions': predictions,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get predictions: {e}")
            return jsonify({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get API configuration (without sensitive data)."""
        return jsonify({
            'apis_configured': {
                'football_data_org': bool(config.get('FOOTBALL_DATA_API_KEY')),
                'rapidapi': bool(config.get('RAPIDAPI_KEY'))
            },
            'features': {
                'data_update': True,
                'predictions': True,
                'visualizations': True,
                'live_data': True
            }
        })
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Endpoint not found',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            'error': 'Internal server error',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    return app

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask API server."""
    app = create_app()
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)