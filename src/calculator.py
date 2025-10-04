"""Pension calculator logic using Perplexity API with LangChain"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

from langchain_perplexity import ChatPerplexity
from langchain_core.prompts import ChatPromptTemplate

from .models import UserData, PensionCalculationRequest
from .config import (
    PERPLEXITY_API_KEY,
    PERPLEXITY_MODEL,
    PERPLEXITY_TEMPERATURE,
    PENSION_CONTRIBUTION_RATE,
    MINIMUM_PENSION_2025,
    RETIREMENT_AGE,
    LIFE_EXPECTANCY_MONTHS
)

logger = logging.getLogger(__name__)


class PensionCalculator:
    """Main class for pension calculation using Perplexity API with LangChain"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the calculator with Perplexity API key
        
        Args:
            api_key: Perplexity API key (if not provided, will look for PPLX_API_KEY env var)
        """
        self.api_key = api_key or PERPLEXITY_API_KEY
        if not self.api_key:
            raise ValueError("Perplexity API key must be provided or set in PPLX_API_KEY environment variable")

        logger.info(f"Initializing PensionCalculator with model: {PERPLEXITY_MODEL}")
        
        # Initialize ChatPerplexity with LangChain
        self.llm = ChatPerplexity(
            api_key=self.api_key,
            model=PERPLEXITY_MODEL,
            temperature=PERPLEXITY_TEMPERATURE
        )

        # Create prompt template for Polish pension calculation
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Jesteś ekspertem od polskiego systemu emerytalnego i ZUS. 
            Analizujesz dane użytkownika i obliczasz prognozowaną emeryturę uwzględniając:
            - Składki emerytalne (19.52% wynagrodzenia brutto)
            - Waloryzację składek i kapitału początkowego
            - Średnie dalsze trwanie życia
            - Wpływ zwolnień lekarskich na składki
            - Indeksację i inflację
            - Stopę zastąpienia (replacement rate)

            Zwróć wynik w formacie JSON z dokładnymi obliczeniami i uzasadnieniem."""),
            ("human", "{prompt}")
        ])

        # Create LangChain chain (prompt | llm)
        self.chain = self.prompt_template | self.llm
        logger.info("PensionCalculator initialized successfully with LangChain chain")


    def calculate_basic_parameters(self, user_data: UserData) -> Dict[str, Any]:
        """
        Calculate basic pension parameters based on user data
        
        Args:
            user_data: User data for calculation
            
        Returns:
            Dictionary with calculated parameters
        """
        logger.debug(f"Calculating parameters for user age {user_data.age}, gender {user_data.gender}")
        
        current_year = datetime.now().year
        years_worked = current_year - user_data.work_start_year
        
        # Set retirement year if not provided
        if user_data.work_end_year is None:
            retirement_age = RETIREMENT_AGE[user_data.gender]
            user_data.work_end_year = user_data.work_start_year + (retirement_age - (user_data.age - years_worked))
        
        remaining_years = max(0, user_data.work_end_year - current_year)
        
        # Calculate contributions
        monthly_contribution = user_data.gross_salary * PENSION_CONTRIBUTION_RATE
        annual_contribution = monthly_contribution * 12
        total_years = user_data.work_end_year - user_data.work_start_year
        
        # Estimate total contributions (accounting for salary growth)
        estimated_total_contributions = annual_contribution * total_years * 1.5
        
        # Get retirement parameters
        retirement_age = RETIREMENT_AGE[user_data.gender]
        avg_life_expectancy_months = LIFE_EXPECTANCY_MONTHS[user_data.gender]
        
        # Basic pension calculation (simplified)
        basic_pension = estimated_total_contributions / avg_life_expectancy_months
        basic_pension = max(basic_pension, MINIMUM_PENSION_2025)

        params = {
            "years_worked": years_worked,
            "remaining_years": remaining_years,
            "monthly_contribution": monthly_contribution,
            "estimated_total_contributions": estimated_total_contributions,
            "basic_pension": basic_pension,
            "retirement_age": retirement_age,
            "avg_life_expectancy_months": avg_life_expectancy_months
        }
        
        logger.debug(f"Calculated parameters: {params}")
        return params


    def generate_polish_prompt(self, user_data: UserData, parameters: Dict[str, Any]) -> str:
        """
        Generate Polish prompt for Perplexity API
        
        Args:
            user_data: User data
            parameters: Calculated parameters
            
        Returns:
            Polish prompt string
        """
        logger.debug("Generating Polish prompt for Perplexity API")
        
        prompt = f"""
        Oblicz dokładną prognozę emerytury dla osoby o następujących parametrach:

        DANE OBOWIĄZKOWE:
        - Wiek: {user_data.age} lat
        - Płeć: {user_data.gender}
        - Wysokość wynagrodzenia brutto: {user_data.gross_salary} PLN miesięcznie
        - Rok rozpoczęcia pracy: {user_data.work_start_year}
        - Planowany rok zakończenia pracy: {user_data.work_end_year}

        DODATKOWE INFORMACJE:
        - Branża/pozycja: {user_data.industry or 'nie podano'} / {user_data.position or 'nie podano'}
        - Firma: {user_data.company or 'nie podano'}

        DANE OPCJONALNE:
        - Środki zgromadzone na koncie ZUS: {user_data.zus_account_balance or 'nie podano'} PLN
        - Środki zgromadzone na subkoncie ZUS: {user_data.zus_subaccount_balance or 'nie podano'} PLN
        - Średnia liczba dni zwolnień lekarskich rocznie: {user_data.sick_leave_days_per_year or 'nie podano'}

        OBLICZONE PARAMETRY:
        - Lata przepracowane: {parameters['years_worked']}
        - Pozostałe lata do emerytury: {parameters['remaining_years']}
        - Miesięczna składka emerytalna: {parameters['monthly_contribution']:.2f} PLN

        Proszę o obliczenie:
        1. Rzeczywistej wysokości przyszłej emerytury (kwota brutto w PLN)
        2. Urealnionej (indeksowanej) wysokości emerytury uwzględniającej inflację
        3. Wpływu zwolnień lekarskich na wysokość emerytury
        4. Wpływu zmienności zarobków i waloryzacji składek
        5. Stopy zastąpienia (procent wynagrodzenia realizowany przez emeryturę)
        6. Porównania z minimalną emeryturą ({parameters['basic_pension']:.2f} PLN)
        7. Informacji, ile lat trzeba pracować dłużej, jeśli prognoza jest niższa od oczekiwanej

        Uwzględnij aktualne zasady ZUS, waloryzację składek, tabele średniego dalszego trwania życia GUS.

        Zwróć odpowiedź w formacie JSON z następującymi polami:
        {{
            "current_pension_projection": [kwota emerytury w PLN],
            "indexed_pension_projection": [kwota po indeksacji w PLN], 
            "replacement_rate": [stopa zastąpienia w %],
            "years_to_work_longer": [dodatkowe lata pracy lub null],
            "sick_leave_impact": [wpływ zwolnień w PLN lub null],
            "salary_variability_impact": [wpływ zmienności płac w PLN],
            "minimum_pension_gap": [różnica do minimum lub null],
            "calculation_details": {{
                "contribution_rate": "19.52%",
                "total_contributions_estimated": [łączne składki],
                "valorization_rate": "aktualna stopa waloryzacji",
                "life_expectancy_months": [miesiące życia na emeryturze],
                "assumptions": ["lista założeń obliczeniowych"]
            }}
        }}
        """
        return prompt.strip()


    def process_request(self, request: PensionCalculationRequest) -> Dict[str, Any]:
        """
        Process pension calculation request (synchronous version)
        
        Args:
            request: Pension calculation request
            
        Returns:
            Calculation results with metadata
        """
        logger.info("Processing pension calculation request")
        
        try:
            # Parse user data
            user_data = UserData(**request.user_data)
            logger.info(f"Processing for user: age={user_data.age}, gender={user_data.gender}, salary={user_data.gross_salary}")

            # Calculate basic parameters
            parameters = self.calculate_basic_parameters(user_data)

            # Generate Polish prompt
            if not request.prompt:
                prompt = self.generate_polish_prompt(user_data, parameters)
            else:
                # Use custom prompt with injected data
                prompt = request.prompt.format(
                    user_data=asdict(user_data),
                    parameters=parameters
                )

            # Call Perplexity API using LangChain chain
            logger.info("Calling Perplexity API via LangChain chain...")
            response = self.chain.invoke({"prompt": prompt})
            logger.info("Received response from Perplexity API")

            # Parse response - extract JSON from LLM response
            try:
                content = response.content
                
                # Extract JSON from response (handle markdown code blocks)
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
                logger.info("Successfully parsed JSON response from API")

                # Add metadata to result
                result["metadata"] = {
                    "calculation_date": datetime.now().isoformat(),
                    "user_age": user_data.age,
                    "user_gender": user_data.gender,
                    "current_salary": user_data.gross_salary,
                    "api_model": PERPLEXITY_MODEL
                }

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return {
                    "error": "Failed to parse API response",
                    "raw_response": response.content,
                    "calculation_date": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error processing pension calculation: {e}", exc_info=True)
            return {
                "error": str(e),
                "calculation_date": datetime.now().isoformat()
            }
