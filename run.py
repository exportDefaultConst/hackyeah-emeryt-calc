"""
Pension Calculator API Runner
Simple entry point to start the Flask API server
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api import app, logger
from src.config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Starting Polish Pension Calculator API")
    logger.info("="*60)
    logger.info(f"Host: {FLASK_HOST}")
    logger.info(f"Port: {FLASK_PORT}")
    logger.info(f"Debug: {FLASK_DEBUG}")
    logger.info("="*60)
    logger.info("")
    logger.info("Available endpoints:")
    logger.info(f"  - GET  http://{FLASK_HOST}:{FLASK_PORT}/health")
    logger.info(f"  - POST http://{FLASK_HOST}:{FLASK_PORT}/calculate_pension")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
