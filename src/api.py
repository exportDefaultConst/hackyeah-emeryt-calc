"""Flask API for pension calculations"""
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

from .calculator import PensionCalculator, calculate_pension_locally
from .models import PensionCalculationRequest, UserData
from .config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_LEVEL, LOG_FORMAT
from .validation import validate_user_data, sanity_check_pension
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

# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

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


@app.route('/api/validate_user_data', methods=['POST'])
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


@app.route('/api/zus_tables', methods=['GET'])
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


@app.route('/api/faq', methods=['POST'])
def generate_faq():
    """
    Generate personalized FAQ based on user's pension calculation.
    
    🌟 WOW FEATURE #1: AI-Generated Personalized Questions
    
    Uses AI to generate relevant questions based on user's specific situation:
    - "Ile dostają emeryci w mojej branży?"
    - "Jak wypadam na tle rówieśników?"
    - "Co jeśli nie będę pracować przez 5 lat?"
    - "Czy mogę liczyć na wcześniejszą emeryturę?"
    
    Request JSON:
    {
        "user_data": {
            "age": 35,
            "gender": "male",
            "gross_salary": 8000.0,
            "work_start_year": 2010,
            "industry": "IT",
            "position": "Senior Developer",
            ...
        },
        "calculation_result": {
            "monthly_pension": 4567.89,
            "replacement_rate": 37.5,
            ...
        }
    }
    
    Response:
    {
        "faq": [
            {
                "question": "Ile dostają emeryci w mojej branży?",
                "answer": "W branży IT średnia emerytura...",
                "relevance": "high"
            },
            ...
        ],
        "metadata": {...}
    }
    """
    logger.info("FAQ generation endpoint called")
    
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
        
        if not data or 'user_data' not in data:
            return jsonify({"error": "user_data field is required"}), 400
        
        user_data_dict = data['user_data']
        calculation_result = data.get('calculation_result', {})
        
        # Parse user data
        user_data = UserData(**user_data_dict)
        
        logger.info(f"Generating FAQ for user: age={user_data.age}, "
                   f"gender={user_data.gender}, industry={user_data.industry}")
        
        # Generate personalized prompt for FAQ
        monthly_pension = calculation_result.get('monthly_pension', 'nie obliczono')
        replacement_rate = calculation_result.get('replacement_rate', 'nie obliczono')
        
        # Check if user has desired pension goal
        desired_pension_info = ""
        pension_gap = None
        if user_data.desired_pension:
            pension_gap = user_data.desired_pension - (monthly_pension if isinstance(monthly_pension, (int, float)) else 0)
            if pension_gap > 0:
                desired_pension_info = f"""
        - WAŻNE: Użytkownik CHCE emeryturę: {user_data.desired_pension} PLN
        - LUKA: Brakuje mu {pension_gap:.0f} PLN do celu ({user_data.desired_pension} PLN)
        - Status: Emerytura NIE OSIĄGA celu użytkownika!
                """
            elif pension_gap < 0:
                desired_pension_info = f"""
        - DOBRA WIADOMOŚĆ: Użytkownik CHCE {user_data.desired_pension} PLN, a dostanie {monthly_pension} PLN
        - NADWYŻKA: {abs(pension_gap):.0f} PLN powyżej celu!
        - Status: Emerytura PRZEKRACZA oczekiwania użytkownika!
                """
            else:
                desired_pension_info = f"""
        - Użytkownik CHCE emeryturę: {user_data.desired_pension} PLN
        - Status: CEL OSIĄGNIĘTY! Prognoza = cel użytkownika
                """
        
        faq_prompt = f"""
        Jesteś ekspertem od polskiego systemu emerytalnego ZUS.
        
        Użytkownik właśnie obliczył swoją prognozowaną emeryturę. Oto jego sytuacja:
        - Wiek: {user_data.age} lat
        - Płeć: {user_data.gender}
        - Wynagrodzenie: {user_data.gross_salary} PLN brutto
        - Branża: {user_data.industry or 'nie podano'}
        - Stanowisko: {user_data.position or 'nie podano'}
        - Rok rozpoczęcia pracy: {user_data.work_start_year}
        - Prognozowana emerytura: {monthly_pension} PLN
        - Stopa zastąpienia: {replacement_rate}%
        {desired_pension_info}
        
        Wygeneruj 5-7 NAJBARDZIEJ ISTOTNYCH pytań, które ta osoba prawdopodobnie chce zadać
        dotyczących swojej emerytury i sytuacji emerytalnej. Pytania powinny być:
        - Personalizowane (uwzględniające branżę, wiek, płeć)
        - Praktyczne (dotyczące rzeczywistych decyzji życiowych)
        - Zróżnicowane (porównania, scenariusze "co jeśli", optymalizacje)
        
        {"⚠️ PRIORYTET: Jeśli użytkownik ma CEL emerytury i go NIE OSIĄGA, MUSISZ wygenerować pytania:" if pension_gap and pension_gap > 0 else ""}
        {"- 'Co muszę zrobić, aby osiągnąć moją docelową emeryturę X PLN?'" if pension_gap and pension_gap > 0 else ""}
        {"- 'Ile lat dłużej muszę pracować, aby dostać X PLN emerytury?'" if pension_gap and pension_gap > 0 else ""}
        {"- 'Jakie są opcje zwiększenia mojej emerytury do poziomu X PLN?'" if pension_gap and pension_gap > 0 else ""}
        {"- 'Czy realistyczne jest osiągnięcie emerytury X PLN przy mojej sytuacji?'" if pension_gap and pension_gap > 0 else ""}
        
        Dla każdego pytania podaj KONKRETNĄ, PRAKTYCZNĄ odpowiedź (2-3 zdania).
        {"W odpowiedziach na pytania o cel - podaj KONKRETNE LICZBY i DZIAŁANIA." if pension_gap and pension_gap > 0 else ""}
        
        Zwróć wynik w formacie JSON:
        {{
            "faq": [
                {{
                    "question": "Pytanie?",
                    "answer": "Szczegółowa odpowiedź bazująca na danych użytkownika...",
                    "relevance": "high|medium|low",
                    "category": "comparison|scenario|optimization|legal|goal"
                }}
            ]
        }}
        
        Uwzględnij pytania typu:
        {f"- JAK OSIĄGNĄĆ CEL {user_data.desired_pension} PLN (NAJWAŻNIEJSZE!)" if pension_gap and pension_gap > 0 else ""}
        - Porównania z rówieśnikami/branżą
        - Scenariusze "co jeśli" (przerwy w pracy, zmiana zarobków)
        - Optymalizacje (kiedy przejść na emeryturę, ile pracować dłużej)
        - Wcześniejsza emerytura / emerytura pomostowa
        - Wpływ dodatkowych oszczędności (IKE, IKZE, III filar)
        """
        
        # Call Perplexity API
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "Jesteś ekspertem od polskiego systemu emerytalnego i ZUS. Odpowiadasz konkretnie i praktycznie."),
            ("human", "{prompt}")
        ])
        
        chain = prompt_template | calculator.llm
        response = chain.invoke({"prompt": faq_prompt})
        
        # Parse JSON response
        import json
        content = response.content
        
        # Extract JSON from response
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        elif "{" in content and "}" in content:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            json_str = content[json_start:json_end]
        else:
            json_str = content
        
        result = json.loads(json_str)
        
        # Add metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "user_age": user_data.age,
            "user_industry": user_data.industry,
            "model": "perplexity-ai",
            "total_questions": len(result.get("faq", []))
        }
        
        # Add pension goal info to metadata if available
        if user_data.desired_pension:
            metadata["has_pension_goal"] = True
            metadata["desired_pension"] = float(user_data.desired_pension)
            metadata["actual_pension"] = float(monthly_pension)
            if pension_gap:
                metadata["pension_gap"] = float(pension_gap)
                metadata["gap_percentage"] = round((pension_gap / monthly_pension) * 100, 1)
        
        result["metadata"] = metadata
        
        logger.info(f"Generated {len(result.get('faq', []))} FAQ questions")
        return jsonify(result), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse FAQ JSON: {e}")
        return jsonify({
            "error": "Failed to parse AI response",
            "raw_response": response.content if 'response' in locals() else None
        }), 500
        
    except Exception as e:
        logger.error(f"Error generating FAQ: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "calculation_date": datetime.now().isoformat()
        }), 500


