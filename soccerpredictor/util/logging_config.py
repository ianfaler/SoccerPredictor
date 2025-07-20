"""
Centralized logging configuration for SoccerPredictor
"""

import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Set up centralized logging configuration.
    
    :param log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param log_file: Optional log file path
    :return: Configured logger
    """
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Default log file with timestamp
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"soccerpredictor_{timestamp}.log"
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            },
            'json': {
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(log_file),
                'mode': 'a',
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.FileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': str(logs_dir / 'errors.log'),
                'mode': 'a',
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'soccerpredictor': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'werkzeug': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'requests': {
                'level': 'WARNING',
                'handlers': ['file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'WARNING',
            'handlers': ['console', 'file']
        }
    }
    
    # Configure logging
    logging.config.dictConfig(config)
    
    # Get main logger
    logger = logging.getLogger('soccerpredictor')
    
    # Log startup message
    logger.info("="*60)
    logger.info("SoccerPredictor logging initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_file}")
    logger.info("="*60)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.
    
    :param name: Logger name (defaults to soccerpredictor)
    :return: Logger instance
    """
    if name is None:
        name = 'soccerpredictor'
    elif not name.startswith('soccerpredictor'):
        name = f'soccerpredictor.{name}'
    
    return logging.getLogger(name)