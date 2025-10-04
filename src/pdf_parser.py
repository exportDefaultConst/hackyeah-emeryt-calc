"""
PDF parsing utilities for official ZUS publications.
Extracts valorization indices, demographic projections, and statistical tables.
"""
import logging
import re
from typing import Dict, Any, Optional, List
from decimal import Decimal
import os

logger = logging.getLogger(__name__)

# Try to import PDF libraries (graceful degradation if not available)
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not available - PDF parsing will be limited")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available - PDF parsing will be limited")


def load_official_zus_tables(pdf_path: str) -> Dict[str, Any]:
    """
    Załaduj i sparsuj wskaźniki, prognozy i tabele z oficjalnego PDF ZUS.
    
    Parsuje dokument "Publikacja Fundusz Emerytalny 2023-2080.pdf" lub podobne
    publikacje ZUS zawierające:
    - Wskaźniki waloryzacji (historyczne i prognozowane)
    - Współczynniki rentowności subkonta
    - Tabele demograficzne (oczekiwana długość życia)
    - Prognozy makroekonomiczne
    
    Args:
        pdf_path: Ścieżka do pliku PDF (lokalnego lub URL)
        
    Returns:
        Dict zawierający:
        - valorization_indices: Słownik {rok: wskaźnik}
        - profitability_indices: Słownik {rok: wskaźnik} dla subkonta
        - life_expectancy_tables: Tabele dalszego trwania życia
        - economic_projections: Prognozy makroekonomiczne
        - metadata: Informacje o źródle i dacie publikacji
        
    Raises:
        FileNotFoundError: Jeśli plik nie istnieje
        ValueError: Jeśli parsowanie nie powiodło się
    """
    logger.info(f"Loading official ZUS tables from: {pdf_path}")
    
    # Sprawdź czy plik istnieje
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Wybierz metodę parsowania w zależności od dostępności bibliotek
    if PDFPLUMBER_AVAILABLE:
        return _parse_with_pdfplumber(pdf_path)
    elif PYPDF2_AVAILABLE:
        return _parse_with_pypdf2(pdf_path)
    else:
        logger.error("No PDF parsing library available")
        raise ImportError("Please install PyPDF2 or pdfplumber: pip install PyPDF2 pdfplumber")


def _parse_with_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """
    Parsuj PDF używając pdfplumber (preferowana metoda).
    
    pdfplumber oferuje lepsze wyodrębnianie tabel i struktury.
    """
    import pdfplumber
    
    result = {
        "valorization_indices": {},
        "profitability_indices": {},
        "life_expectancy_tables": {},
        "economic_projections": {},
        "metadata": {
            "source": pdf_path,
            "parser": "pdfplumber"
        }
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"PDF opened: {len(pdf.pages)} pages")
            result["metadata"]["pages"] = len(pdf.pages)
            
            # Iteruj po stronach i szukaj kluczowych danych
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                # Szukaj wskaźników waloryzacji
                valorization_matches = _extract_valorization_indices(text)
                if valorization_matches:
                    result["valorization_indices"].update(valorization_matches)
                    logger.debug(f"Found {len(valorization_matches)} valorization indices on page {page_num}")
                
                # Szukaj wskaźników rentowności
                profitability_matches = _extract_profitability_indices(text)
                if profitability_matches:
                    result["profitability_indices"].update(profitability_matches)
                    logger.debug(f"Found {len(profitability_matches)} profitability indices on page {page_num}")
                
                # Szukaj tabel demograficznych
                demographic_data = _extract_demographic_data(text)
                if demographic_data:
                    result["life_expectancy_tables"].update(demographic_data)
                
                # Wyodrębnij tabele jeśli dostępne
                tables = page.extract_tables()
                if tables:
                    parsed_tables = _parse_tables(tables, page_num)
                    if parsed_tables:
                        result["tables"] = result.get("tables", [])
                        result["tables"].extend(parsed_tables)
            
            logger.info(f"Parsing complete: {len(result['valorization_indices'])} valorization indices found")
            
    except Exception as e:
        logger.error(f"Error parsing PDF with pdfplumber: {e}", exc_info=True)
        raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    return result