@app.route('/api/explain_terms', methods=['POST'])
def explain_terms():
    """
    Explain complex pension terminology in simple terms.
    
    🌟 WOW FEATURE #2: AI-Powered Pension Dictionary
    
    Uses AI to explain difficult pension concepts in easy-to-understand language,
    with examples relevant to the user's situation.
    
    Request JSON:
    {
        "terms": ["kapitał początkowy", "waloryzacja", "współczynnik zastąpienia"],
        "user_data": {  // Optional - for personalized examples
            "age": 35,
            "gross_salary": 8000.0,
            ...
        },
        "calculation_result": {  // Optional - for context
            "monthly_pension": 4567.89,
            ...
        }
    }
    
    Response:
    {
        "explanations": [
            {
                "term": "kapitał początkowy",
                "simple_explanation": "To pieniądze zgromadzone...",
                "detailed_explanation": "Kapitał początkowy to...",
                "example": "W Twoim przypadku, jeśli...",
                "related_terms": ["kapitał emerytalny", "składki"]
            },
            ...
        ],
        "metadata": {...}
    }
    """
    logger.info("Terms explanation endpoint called")
    
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
        
        if not data or 'terms' not in data:
            return jsonify({"error": "terms field is required (array of terms to explain)"}), 400
        
        terms = data['terms']
        user_data_dict = data.get('user_data', {})
        calculation_result = data.get('calculation_result', {})
        
        if not isinstance(terms, list) or len(terms) == 0:
            return jsonify({"error": "terms must be a non-empty array"}), 400
        
        logger.info(f"Explaining {len(terms)} pension terms")
        
        # Build context from user data if provided
        context = ""
        if user_data_dict:
            user_data = UserData(**user_data_dict)
            context = f"""
            Kontekst użytkownika (do personalizacji przykładów):
            - Wiek: {user_data.age} lat
            - Wynagrodzenie: {user_data.gross_salary} PLN brutto
            - Płeć: {user_data.gender}
            """
            if calculation_result.get('monthly_pension'):
                context += f"\n- Prognozowana emerytura: {calculation_result['monthly_pension']} PLN"
        
        # Generate explanation prompt
        terms_list = ", ".join([f'"{term}"' for term in terms])
        
        explanation_prompt = f"""
        Jesteś ekspertem od polskiego systemu emerytalnego, który wyjaśnia trudne pojęcia prostym językiem.
        
        {context}
        
        Wyjaśnij następujące terminy emerytalne: {terms_list}
        
        Dla każdego terminu podaj:
        1. **Proste wyjaśnienie** (1-2 zdania, jak dla osoby bez wiedzy o emeryturach)
        2. **Szczegółowe wyjaśnienie** (2-3 zdania z kontekstem prawnym/systemowym)
        3. **Przykład praktyczny** (najlepiej spersonalizowany do kontekstu użytkownika, jeśli podany)
        4. **Powiązane terminy** (lista 2-3 powiązanych pojęć)
        
        Zwróć wynik w formacie JSON:
        {{
            "explanations": [
                {{
                    "term": "nazwa terminu",
                    "simple_explanation": "Proste wyjaśnienie dla laika...",
                    "detailed_explanation": "Szczegółowe wyjaśnienie z kontekstem prawnym...",
                    "example": "Przykład: W Twoim przypadku...",
                    "related_terms": ["termin1", "termin2"],
                    "importance": "high|medium|low"
                }}
            ]
        }}
        
        Używaj prostego języka, unikaj żargonu. Jeśli musisz użyć kolejnego trudnego terminu, 
        wyjaśnij go w nawiasie.
        """
        
        # Call Perplexity API
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "Jesteś ekspertem emerytalnym, który wyjaśnia trudne pojęcia w prosty, zrozumiały sposób. Unikasz żargonu i używasz przykładów z życia."),
            ("human", "{prompt}")
        ])
        
        chain = prompt_template | calculator.llm
        response = chain.invoke({"prompt": explanation_prompt})
        
        # Parse JSON response
        import json
        content = response.content
        
        # Extract JSON from response
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        elif "{" in content and "}" in content:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            json_str = content[json_start:json_end]
        else:
            json_str = content
        
        result = json.loads(json_str)
        
        # Add metadata
        result["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "terms_count": len(terms),
            "terms_requested": terms,
            "model": "perplexity-ai",
            "personalized": bool(user_data_dict)
        }
        
        logger.info(f"Explained {len(result.get('explanations', []))} terms")
        return jsonify(result), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse explanation JSON: {e}")
        return jsonify({
            "error": "Failed to parse AI response",
            "raw_response": response.content if 'response' in locals() else None
        }), 500
        
    except Exception as e:
        logger.error(f"Error explaining terms: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "calculation_date": datetime.now().isoformat()
        }), 500


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500
