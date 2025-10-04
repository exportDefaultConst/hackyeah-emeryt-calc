"""Flask API for pension calculations"""
import logging
from datetime import datetime
from flask import Flask, request, jsonify

from .calculator import PensionCalculator
from .models import PensionCalculationRequest
from .config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize calculator (will be set on first request)
calculator = None


@app.before_request
def initialize_calculator():
    """Initialize calculator on first request"""
    global calculator
    if calculator is None:
        try:
            logger.info("Initializing PensionCalculator...")
            calculator = PensionCalculator()
            logger.info("PensionCalculator initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize calculator: {e}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "calculator_initialized": calculator is not None
    }), 200


@app.route('/calculate_pension', methods=['POST'])
def calculate_pension():
    """Calculate pension based on user data"""
    logger.info("Pension calculation endpoint called")
    
    try:
        # Check if calculator is initialized
        if calculator is None:
            logger.error("Calculator not initialized - missing API key")
            return jsonify({
                "error": "Calculator not initialized. Please set PPLX_API_KEY environment variable",
                "calculation_date": datetime.now().isoformat()
            }), 500

        # Get request data
        data = request.get_json()
        
        if not data:
            logger.warning("No JSON data provided in request")
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate request
        if 'user_data' not in data:
            logger.warning("Missing user_data field in request")
            return jsonify({"error": "user_data field is required"}), 400

        # Log request details
        user_data = data['user_data']
        logger.info(f"Processing calculation for user: age={user_data.get('age')}, "
                   f"gender={user_data.get('gender')}, salary={user_data.get('gross_salary')}")

        # Create request object
        calc_request = PensionCalculationRequest(
            user_data=data['user_data'],
            prompt=data.get('prompt', '')
        )

        # Process calculation
        result = calculator.process_request(calc_request)

        # Check for errors in result
        if 'error' in result:
            logger.error(f"Calculation failed: {result['error']}")
            return jsonify(result), 500

        logger.info("Calculation completed successfully")
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Unexpected error in calculate_pension: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "calculation_date": datetime.now().isoformat()
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500
