"""Pension calculator logic using Perplexity API with LangChain"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_UP

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


def calculate_pension_locally(user_data: UserData, official_tables: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Wylicz prognozowaną emeryturę wg aktualnych zasad ZUS.
    
    Wykorzystuje oficjalne wskaźniki z publikacji ZUS/GUS oraz załączonych tabel 
    (jeśli dostępne). Oblicza składki, kapitalizację, waloryzację i wysokość 
    świadczenia emerytalnego z uwzględnieniem płci i wieku emerytalnego.
    
    Args:
        user_data: Dane użytkownika (UserData object)
        official_tables: Opcjonalny słownik z oficjalnymi tabelami ZUS/GUS
            zawierający wskaźniki waloryzacji, rentowności, prognozy demograficzne
    
    Returns:
        Słownik JSON zawierający:
        - monthly_pension: miesięczna emerytura brutto (PLN)
        - details: szczegółowe obliczenia, formuły i współczynniki
    
    Zasady obliczeniowe (system ZUS obowiązujący od 1999):
    1. Składka emerytalna = 19.52% wynagrodzenia brutto
       - 12.22% trafia na subkonto (część kapitałowa)
       - 7.3% trafia na konto główne (część bazowa)
    2. Składki są waloryzowane rocznym wskaźnikiem waloryzacji
    3. Kapitał emerytalny = suma zwaloryzowanych składek
    4. Emerytura miesięczna = kapitał emerytalny / średnie dalsze trwanie życia (w miesiącach)
    5. Wiek emerytalny: mężczyźni 65 lat, kobiety 60 lat
    """
    
    logger.info(f"Starting local pension calculation for {user_data.gender}, age {user_data.age}")
    
    # ===== STAŁE I PARAMETRY SYSTEMOWE =====
    current_year = datetime.now().year
    
    # Składki emerytalne (obowiązujące od 1999)
    CONTRIBUTION_RATE_TOTAL = Decimal("0.1952")  # 19.52% całkowita składka
    CONTRIBUTION_RATE_MAIN = Decimal("0.1222")   # 12.22% na konto główne
    CONTRIBUTION_RATE_SUB = Decimal("0.073")     # 7.3% na subkonto
    
    # Wiek emerytalny według płci
    retirement_age = RETIREMENT_AGE[user_data.gender]
    
    # Średnie dalsze trwanie życia w miesiącach (wg GUS 2024)
    life_expectancy_months = Decimal(str(LIFE_EXPECTANCY_MONTHS[user_data.gender]))
    
    # Wskaźniki waloryzacji i rentowności
    if official_tables and "valorization_indices" in official_tables:
        # Użyj danych z oficjalnych tabel jeśli dostępne
        # Konwertuj float na Decimal dla precyzji
        valorization_indices = {
            int(year): Decimal(str(value)) 
            for year, value in official_tables["valorization_indices"].items()
        }
        profitability_indices = {
            int(year): Decimal(str(value)) 
            for year, value in official_tables.get("profitability_indices", {}).items()
        }
        logger.info("Using official valorization tables from provided data")
    else:
        # Domyślne wskaźniki waloryzacji (średnie historyczne i prognozy ZUS/GUS)
        # Źródło: Fundusz Emerytalny 2023-2080, prognozy ZUS
        valorization_indices = {
            # Historyczne (2015-2024) - rzeczywiste dane ZUS
            2015: Decimal("1.0407"),  # 4.07%
            2016: Decimal("1.0039"),  # 0.39%
            2017: Decimal("1.0464"),  # 4.64%
            2018: Decimal("1.0529"),  # 5.29%
            2019: Decimal("1.0643"),  # 6.43%
            2020: Decimal("1.0486"),  # 4.86%
            2021: Decimal("1.0524"),  # 5.24%
            2022: Decimal("1.1086"),  # 10.86%
            2023: Decimal("1.1439"),  # 14.39%
            2024: Decimal("1.1266"),  # 12.66%
            # Prognozy (2025-2080) - na podstawie projekcji ZUS
            2025: Decimal("1.0580"),  # 5.8% prognoza
            2026: Decimal("1.0520"),  # 5.2%
            2027: Decimal("1.0480"),  # 4.8%
            2028: Decimal("1.0450"),  # 4.5%
            2029: Decimal("1.0430"),  # 4.3%
            2030: Decimal("1.0420"),  # 4.2%
        }
        # Wskaźnik rentowności subkonta (stopa zwrotu z OFE/portfela obligacji)
        profitability_indices = {}
        logger.info("Using default valorization indices (historical + ZUS projections)")
    
    # Wypełnij brakujące lata wskaźnikiem bazowym (dla lat po 2030)
    DEFAULT_VALORIZATION = Decimal("1.0400")  # 4% - długoterminowa prognoza ZUS
    DEFAULT_PROFITABILITY = Decimal("1.0350")  # 3.5% - rentowność subkonta
    
    # Minimalna emerytura (2025)
    minimum_pension = Decimal(str(MINIMUM_PENSION_2025))
    
    # ===== PRZYGOTOWANIE DANYCH WEJŚCIOWYCH =====
    
    # Konwersja danych użytkownika na Decimal dla precyzyjnych obliczeń
    gross_salary = Decimal(str(user_data.gross_salary))
    work_start_year = user_data.work_start_year
    
    # Określ rok przejścia na emeryturę
    if user_data.work_end_year:
        work_end_year = user_data.work_end_year
    else:
        # Oblicz rok przejścia na emeryturę na podstawie wieku emerytalnego
        years_worked = current_year - work_start_year
        current_user_age = user_data.age
        work_end_year = current_year + (retirement_age - current_user_age)
    
    # Walidacja
    if work_end_year < work_start_year:
        raise ValueError(f"Invalid work period: end year {work_end_year} < start year {work_start_year}")
    
    total_work_years = work_end_year - work_start_year
    years_worked_so_far = current_year - work_start_year
    remaining_years = max(0, work_end_year - current_year)
    
    # ===== OBLICZENIE SKŁADEK I KAPITAŁU EMERYTALNEGO =====
    
    # Inicjalizacja kapitału
    main_account_capital = Decimal("0")  # Konto główne (12.22%)
    sub_account_capital = Decimal("0")   # Subkonto (7.3%)
    
    # Użyj istniejących sald jeśli dostępne
    if user_data.zus_account_balance:
        main_account_capital = Decimal(str(user_data.zus_account_balance))
        logger.info(f"Starting with existing main account balance: {main_account_capital} PLN")
    
    if user_data.zus_subaccount_balance:
        sub_account_capital = Decimal(str(user_data.zus_subaccount_balance))
        logger.info(f"Starting with existing sub-account balance: {sub_account_capital} PLN")
    
    # Listy do śledzenia składek i waloryzacji (audyt)
    yearly_contributions = []
    valorization_log = []
    
    # Średni wzrost wynagrodzeń (historyczny 3-5% + inflacja)
    SALARY_GROWTH_RATE = Decimal("1.035")  # 3.5% rocznie
    
    # Oblicz składki i kapitalizację dla każdego roku
    current_salary_projection = gross_salary
    
    for year in range(work_start_year, work_end_year + 1):
        # Składka za dany rok
        if year <= current_year:
            # Lata historyczne - użyj obecnej pensji (uproszczenie) lub średniej
            yearly_salary = gross_salary
        else:
            # Lata przyszłe - prognoza ze wzrostem wynagrodzeń
            years_forward = year - current_year
            yearly_salary = gross_salary * (SALARY_GROWTH_RATE ** years_forward)
        
        # Zmniejszenie z tytułu zwolnień lekarskich
        sick_leave_reduction = Decimal("1.0")
        if user_data.sick_leave_days_per_year:
            # Zwolnienia lekarskie zmniejszają podstawę wymiaru składek
            # (maksymalnie 182 dni L4 płatne przez ZUS, 33 dni przez pracodawcę)
            working_days_per_year = Decimal("250")  # dni roboczych
            sick_days = Decimal(str(user_data.sick_leave_days_per_year))
            sick_leave_reduction = (working_days_per_year - sick_days) / working_days_per_year
        
        effective_salary = yearly_salary * sick_leave_reduction
        
        # Składki na oba konta
        contribution_main = effective_salary * CONTRIBUTION_RATE_MAIN * Decimal("12")  # 12 miesięcy
        contribution_sub = effective_salary * CONTRIBUTION_RATE_SUB * Decimal("12")
        
        # Dodaj do kapitału
        main_account_capital += contribution_main
        sub_account_capital += contribution_sub
        
        yearly_contributions.append({
            "year": year,
            "salary": float(yearly_salary),
            "effective_salary": float(effective_salary),
            "contribution_main": float(contribution_main),
            "contribution_sub": float(contribution_sub),
            "sick_leave_factor": float(sick_leave_reduction)
        })
        
        # Waloryzacja kapitału na koniec roku (jeśli nie jest to ostatni rok)
        if year < work_end_year:
            # Pobierz wskaźnik waloryzacji
            val_index_main = valorization_indices.get(year + 1, DEFAULT_VALORIZATION)
            prof_index_sub = profitability_indices.get(year + 1, DEFAULT_PROFITABILITY)
            
            # Waloryzacja konta głównego
            main_account_capital *= val_index_main
            
            # Rentowność subkonta (zazwyczaj niższa niż waloryzacja)
            sub_account_capital *= prof_index_sub
            
            valorization_log.append({
                "year": year + 1,
                "valorization_index_main": float(val_index_main),
                "profitability_index_sub": float(prof_index_sub),
                "main_account_after_valorization": float(main_account_capital),
                "sub_account_after_profitability": float(sub_account_capital)
            })
    
    # Łączny kapitał emerytalny
    total_pension_capital = main_account_capital + sub_account_capital
    
    logger.info(f"Total pension capital calculated: {total_pension_capital} PLN")
    
    # ===== OBLICZENIE EMERYTURY MIESIĘCZNEJ =====
    
    # Formuła ZUS: Emerytura = Kapitał / Średnie dalsze trwanie życia (w miesiącach)
    monthly_pension_gross = total_pension_capital / life_expectancy_months
    
    # Sprawdzenie minimalnej emerytury
    if monthly_pension_gross < minimum_pension:
        logger.warning(f"Calculated pension {monthly_pension_gross} below minimum {minimum_pension}")
        pension_gap = minimum_pension - monthly_pension_gross
        # ZUS wypłaca minimum, jeśli składki są za niskie
        monthly_pension_adjusted = minimum_pension
    else:
        pension_gap = Decimal("0")
        monthly_pension_adjusted = monthly_pension_gross
    
    # ===== WSKAŹNIKI DODATKOWE =====
    
    # Stopa zastąpienia (replacement rate)
    # Ostatnia prognozowana pensja
    final_salary = gross_salary * (SALARY_GROWTH_RATE ** remaining_years)
    replacement_rate = (monthly_pension_adjusted / final_salary) * Decimal("100")
    
    # Wpływ zwolnień lekarskich
    sick_leave_impact = None
    if user_data.sick_leave_days_per_year and user_data.sick_leave_days_per_year > 0:
        # Oblicz emeryturę bez zwolnień dla porównania
        sick_days = Decimal(str(user_data.sick_leave_days_per_year))
        working_days = Decimal("250")
        loss_factor = sick_days / working_days
        estimated_loss_per_year = gross_salary * CONTRIBUTION_RATE_TOTAL * Decimal("12") * loss_factor
        total_loss = estimated_loss_per_year * Decimal(str(total_work_years))
        # Zwaloryzuj stratę (średnio)
        avg_valorization = Decimal("1.05")  # średnia waloryzacja 5%
        avg_years = Decimal(str(total_work_years)) / Decimal("2")
        valorized_loss = total_loss * (avg_valorization ** avg_years)
        sick_leave_impact = valorized_loss / life_expectancy_months
    
    # Ile lat trzeba pracować dłużej, żeby osiągnąć wyższą emeryturę
    # (np. żeby przekroczyć 3000 PLN lub osiągnąć 60% replacement rate)
    target_pension = max(Decimal("3000"), final_salary * Decimal("0.60"))
    if monthly_pension_adjusted < target_pension:
        # Oszacuj dodatkowe lata
        monthly_contribution_avg = gross_salary * CONTRIBUTION_RATE_TOTAL
        annual_capital_gain = monthly_contribution_avg * Decimal("12") * DEFAULT_VALORIZATION
        capital_needed = (target_pension * life_expectancy_months) - total_pension_capital
        years_to_work_longer = int((capital_needed / annual_capital_gain).to_integral_value(ROUND_HALF_UP))
        years_to_work_longer = max(0, years_to_work_longer)
    else:
        years_to_work_longer = 0
    
    # ===== PRZYGOTOWANIE WYNIKU =====
    
    result = {
        "monthly_pension": float(monthly_pension_adjusted.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "details": {
            # Podstawowe informacje
            "calculation_date": datetime.now().isoformat(),
            "user_info": {
                "age": user_data.age,
                "gender": user_data.gender,
                "current_salary": float(gross_salary),
                "work_start_year": work_start_year,
                "work_end_year": work_end_year,
                "retirement_age": retirement_age,
                "total_work_years": total_work_years,
                "years_worked_so_far": years_worked_so_far,
                "remaining_years": remaining_years
            },
            
            # Kapitał emerytalny
            "pension_capital": {
                "main_account": float(main_account_capital.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "sub_account": float(sub_account_capital.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "total_capital": float(total_pension_capital.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "life_expectancy_months": float(life_expectancy_months)
            },
            
            # Formuły i współczynniki
            "formulas": {
                "contribution_formula": "Składka = Wynagrodzenie brutto × 19.52%",
                "main_account_rate": "12.22% wynagrodzenia brutto",
                "sub_account_rate": "7.3% wynagrodzenia brutto",
                "valorization_formula": "Kapitał(rok N) = Kapitał(rok N-1) × Wskaźnik waloryzacji",
                "pension_formula": "Emerytura miesięczna = Kapitał emerytalny / Średnie dalsze trwanie życia (miesiące)",
                "replacement_rate_formula": "Stopa zastąpienia = (Emerytura / Ostatnie wynagrodzenie) × 100%"
            },
            
            # Współczynniki
            "coefficients": {
                "contribution_rate_total": float(CONTRIBUTION_RATE_TOTAL),
                "contribution_rate_main": float(CONTRIBUTION_RATE_MAIN),
                "contribution_rate_sub": float(CONTRIBUTION_RATE_SUB),
                "salary_growth_rate_annual": float(SALARY_GROWTH_RATE),
                "default_valorization_rate": float(DEFAULT_VALORIZATION),
                "default_profitability_rate": float(DEFAULT_PROFITABILITY),
                "minimum_pension_2025": float(minimum_pension)
            },
            
            # Wskaźniki emerytalne
            "pension_metrics": {
                "monthly_pension_gross": float(monthly_pension_gross.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "monthly_pension_adjusted": float(monthly_pension_adjusted.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "final_salary_projection": float(final_salary.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "replacement_rate_percent": float(replacement_rate.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "minimum_pension_gap": float(pension_gap.quantize(Decimal("0.01"), ROUND_HALF_UP)) if pension_gap > 0 else None,
                "years_to_work_longer": years_to_work_longer if years_to_work_longer > 0 else None,
                "sick_leave_impact_monthly": float(sick_leave_impact.quantize(Decimal("0.01"), ROUND_HALF_UP)) if sick_leave_impact else None
            },
            
            # Audyt - szczegółowe logi
            "audit_trail": {
                "yearly_contributions": yearly_contributions[-10:] if len(yearly_contributions) > 10 else yearly_contributions,  # ostatnie 10 lat
                "valorization_log": valorization_log[-10:] if len(valorization_log) > 10 else valorization_log,
                "total_contributions_count": len(yearly_contributions),
                "valorization_count": len(valorization_log)
            },
            
            # Źródła danych
            "data_sources": {
                "valorization_indices_source": "Official tables" if (official_tables and "valorization_indices" in official_tables) else "ZUS historical data + projections (Fundusz Emerytalny 2023-2080)",
                "life_expectancy_source": "GUS 2024 - Tablice średniego dalszego trwania życia",
                "minimum_pension_source": "Rozporządzenie ZUS 2025",
                "contribution_rates_source": "Ustawa o systemie ubezpieczeń społecznych (19.52% od 1999)"
            },
            
            # Założenia
            "assumptions": [
                f"Wiek emerytalny: {retirement_age} lat ({user_data.gender})",
                f"Średnie dalsze trwanie życia: {float(life_expectancy_months)} miesięcy",
                f"Roczny wzrost wynagrodzeń: {float((SALARY_GROWTH_RATE - 1) * 100):.2f}%",
                f"Długoterminowa waloryzacja: {float((DEFAULT_VALORIZATION - 1) * 100):.2f}%",
                "Składka emerytalna: 19.52% (12.22% konto główne + 7.3% subkonto)",
                f"Minimalna emerytura 2025: {float(minimum_pension)} PLN"
            ]
        }
    }
    
    logger.info(f"Local calculation completed: {result['monthly_pension']} PLN/month")
    
    return result
