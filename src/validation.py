"""
Validation utilities for pension calculation inputs and outputs.
Provides comprehensive validation for user data and sanity checks for results.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from .models import UserData
from .config import RETIREMENT_AGE, MINIMUM_PENSION_2025

logger = logging.getLogger(__name__)


def validate_user_data(user_data: UserData) -> Dict[str, Any]:
    """
    Waliduj dane użytkownika przed obliczeniami emeryturalnymi.
    
    Sprawdza:
    - Zakres wieku (18-67 lat)
    - Poprawność płci ('male'/'female', 'M'/'K')
    - Wysokość wynagrodzenia (dodatnia, realistyczna)
    - Logiczność dat rozpoczęcia/zakończenia pracy
    - Poprawność opcjonalnych pól (salda ZUS, L4)
    
    Args:
        user_data: Obiekt UserData do walidacji
        
    Returns:
        Dict zawierający:
        - valid (bool): True jeśli dane są poprawne
        - errors (List[str]): Lista błędów walidacji
        - warnings (List[str]): Lista ostrzeżeń (opcjonalnie)
    """
    errors: List[str] = []
    warnings: List[str] = []
    current_year = datetime.now().year
    
    # Walidacja wieku
    if not isinstance(user_data.age, int):
        errors.append("Wiek musi być liczbą całkowitą")
    elif user_data.age < 18:
        errors.append("Wiek nie może być mniejszy niż 18 lat")
    elif user_data.age > 67:
        errors.append("Wiek nie może być większy niż 67 lat")
    elif user_data.age < 20:
        warnings.append("Bardzo młody wiek - sprawdź czy dane są poprawne")
    
    # Walidacja płci
    valid_genders = ['male', 'female', 'M', 'K', 'm', 'f']
    if user_data.gender not in valid_genders:
        errors.append(f"Płeć musi być jedną z wartości: {', '.join(valid_genders)}")
    
    # Normalizacja płci do standardowego formatu
    gender_normalized = user_data.gender.lower()
    if gender_normalized in ['k', 'f']:
        gender_normalized = 'female'
    elif gender_normalized in ['m']:
        gender_normalized = 'male'
    
    # Walidacja wynagrodzenia brutto
    if not isinstance(user_data.gross_salary, (int, float)):
        errors.append("Wynagrodzenie musi być liczbą")
    elif user_data.gross_salary <= 0:
        errors.append("Wynagrodzenie musi być dodatnie")
    elif user_data.gross_salary < 3000:
        warnings.append(f"Niskie wynagrodzenie ({user_data.gross_salary} PLN) - poniżej płacy minimalnej")
    elif user_data.gross_salary > 100000:
        warnings.append(f"Bardzo wysokie wynagrodzenie ({user_data.gross_salary} PLN) - sprawdź poprawność")
    
    # Walidacja roku rozpoczęcia pracy
    if not isinstance(user_data.work_start_year, int):
        errors.append("Rok rozpoczęcia pracy musi być liczbą całkowitą")
    elif user_data.work_start_year < 1970:
        errors.append("Rok rozpoczęcia pracy nie może być wcześniejszy niż 1970")
    elif user_data.work_start_year > current_year:
        errors.append("Rok rozpoczęcia pracy nie może być w przyszłości")
    else:
        # Sprawdź czy wiek jest zgodny z rokiem rozpoczęcia pracy
        expected_age_at_start = current_year - user_data.work_start_year
        min_work_age = 18
        if expected_age_at_start > user_data.age:
            errors.append(f"Niespójność: wiek ({user_data.age}) vs rok rozpoczęcia pracy ({user_data.work_start_year})")
        elif (user_data.age - expected_age_at_start) < min_work_age:
            warnings.append(f"Rozpoczęcie pracy przed {min_work_age} rokiem życia - sprawdź dane")
    
    # Walidacja roku zakończenia pracy (opcjonalnie)
    if user_data.work_end_year is not None:
        if not isinstance(user_data.work_end_year, int):
            errors.append("Rok zakończenia pracy musi być liczbą całkowitą")
        elif user_data.work_end_year < user_data.work_start_year:
            errors.append("Rok zakończenia pracy nie może być wcześniejszy niż rok rozpoczęcia")
        elif user_data.work_end_year < current_year:
            warnings.append("Rok zakończenia pracy jest w przeszłości - osoba już na emeryturze?")
        elif user_data.work_end_year > current_year + 50:
            warnings.append("Bardzo odległy rok zakończenia pracy - sprawdź poprawność")
        
        # Sprawdź czy wiek emerytalny jest logiczny
        if gender_normalized in ['male', 'female']:
            retirement_age = RETIREMENT_AGE[gender_normalized]
            years_to_retirement = user_data.work_end_year - current_year
            expected_age_at_retirement = user_data.age + years_to_retirement
            
            if expected_age_at_retirement < retirement_age - 10:
                warnings.append(f"Wczesna emerytura - wiek {expected_age_at_retirement} (standardowy: {retirement_age})")
            elif expected_age_at_retirement > retirement_age + 5:
                warnings.append(f"Późna emerytura - wiek {expected_age_at_retirement} (standardowy: {retirement_age})")
    
    # Walidacja salda konta ZUS (opcjonalnie)
    if user_data.zus_account_balance is not None:
        if not isinstance(user_data.zus_account_balance, (int, float)):
            errors.append("Saldo konta ZUS musi być liczbą")
        elif user_data.zus_account_balance < 0:
            errors.append("Saldo konta ZUS nie może być ujemne")
        elif user_data.zus_account_balance > 5000000:
            warnings.append(f"Bardzo wysokie saldo ZUS ({user_data.zus_account_balance} PLN) - sprawdź poprawność")
    
    # Walidacja salda subkonta ZUS (opcjonalnie)
    if user_data.zus_subaccount_balance is not None:
        if not isinstance(user_data.zus_subaccount_balance, (int, float)):
            errors.append("Saldo subkonta ZUS musi być liczbą")
        elif user_data.zus_subaccount_balance < 0:
            errors.append("Saldo subkonta ZUS nie może być ujemne")
        elif user_data.zus_subaccount_balance > 2000000:
            warnings.append(f"Bardzo wysokie saldo subkonta ({user_data.zus_subaccount_balance} PLN)")
        
        # Sprawdź proporcje między kontami (subkonto zazwyczaj mniejsze)
        if user_data.zus_account_balance is not None:
            if user_data.zus_subaccount_balance > user_data.zus_account_balance:
                warnings.append("Subkonto większe niż konto główne - nietypowa sytuacja")
    
    # Walidacja dni zwolnień lekarskich (opcjonalnie)
    if user_data.sick_leave_days_per_year is not None:
        if not isinstance(user_data.sick_leave_days_per_year, (int, float)):
            errors.append("Liczba dni L4 musi być liczbą")
        elif user_data.sick_leave_days_per_year < 0:
            errors.append("Liczba dni L4 nie może być ujemna")
        elif user_data.sick_leave_days_per_year > 250:
            errors.append("Liczba dni L4 nie może przekraczać 250 dni rocznie")
        elif user_data.sick_leave_days_per_year > 100:
            warnings.append(f"Bardzo duża liczba dni L4 ({user_data.sick_leave_days_per_year}) - poważny wpływ na emeryturę")
    
    # Przygotuj wynik
    is_valid = len(errors) == 0
    
    result = {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings
    }
    
    if is_valid:
        logger.info(f"Walidacja danych użytkownika: OK (ostrzeżeń: {len(warnings)})")
    else:
        logger.warning(f"Walidacja danych użytkownika: BŁĄD ({len(errors)} błędów)")
        for error in errors:
            logger.warning(f"  - {error}")
    
    return result


def sanity_check_pension(
    pension_result: Dict[str, Any], 
    tables: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Sprawdź czy prognozowana emerytura mieści się w realnych granicach.
    
    Porównuje obliczoną emeryturę z:
    - Minimalną emeryturą (dolny próg)
    - Historycznymi średnimi ZUS
    - Maksymalnymi realistycznymi wartościami
    - Stopą zastąpienia (replacement rate)
    
    Args:
        pension_result: Wynik obliczeń emerytury (dict z monthly_pension i details)
        tables: Opcjonalne tabele z oficjalnymi statystykami ZUS/GUS
        
    Returns:
        Dict zawierający:
        - status (str): 'ok', 'uncertain', 'warning'
        - diagnostic (str): Opis statusu
        - details (dict): Szczegółowe informacje o sprawdzeniu
    """
    diagnostics = []
    status = "ok"
    details = {}
    
    # Pobierz kwotę emerytury
    monthly_pension = pension_result.get("monthly_pension")
    
    if monthly_pension is None:
        return {
            "status": "error",
            "diagnostic": "Brak wartości emerytury w wynikach",
            "details": {}
        }
    
    # Pobierz dodatkowe metryki jeśli dostępne
    pension_metrics = pension_result.get("details", {}).get("pension_metrics", {})
    replacement_rate = pension_metrics.get("replacement_rate_percent")
    final_salary = pension_metrics.get("final_salary_projection")
    
    # Statystyki ZUS (2024) - średnie emerytury
    AVERAGE_PENSION_MALE = 3500.0  # PLN (orientacyjnie)
    AVERAGE_PENSION_FEMALE = 2800.0  # PLN (orientacyjnie)
    MAX_REALISTIC_PENSION = 20000.0  # PLN (bardzo wysoka, ale możliwa)
    MIN_REALISTIC_PENSION = 1000.0  # PLN (poniżej minimum - problem)
    
    # Jeśli dostępne tabele oficjalne, użyj ich
    if tables and "average_pensions" in tables:
        AVERAGE_PENSION_MALE = tables["average_pensions"].get("male", AVERAGE_PENSION_MALE)
        AVERAGE_PENSION_FEMALE = tables["average_pensions"].get("female", AVERAGE_PENSION_FEMALE)
    
    # Sprawdzenie 1: Minimalna emerytura
    if monthly_pension < MIN_REALISTIC_PENSION:
        status = "uncertain"
        diagnostics.append(f"Emerytura poniżej minimalnego progu ({MIN_REALISTIC_PENSION} PLN)")
        details["below_minimum"] = True
    elif monthly_pension < MINIMUM_PENSION_2025:
        diagnostics.append(f"Emerytura poniżej minimum ({MINIMUM_PENSION_2025} PLN) - ZUS dopłaci do minimum")
        details["minimum_guarantee_applied"] = True
        if status == "ok":
            status = "warning"
    
    # Sprawdzenie 2: Maksymalna realistyczna emerytura
    if monthly_pension > MAX_REALISTIC_PENSION:
        status = "uncertain"
        diagnostics.append(f"Emerytura powyżej maksymalnego realnego progu ({MAX_REALISTIC_PENSION} PLN)")
        details["above_maximum"] = True
    
    # Sprawdzenie 3: Porównanie ze średnią
    user_gender = pension_result.get("details", {}).get("user_info", {}).get("gender")
    if user_gender:
        avg_pension = AVERAGE_PENSION_MALE if user_gender == "male" else AVERAGE_PENSION_FEMALE
        deviation = ((monthly_pension - avg_pension) / avg_pension) * 100
        
        details["deviation_from_average_percent"] = round(deviation, 2)
        details["average_pension_for_gender"] = avg_pension
        
        if abs(deviation) > 200:  # Więcej niż 200% odchylenia
            if status == "ok":
                status = "uncertain"
            diagnostics.append(f"Znaczne odchylenie od średniej ({deviation:+.1f}%)")
        elif abs(deviation) > 100:  # Więcej niż 100% odchylenia
            if status == "ok":
                status = "warning"
            diagnostics.append(f"Duże odchylenie od średniej ({deviation:+.1f}%)")
    
    # Sprawdzenie 4: Stopa zastąpienia (replacement rate)
    if replacement_rate is not None:
        details["replacement_rate"] = replacement_rate
        
        if replacement_rate < 20:
            if status == "ok":
                status = "uncertain"
            diagnostics.append(f"Bardzo niska stopa zastąpienia ({replacement_rate:.1f}%)")
        elif replacement_rate < 40:
            if status == "ok":
                status = "warning"
            diagnostics.append(f"Niska stopa zastąpienia ({replacement_rate:.1f}%) - rozważ dłuższą pracę")
        elif replacement_rate > 80:
            if status == "ok":
                status = "warning"
            diagnostics.append(f"Wysoka stopa zastąpienia ({replacement_rate:.1f}%) - sprawdź założenia")
    
    # Sprawdzenie 5: Relacja pensja-emerytura
    if final_salary is not None and monthly_pension is not None:
        if monthly_pension > final_salary:
            status = "uncertain"
            diagnostics.append("Emerytura wyższa niż ostatnia pensja - sprawdź obliczenia")
            details["pension_higher_than_salary"] = True
    
    # Sprawdzenie 6: Kapitał emerytalny
    pension_capital = pension_result.get("details", {}).get("pension_capital", {})
    total_capital = pension_capital.get("total_capital")
    
    if total_capital is not None:
        details["total_capital"] = total_capital
        
        if total_capital < 100000:
            if status == "ok":
                status = "warning"
            diagnostics.append("Niski kapitał emerytalny - rozważ dłuższą pracę lub wyższe składki")
        elif total_capital > 5000000:
            if status == "ok":
                status = "warning"
            diagnostics.append("Bardzo wysoki kapitał emerytalny - sprawdź założenia")
    
    # Przygotuj finalny komunikat diagnostyczny
    if not diagnostics:
        diagnostic_message = "Emerytura w normalnych granicach - obliczenia wyglądają poprawnie"
    else:
        diagnostic_message = "; ".join(diagnostics)
    
    result = {
        "status": status,
        "diagnostic": diagnostic_message,
        "details": details
    }
    
    logger.info(f"Sanity check emerytury: {status.upper()} - {diagnostic_message}")
    
    return result
