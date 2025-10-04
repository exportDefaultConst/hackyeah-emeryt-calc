"""
Result formatting utilities for pension calculations.
Provides standardized JSON schemas for consistent API responses.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def build_pension_result_json(
    calc_details: Dict[str, Any],
    meta: Dict[str, Any],
    diagnostics: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stwórz jednolity wynik JSON dla UI/backend/panelu admina.
    
    Standaryzuje format wyników z różnych źródeł (lokalne obliczenia, API AI)
    do wspólnego schematu zawierającego:
    - Metadane (data, źródło, wersja)
    - Wyniki użytkownika (kwoty, wskaźniki)
    - Szczegóły obliczeniowe
    - Diagnostyka i ostrzeżenia
    
    Args:
        calc_details: Szczegóły obliczeń (kapitał, formuły, logi)
        meta: Metadane (data, użytkownik, źródło danych)
        diagnostics: Opcjonalne informacje diagnostyczne/ostrzeżenia
        
    Returns:
        Ustandaryzowany dict z pełnymi wynikami
    """
    logger.debug("Building standardized pension result JSON")
    
    # Wyodrębnij kluczowe wartości z calc_details
    pension_capital = calc_details.get("pension_capital", {})
    pension_metrics = calc_details.get("pension_metrics", {})
    user_info = calc_details.get("user_info", {})
    
    # Główna kwota emerytury
    monthly_pension = pension_metrics.get("monthly_pension_adjusted") or \
                     pension_metrics.get("monthly_pension_gross") or \
                     calc_details.get("monthly_pension")
    
    # Zindeksowana emerytura (uwzględniająca inflację)
    indexed_pension = pension_metrics.get("indexed_pension_projection") or monthly_pension
    
    # Stopa zastąpienia
    replacement_rate = pension_metrics.get("replacement_rate_percent") or \
                      calc_details.get("replacement_rate")
    
    # Dodatkowe lata pracy
    years_to_work_longer = pension_metrics.get("years_to_work_longer")
    
    # Wpływ zwolnień lekarskich
    sick_leave_impact = pension_metrics.get("sick_leave_impact_monthly") or \
                       calc_details.get("sick_leave_impact")
    
    # Wpływ zmienności pensji
    salary_variability_impact = calc_details.get("salary_variability_impact")
    
    # Różnica do minimum
    minimum_pension_gap = pension_metrics.get("minimum_pension_gap") or \
                         calc_details.get("minimum_pension_gap")
    
    # Przygotuj sekcję calculation_details
    calculation_details = {
        "contribution_rate": calc_details.get("coefficients", {}).get("contribution_rate_total") or 
                            calc_details.get("contribution_rate") or "19.52%",
        "total_contributions_estimated": pension_capital.get("total_capital"),
        "valorization_rate": calc_details.get("coefficients", {}).get("default_valorization_rate") or 
                            calc_details.get("valorization_rate") or "4.0%",
        "life_expectancy_months": pension_capital.get("life_expectancy_months"),
        "assumptions": calc_details.get("assumptions", [])
    }
    
    # Dodaj formuly jeśli dostępne
    if "formulas" in calc_details:
        calculation_details["formulas"] = calc_details["formulas"]
    
    # Dodaj audit trail jeśli dostępny
    if "audit_trail" in calc_details:
        calculation_details["audit_trail"] = calc_details["audit_trail"]
    
    # Dodaj źródła danych
    if "data_sources" in calc_details:
        calculation_details["data_sources"] = calc_details["data_sources"]
    
    # Przygotuj metadane
    metadata = {
        "calculation_date": meta.get("calculation_date") or datetime.now().isoformat(),
        "user_age": user_info.get("age") or meta.get("user_age"),
        "user_gender": user_info.get("gender") or meta.get("user_gender"),
        "current_salary": user_info.get("current_salary") or meta.get("current_salary"),
        "calculation_method": meta.get("calculation_method") or "local",
        "api_model": meta.get("api_model"),
        "version": meta.get("version") or "1.0.0"
    }
    
    # Dodaj diagnostykę jeśli dostępna
    if diagnostics:
        metadata["diagnostics"] = diagnostics
    
    # Zbuduj pełny wynik zgodny ze standardowym schematem
    result = {
        # Wyniki główne - dla użytkownika
        "pension_actual": monthly_pension,  # Aktualna wartość emerytury
        "pension_indexed": indexed_pension,  # Po uwzględnieniu inflacji
        "replacement_rate": replacement_rate,  # Stopa zastąpienia (%)
        "years_to_work_longer": years_to_work_longer,  # Dodatkowe lata pracy
        
        # Wpływy i korekty
        "sick_leave_impact": sick_leave_impact,
        "salary_variability_impact": salary_variability_impact,
        "minimum_pension_gap": minimum_pension_gap,
        
        # Szczegóły obliczeniowe
        "calculation_details": calculation_details,
        
        # Metadane
        "metadata": metadata,
        
        # Kompatybilność wsteczna - aliasy
        "current_pension_projection": monthly_pension,
        "indexed_pension_projection": indexed_pension,
        "monthly_pension": monthly_pension
    }
    
    # Dodaj pełne details jeśli dostępne (dla zaawansowanych użytkowników/debugowania)
    if calc_details:
        result["details"] = calc_details
    
    logger.info(f"Built standardized result: {monthly_pension:.2f} PLN/month, "
               f"replacement rate: {replacement_rate:.1f}%" if replacement_rate else "N/A")
    
    return result


def format_api_error(
    error_message: str,
    error_type: str = "calculation_error",
    user_data_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Formatuj błąd w standardowym formacie API.
    
    Args:
        error_message: Komunikat błędu
        error_type: Typ błędu (validation_error, calculation_error, api_error)
        user_data_summary: Opcjonalne podsumowanie danych użytkownika
        
    Returns:
        Standaryzowany dict z informacją o błędzie
    """
    error_response = {
        "error": True,
        "error_type": error_type,
        "error_message": error_message,
        "metadata": {
            "calculation_date": datetime.now().isoformat(),
            "status": "error"
        }
    }
    
    if user_data_summary:
        error_response["user_data_summary"] = user_data_summary
    
    logger.error(f"API Error [{error_type}]: {error_message}")
    
    return error_response


def format_validation_errors(
    validation_result: Dict[str, Any],
    user_data_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Formatuj błędy walidacji w standardowym formacie API.
    
    Args:
        validation_result: Wynik walidacji z validate_user_data()
        user_data_summary: Opcjonalne podsumowanie danych użytkownika
        
    Returns:
        Standaryzowany dict z informacją o błędach walidacji
    """
    if validation_result.get("valid"):
        # Brak błędów - zwróć sukces z ostrzeżeniami
        return {
            "error": False,
            "warnings": validation_result.get("warnings", []),
            "metadata": {
                "calculation_date": datetime.now().isoformat(),
                "status": "validated"
            }
        }
    
    # Są błędy - zwróć szczegóły
    error_response = {
        "error": True,
        "error_type": "validation_error",
        "error_message": "Dane użytkownika zawierają błędy",
        "validation_errors": validation_result.get("errors", []),
        "validation_warnings": validation_result.get("warnings", []),
        "metadata": {
            "calculation_date": datetime.now().isoformat(),
            "status": "validation_failed"
        }
    }
    
    if user_data_summary:
        error_response["user_data_summary"] = user_data_summary
    
    logger.warning(f"Validation failed: {len(validation_result.get('errors', []))} errors")
    
    return error_response