def _parse_with_pypdf2(pdf_path: str) -> Dict[str, Any]:
    """
    Parsuj PDF używając PyPDF2 (fallback method).
    
    PyPDF2 jest prostszy ale mniej precyzyjny w wyodrębnianiu tabel.
    """
    import PyPDF2
    
    result = {
        "valorization_indices": {},
        "profitability_indices": {},
        "life_expectancy_tables": {},
        "economic_projections": {},
        "metadata": {
            "source": pdf_path,
            "parser": "PyPDF2"
        }
    }
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            logger.info(f"PDF opened with PyPDF2: {num_pages} pages")
            result["metadata"]["pages"] = num_pages
            
            # Iteruj po stronach
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Szukaj wskaźników waloryzacji
                valorization_matches = _extract_valorization_indices(text)
                if valorization_matches:
                    result["valorization_indices"].update(valorization_matches)
                
                # Szukaj wskaźników rentowności
                profitability_matches = _extract_profitability_indices(text)
                if profitability_matches:
                    result["profitability_indices"].update(profitability_matches)
                
                # Szukaj danych demograficznych
                demographic_data = _extract_demographic_data(text)
                if demographic_data:
                    result["life_expectancy_tables"].update(demographic_data)
            
            logger.info(f"Parsing complete: {len(result['valorization_indices'])} indices found")
            
    except Exception as e:
        logger.error(f"Error parsing PDF with PyPDF2: {e}", exc_info=True)
        raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    return result


def _extract_valorization_indices(text: str) -> Dict[int, float]:
    """
    Wyodrębnij wskaźniki waloryzacji z tekstu.
    
    Szuka wzorców typu:
    - "2025: 5.8%" lub "2025 - 5.8%"
    - "Waloryzacja 2025: 1.058"
    - Tabele z rokami i procentami
    """
    indices = {}
    
    # Wzorzec 1: Rok: XX.X% lub Rok - XX.X%
    pattern1 = r'(\d{4})[\s:−-]+(\d{1,2}[.,]\d{1,2})\s*%'
    matches1 = re.finditer(pattern1, text)
    
    for match in matches1:
        year = int(match.group(1))
        value = float(match.group(2).replace(',', '.'))
        
        # Walidacja zakresu
        if 2010 <= year <= 2100 and 0 < value < 50:  # Realistyczne wartości
            indices[year] = 1 + (value / 100)  # Konwersja % na wskaźnik
    
    # Wzorzec 2: Rok wskaźnik (np. "2025 1.058")
    pattern2 = r'(\d{4})[\s]+([01][.,]\d{3,4})'
    matches2 = re.finditer(pattern2, text)
    
    for match in matches2:
        year = int(match.group(1))
        value = float(match.group(2).replace(',', '.'))
        
        # Walidacja zakresu
        if 2010 <= year <= 2100 and 0.9 < value < 1.5:  # Wskaźnik w rozsądnym zakresie
            indices[year] = value
    
    return indices


def _extract_profitability_indices(text: str) -> Dict[int, float]:
    """
    Wyodrębnij wskaźniki rentowności subkonta.
    
    Szuka fraz związanych z rentownością OFE/subkonta.
    """
    indices = {}
    
    # Szukaj sekcji o rentowności
    if any(keyword in text.lower() for keyword in ['rentowność', 'subkonto', 'ofe', 'stopa zwrotu']):
        # Użyj podobnych wzorców jak dla waloryzacji
        pattern = r'(\d{4})[\s:−-]+(\d{1,2}[.,]\d{1,2})\s*%'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            year = int(match.group(1))
            value = float(match.group(2).replace(',', '.'))
            
            if 2010 <= year <= 2100 and 0 < value < 30:
                indices[year] = 1 + (value / 100)
    
    return indices


