"""Flask API for pension calculations"""
import logging
from datetime import datetime
from flask import Flask, request, jsonify

from .calculator import PensionCalculator, calculate_pension_locally
from .models import PensionCalculationRequest, UserData
from .config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_LEVEL, LOG_FORMAT
from .validation import validate_uaser_data, sanity_check_pension
from .result_formatter import build_pension_result_json, format_validation_errors
from .pdf_parser import get_mock_zus_tables

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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "calculator_initialized": calculator is not None
    }), 200


@app.route('/api/calculate_pension', methods=['POST'])
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


@app.route('/api/calculate_pension_local', methods=['POST'])
def calculate_pension_local():
    """
    Calculate pension locally using ZUS statistics (no AI API call).
    Uses official indices and formulas from ZUS/GUS publications.
    
    Request JSON:
    {
        "user_data": {
            "age": 35,
            "gender": "male",
            "gross_salary": 8000.0,
            "work_start_year": 2010,
            "work_end_year": 2054,
            "zus_account_balance": 50000.0,  // optional
            "zus_subaccount_balance": 20000.0,  // optional
            "sick_leave_days_per_year": 10  // optional
        },
        "official_tables": {  // optional
            "valorization_indices": {
                "2024": 1.1266,
                "2025": 1.0580,
                ...
            },
            "profitability_indices": {
                "2024": 1.0350,
                ...
            }
        }
    }
    """
    logger.info("Local pension calculation endpoint called")
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            logger.warning("No JSON data provided in request")
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate request
        if 'user_data' not in data:
            logger.warning("Missing user_data field in request")
            return jsonify({"error": "user_data field is required"}), 400

        # Parse user data
        user_data_dict = data['user_data']
        logger.info(f"Processing local calculation for user: age={user_data_dict.get('age')}, "
                   f"gender={user_data_dict.get('gender')}, salary={user_data_dict.get('gross_salary')}")

        # Create UserData object
        user_data = UserData(**user_data_dict)
        
        # Validate user data
        validation_result = validate_user_data(user_data)
        if not validation_result["valid"]:
            logger.warning(f"Validation failed: {validation_result['errors']}")
            return jsonify(format_validation_errors(validation_result, user_data_dict)), 400
        
        # Log warnings if any
        if validation_result.get("warnings"):
            logger.info(f"Validation warnings: {validation_result['warnings']}")
        
        # Get optional official tables or use defaults
        official_tables = data.get('official_tables', None)
        if not official_tables:
            # Use mock tables with historical and projected data
            official_tables = get_mock_zus_tables()
            logger.info("Using default ZUS tables (historical + projections)")
        else:
            logger.info("Using provided official tables for calculation")
        
        # Perform calculation
        result = calculate_pension_locally(user_data, official_tables)
        
        # Perform sanity check
        sanity_result = sanity_check_pension(result, official_tables)
        
        # Build standardized response
        meta = {
            "calculation_date": datetime.now().isoformat(),
            "user_age": user_data.age,
            "user_gender": user_data.gender,
            "current_salary": user_data.gross_salary,
            "calculation_method": "local",
            "validation_warnings": validation_result.get("warnings", []),
            "sanity_check_status": sanity_result["status"],
            "sanity_check_diagnostic": sanity_result["diagnostic"]
        }
        
        formatted_result = build_pension_result_json(
            result.get("details", {}),
            meta,
            sanity_result["diagnostic"]
        )
        
        # Add monthly_pension at top level for easy access
        formatted_result["monthly_pension"] = result["monthly_pension"]
        
        # Add sanity check details
        formatted_result["sanity_check"] = sanity_result
        
        logger.info(f"Local calculation completed: {result['monthly_pension']:.2f} PLN/month, "
                   f"status: {sanity_result['status']}")
        return jsonify(formatted_result), 200

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            "error": f"Validation error: {str(e)}",
            "calculation_date": datetime.now().isoformat()
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error in calculate_pension_local: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "calculation_date": datetime.now().isoformat()
        }), 500


@app.route('/validate_user_data', methods=['POST'])
def validate_user_data_endpoint():
    """
    Validate user data without performing calculation.
    
    Request JSON:
    {
        "user_data": {
            "age": 35,
            "gender": "male",
            "gross_salary": 8000.0,
            "work_start_year": 2010,
            ...
        }
    }
    
    Response:
    {
        "valid": true/false,
        "errors": [...],
        "warnings": [...]
    }
    """
    logger.info("Validation endpoint called")
    
    try:
        data = request.get_json()
        
        if not data or 'user_data' not in data:
            return jsonify({"error": "user_data field is required"}), 400
        
        user_data = UserData(**data['user_data'])
        validation_result = validate_user_data(user_data)
        
        logger.info(f"Validation result: {'PASS' if validation_result['valid'] else 'FAIL'}")
        return jsonify(validation_result), 200
        
    except Exception as e:
        logger.error(f"Error in validation: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 400


@app.route('/zus_tables', methods=['GET'])
def get_zus_tables():
    """
    Get default ZUS tables (valorization indices, demographics, etc.).
    
    Returns mock tables with historical data and projections.
    Useful for reference or as defaults for calculations.
    """
    logger.info("ZUS tables endpoint called")
    
    try:
        tables = get_mock_zus_tables()
        return jsonify(tables), 200
        
    except Exception as e:
        logger.error(f"Error getting ZUS tables: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500