def _extract_demographic_data(text: str) -> Dict[str, Any]:
    """
    Wyodrębnij dane demograficzne (oczekiwana długość życia).
    
    Szuka tabel z danymi GUS o dalszym trwaniu życia.
    """
    demographic = {}
    
    # Szukaj wzorców dla oczekiwanej długości życia
    patterns = [
        r'mężczyźni[\s:]+(\d{2,3})[.,](\d{1,2})\s*(?:lat|roku|miesięcy)',
        r'kobiety[\s:]+(\d{2,3})[.,](\d{1,2})\s*(?:lat|roku|miesięcy)',
        r'wiek\s+65[\s:]+(\d{2,3})[.,](\d{1,2})',
        r'wiek\s+60[\s:]+(\d{2,3})[.,](\d{1,2})'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            value = float(f"{match.group(1)}.{match.group(2)}")
            if 10 < value < 40:  # Realistyczne lata życia na emeryturze
                if 'mężczyźni' in pattern or 'wiek\s+65' in pattern:
                    demographic['male_life_expectancy_years'] = value
                elif 'kobiety' in pattern or 'wiek\s+60' in pattern:
                    demographic['female_life_expectancy_years'] = value
    
    return demographic


def _parse_tables(tables: List, page_num: int) -> List[Dict[str, Any]]:
    """
    Parsuj wyodrębnione tabele z PDF.
    
    Args:
        tables: Lista tabel z pdfplumber
        page_num: Numer strony
        
    Returns:
        Lista słowników z danymi tabelarycznymi
    """
    parsed = []
    
    for table_idx, table in enumerate(tables):
        if not table or len(table) < 2:
            continue
        
        # Nagłówki w pierwszym wierszu
        headers = table[0]
        
        # Dane w pozostałych wierszach
        table_data = {
            "page": page_num,
            "table_index": table_idx,
            "headers": headers,
            "rows": table[1:]
        }
        
        parsed.append(table_data)
    
    return parsed


def get_mock_zus_tables() -> Dict[str, Any]:
    """
    Zwróć przykładowe tabele ZUS jeśli PDF nie jest dostępny.
    
    Zawiera dane historyczne (2015-2024) i prognozy (2025-2080)
    oparte na publikacjach ZUS i GUS.
    
    Returns:
        Dict z przykładowymi danymi w formacie zgodnym z load_official_zus_tables
    """
    logger.info("Returning mock ZUS tables (fallback data)")
    
    return {
        "valorization_indices": {
            # Dane historyczne (rzeczywiste)
            2015: 1.0407,
            2016: 1.0039,
            2017: 1.0464,
            2018: 1.0529,
            2019: 1.0643,
            2020: 1.0486,
            2021: 1.0524,
            2022: 1.1086,
            2023: 1.1439,
            2024: 1.1266,
            # Prognozy (na podstawie publikacji ZUS)
            2025: 1.0580,
            2026: 1.0520,
            2027: 1.0480,
            2028: 1.0450,
            2029: 1.0430,
            2030: 1.0420,
            2031: 1.0410,
            2032: 1.0400,
            2033: 1.0400,
            2034: 1.0400,
            2035: 1.0400,
            # Długoterminowe (2036-2080) - stabilizacja na 4%
            **{year: 1.0400 for year in range(2036, 2081)}
        },
        "profitability_indices": {
            # Rentowność subkonta (zazwyczaj niższa)
            2024: 1.0350,
            2025: 1.0380,
            2026: 1.0360,
            2027: 1.0350,
            2028: 1.0340,
            2029: 1.0330,
            2030: 1.0330,
            # Długoterminowe
            **{year: 1.0350 for year in range(2031, 2081)}
        },
        "life_expectancy_tables": {
            "male_life_expectancy_years": 17.5,
            "female_life_expectancy_years": 21.2,
            "male_life_expectancy_months": 210,
            "female_life_expectancy_months": 254.3
        },
        "economic_projections": {
            "gdp_growth_rate": 3.0,  # %
            "inflation_target": 2.5,  # %
            "wage_growth_rate": 3.5  # %
        },
        "average_pensions": {
            "male": 3500.0,  # PLN
            "female": 2800.0  # PLN
        },
        "metadata": {
            "source": "mock_data",
            "description": "Historical ZUS data (2015-2024) + projections based on ZUS publications",
            "data_sources": [
                "ZUS Annual Reports 2015-2024",
                "Fundusz Emerytalny 2023-2080 (estimates)",
                "GUS Demographic Tables 2024"
            ],
            "last_updated": "2024-03-01"
        }
    }


def validate_loaded_tables(tables: Dict[str, Any]) -> bool:
    """
    Zwaliduj załadowane tabele ZUS.
    
    Sprawdza czy struktura danych jest poprawna i kompletna.
    
    Args:
        tables: Słownik z tabelami ZUS
        
    Returns:
        True jeśli tabele są poprawne, False w przeciwnym razie
    """
    required_keys = ["valorization_indices", "metadata"]
    
    # Sprawdź czy są wszystkie wymagane klucze
    for key in required_keys:
        if key not in tables:
            logger.error(f"Missing required key in ZUS tables: {key}")
            return False
    
    # Sprawdź czy są jakieś wskaźniki waloryzacji
    if not tables["valorization_indices"]:
        logger.error("No valorization indices found in tables")
        return False
    
    # Sprawdź zakres dat
    years = list(tables["valorization_indices"].keys())
    if not years:
        return False
    
    min_year = min(years)
    max_year = max(years)
    
    if min_year > 2020 or max_year < 2025:
        logger.warning(f"Unusual year range in tables: {min_year}-{max_year}")
    
    logger.info(f"Tables validated: {len(years)} years ({min_year}-{max_year})")
    return True
