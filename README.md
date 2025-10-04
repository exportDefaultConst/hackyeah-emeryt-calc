# Polish Pension Calculator API

A minimalistic Flask API that calculates Polish pension projections using the Perplexity API and LangChain, **plus a fully local calculation engine** based on official ZUS statistics and formulas. Provides detailed retirement calculations based on ZUS (Polish Social Insurance) regulations.

## Features

- ✅ **Clean Architecture**: Separated concerns (config, models, calculator, API)
- ✅ **Comprehensive Logging**: Built-in logging at all levels
- ✅ **Perplexity API Integration**: Uses LangChain for AI-powered calculations
- ✅ **Local ZUS Calculator**: Full pension calculation without external APIs
- ✅ **Official ZUS Statistics**: Uses real valorization indices and demographic data
- ✅ **Input Validation**: Comprehensive user data validation with detailed error messages
- ✅ **Sanity Checking**: Automatic validation of calculation results against realistic bounds
- ✅ **Standardized Results**: Unified JSON schema for all calculation endpoints
- ✅ **PDF Parsing**: Load official ZUS tables from PDF documents
- ✅ **Polish ZUS Calculations**: Accurate pension projections based on Polish regulations
- ✅ **Docker Support**: Production-ready containerization with Gunicorn
- ✅ **Health Check Endpoint**: Monitor service status
- ✅ **Environment Configuration**: Easy setup with .env files
- ✅ **Full Audit Trail**: Detailed calculation logs for transparency
- 🌟 **AI-Powered FAQ**: Personalized questions & answers based on user's situation
- 🌟 **Smart Term Explainer**: AI explains complex pension terminology in simple language

## Project Structure

```
hackyeah-emeryt-calc/
├── src/                          # Source code directory
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration and constants
│   ├── models.py                # Data models (UserData, Request, Result)
│   ├── calculator.py            # Pension calculation logic (AI + Local)
│   ├── validation.py            # Input validation utilities
│   ├── result_formatter.py      # Result standardization
│   ├── pdf_parser.py            # PDF parsing for ZUS documents
│   ├── api.py                   # Flask API endpoints
│   └── example_usage.py         # Example usage script
├── run.py                       # Main runner script (start here!)
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose setup
├── test_local_calculation.py    # Test local calculation function
├── test_local_api.py            # Test local calculation API
├── PENSION_CALCULATION_DOCS.md  # Detailed local calculation docs
├── DATA_SOURCES.md              # Official data sources reference
├── QUICK_START.md               # 5-minute quick start guide
├── IMPLEMENTATION_SUMMARY.md    # Implementation details
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

### Prerequisites
- Python 3.11+ 
- Perplexity API key ([Get one here](https://www.perplexity.ai/settings/api))

### Local Setup

1. **Clone the repository**
   ```powershell
   git clone <repository-url>
   cd hackyeah-emeryt-calc
   ```

2. **Create virtual environment** (recommended)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```powershell
   cp .env.example .env
   # Edit .env and add your PPLX_API_KEY
   ```

5. **Run the API**
   ```powershell
   python run.py
   ```

The API will be available at `http://localhost:5000`

## API Endpoints

### `GET /api/health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T13:25:00",
  "calculator_initialized": true
}
```

### `POST /api/calculate_pension`
Calculate pension projection using Perplexity AI

**Request:**
```json
{
  "user_data": {
    "age": 35,
    "gender": "male",
    "gross_salary": 8000.0,
    "work_start_year": 2010,
    "work_end_year": 2045,
    "industry": "IT",
    "position": "Senior Developer",
    "zus_account_balance": 50000.0,
    "zus_subaccount_balance": 15000.0,
    "sick_leave_days_per_year": 5.0
  }
}
```

**Response:**
```json
{
  "current_pension_projection": 3500.00,
  "indexed_pension_projection": 2800.00,
  "replacement_rate": 65.5,
  "years_to_work_longer": null,
  "sick_leave_impact": -150.00,
  "salary_variability_impact": 200.00,
  "minimum_pension_gap": null,
  "calculation_details": { ... },
  "metadata": {
    "calculation_date": "2025-10-04T13:25:00",
    "user_age": 35,
    "user_gender": "male",
    "current_salary": 8000.0,
    "api_model": "sonar-pro"
  }
}
```

### `POST /api/calculate_pension_local` ⭐ NEW
Calculate pension using local ZUS statistics (no AI API required)

**Features:**
- ✅ Uses official ZUS valorization indices (2015-2080)
- ✅ GUS demographic tables for life expectancy
- ✅ Full audit trail with formulas and coefficients
- ✅ No external API calls - completely local
- ✅ Precise Decimal arithmetic for accuracy

**Request:**
```json
{
  "user_data": {
    "age": 35,
    "gender": "male",
    "gross_salary": 8000.0,
    "work_start_year": 2010,
    "work_end_year": 2054,
    "zus_account_balance": 50000.0,
    "zus_subaccount_balance": 20000.0,
    "sick_leave_days_per_year": 10
  },
  "official_tables": {
    "valorization_indices": {
      "2024": 1.1266,
      "2025": 1.0580,
      "2026": 1.0520
    },
    "profitability_indices": {
      "2024": 1.0350,
      "2025": 1.0380
    }
  }
}
```

**Response:**
```json
{
  "monthly_pension": 4567.89,
  "details": {
    "calculation_date": "2025-10-04T...",
    "user_info": {
      "age": 35,
      "gender": "male",
      "retirement_age": 65,
      "total_work_years": 44,
      "remaining_years": 29
    },
    "pension_capital": {
      "main_account": 456789.12,
      "sub_account": 234567.89,
      "total_capital": 691357.01,
      "life_expectancy_months": 210
    },
    "formulas": {
      "contribution_formula": "Składka = Wynagrodzenie brutto × 19.52%",
      "pension_formula": "Emerytura miesięczna = Kapitał emerytalny / Średnie dalsze trwanie życia (miesiące)"
    },
    "coefficients": {
      "contribution_rate_total": 0.1952,
      "contribution_rate_main": 0.1222,
      "contribution_rate_sub": 0.073,
      "salary_growth_rate_annual": 1.035,
      "minimum_pension_2025": 1780.96
    },
    "pension_metrics": {
      "monthly_pension_gross": 4567.89,
      "final_salary_projection": 12345.67,
      "replacement_rate_percent": 37.02,
      "years_to_work_longer": 5,
      "sick_leave_impact_monthly": -123.45
    },
    "audit_trail": {
      "yearly_contributions": [...],
      "valorization_log": [...]
    },
    "data_sources": {
      "valorization_indices_source": "ZUS historical data + projections",
      "life_expectancy_source": "GUS 2024"
    },
    "assumptions": [...]
  }
}
```

📖 **See [PENSION_CALCULATION_DOCS.md](PENSION_CALCULATION_DOCS.md) for complete documentation**

### `POST /validate_user_data` 🆕
Validate user data without performing calculation

**Request:**
```json
{
  "user_data": {
    "age": 35,
    "gender": "male",
    "gross_salary": 8000.0,
    "work_start_year": 2010
  }
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Rozpoczęcie pracy przed 18 rokiem życia - sprawdź dane"
  ]
}
```

### `GET /zus_tables` 🆕
Get default ZUS tables with historical and projected data

**Response:**
```json
{
  "valorization_indices": {
    "2024": 1.1266,
    "2025": 1.0580,
    ...
  },
  "profitability_indices": { ... },
  "life_expectancy_tables": { ... },
  "economic_projections": { ... },
  "average_pensions": {
    "male": 3500.0,
    "female": 2800.0
  },
  "metadata": { ... }
}
```

---

## 🌟 WOW FEATURES - AI-Powered Assistant

### `POST /api/faq` 🎯 **WOW Feature #1**
Generate personalized FAQ based on user's pension calculation

**What makes this special:**
- AI analyzes user's specific situation (age, salary, industry, pension amount)
- Generates 5-7 most relevant questions they're likely to ask
- Provides concrete, personalized answers
- Categories: comparisons, scenarios, optimizations, legal

**Request:**
```json
{
  "user_data": {
    "age": 35,
    "gender": "male",
    "gross_salary": 8000.0,
    "work_start_year": 2010,
    "industry": "IT",
    "position": "Senior Developer"
  },
  "calculation_result": {
    "monthly_pension": 4567.89,
    "replacement_rate": 37.5,
    "years_to_work_longer": 5
  }
}
```

**Response:**
```json
{
  "faq": [
    {
      "question": "Ile dostają emeryci w mojej branży?",
      "answer": "W branży IT średnia emerytura wynosi około 3,800 PLN. Twoja prognozowana emerytura (4,567 PLN) jest o 20% wyższa od średniej branżowej, co wynika z wysokich zarobków i regularnych składek.",
      "relevance": "high",
      "category": "comparison"
    },
    {
      "question": "Co jeśli nie będę pracować przez 5 lat?",
      "answer": "5-letnia przerwa w pracy zmniejszy Twoją emeryturę o około 850-950 PLN miesięcznie. To wynika z braku składek oraz utraty waloryzacji zgromadzonego kapitału.",
      "relevance": "high",
      "category": "scenario"
    },
    {
      "question": "Czy mogę liczyć na wcześniejszą emeryturę?",
      "answer": "Wcześniejsza emerytura (przed 65. rokiem życia) jest możliwa, ale wiąże się z trwałym obniżeniem świadczenia. Przy przejściu na emeryturę w wieku 60 lat, Twoja emerytura byłaby o ~30% niższa (około 3,200 PLN).",
      "relevance": "medium",
      "category": "legal"
    }
  ],
  "metadata": {
    "generated_at": "2025-10-04T14:30:00",
    "user_age": 35,
    "user_industry": "IT",
    "total_questions": 7
  }
}
```

### `POST /api/explain_terms` 📚 **WOW Feature #2**
AI-powered pension dictionary - explains complex terms in simple language

**What makes this special:**
- Explains difficult pension concepts in easy-to-understand language
- Personalized examples based on user's data
- Simple + detailed explanations for different knowledge levels
- Shows related terms to build understanding

**Request:**
```json
{
  "terms": [
    "kapitał początkowy",
    "waloryzacja",
    "współczynnik zastąpienia"
  ],
  "user_data": {
    "age": 35,
    "gross_salary": 8000.0
  },
  "calculation_result": {
    "monthly_pension": 4567.89,
    "replacement_rate": 37.5
  }
}
```

**Response:**
```json
{
  "explanations": [
    {
      "term": "kapitał początkowy",
      "simple_explanation": "To pieniądze zgromadzone na Twoim koncie ZUS przed 1999 rokiem, kiedy zmienił się system emerytalny. Jeśli pracowałeś przed tą datą, ZUS przeliczył Twoje lata pracy na kapitał startowy.",
      "detailed_explanation": "Kapitał początkowy został ustalony dla osób, które pracowały przed reformą emerytalną z 1999 roku. ZUS obliczył wartość składek i uprawnień emerytalnych według starego systemu i przekształcił je w kwotę, która stanowi fundament Twojego konta emerytalnego.",
      "example": "W Twoim przypadku, jeśli rozpocząłeś pracę w 2010 roku, nie masz kapitału początkowego, ponieważ zacząłeś pracować już w nowym systemie. Wszystkie Twoje składki są liczone według aktualnych zasad.",
      "related_terms": ["kapitał emerytalny", "składki emerytalne", "reforma 1999"],
      "importance": "medium"
    },
    {
      "term": "waloryzacja",
      "simple_explanation": "To coroczne 'podwyższenie' pieniędzy zgromadzonych na Twoim koncie emerytalnym. Dzięki temu Twoje oszczędności emerytalne rosną nie tylko przez wpłacanie składek, ale też przez ich zwiększanie zgodnie ze wzrostem wynagrodzeń w Polsce.",
      "detailed_explanation": "Waloryzacja składek emerytalnych jest mechanizmem dostosowania wartości zgromadzonego kapitału do wzrostu przeciętnego wynagrodzenia. Wskaźnik waloryzacji ogłasza GUS i wynosi on średnio 3-5% rocznie. Dzięki temu pieniądze odłożone 20 lat temu zachowują realną wartość.",
      "example": "Jeśli wpłaciłeś 10,000 PLN składek w 2015 roku, to dzięki waloryzacji około 5% rocznie, dziś te składki są warte około 14,000 PLN. W Twoim przypadku przy wynagrodzeniu 8,000 PLN wpłacasz rocznie około 18,739 PLN składek, które będą corocznie waloryzowane aż do emerytury.",
      "related_terms": ["wskaźnik waloryzacji", "średnie wynagrodzenie", "inflacja"],
      "importance": "high"
    },
    {
      "term": "współczynnik zastąpienia",
      "simple_explanation": "To procent pokazujący, ile z ostatniej pensji będziesz dostawał jako emeryturę. Jeśli zarabiasz 8,000 PLN i współczynnik wynosi 40%, Twoja emerytura będzie około 3,200 PLN.",
      "detailed_explanation": "Współczynnik zastąpienia (replacement rate) określa, jaka część ostatniego wynagrodzenia przed emeryturą stanowi wysokość świadczenia emerytalnego. Jest to kluczowy wskaźnik adekwatności systemu emerytalnego - im wyższy, tym lepiej emerytura zabezpiecza dotychczasowy standard życia.",
      "example": "Twoja prognozowana emerytura to 4,567 PLN przy obecnym wynagrodzeniu 8,000 PLN, co daje współczynnik zastąpienia 57%. To dobry wynik, blisko zalecanego przez ZUS poziomu 60%, który pozwala utrzymać podobny standard życia.",
      "related_terms": ["stopa zastąpienia", "adekwatność emerytury", "standard życia"],
      "importance": "high"
    }
  ],
  "metadata": {
    "generated_at": "2025-10-04T14:35:00",
    "terms_count": 3,
    "terms_requested": ["kapitał początkowy", "waloryzacja", "współczynnik zastąpienia"],
    "personalized": true
  }
}
```


## Usage Examples

### Using curl - AI-powered calculation
```powershell
curl -X POST http://localhost:5000/api/calculate_pension `
  -H "Content-Type: application/json" `
  -d '{
    "user_data": {
      "age": 30,
      "gender": "female",
      "gross_salary": 7000.0,
      "work_start_year": 2015
    }
  }'
```

### Using curl - Local calculation
```powershell
curl -X POST http://localhost:5000/api/calculate_pension_local `
  -H "Content-Type: application/json" `
  -d '{
    "user_data": {
      "age": 35,
      "gender": "male",
      "gross_salary": 8000.0,
      "work_start_year": 2010
    }
  }'
```

### Using Python - Direct function call
```python
from src.models import UserData
from src.calculator import calculate_pension_locally

user_data = UserData(
    age=35,
    gender="male",
    gross_salary=8000.0,
    work_start_year=2010
)

result = calculate_pension_locally(user_data)
print(f"Monthly pension: {result['monthly_pension']:.2f} PLN")
print(f"Replacement rate: {result['details']['pension_metrics']['replacement_rate_percent']:.2f}%")
```

### Running test scripts
```powershell
# Test local calculation function directly
python test_local_calculation.py

# Test local calculation via API (requires running server)
python run.py  # In one terminal
python test_local_api.py  # In another terminal

# Test AI-powered calculation
python src/example_usage.py
```

## Data Structure

### Required Fields (Obowiązkowe pola)
- `age`: Current age
- `gender`: "male" or "female" 
- `gross_salary`: Monthly gross salary in PLN
- `work_start_year`: Year when work began
- `work_end_year`: Planned retirement year (defaults to legal retirement age)

### Optional Fields (Opcjonalne pola)
- `industry`: Industry/sector
- `position`: Job position
- `company`: Company name
- `zus_account_balance`: Accumulated funds in ZUS account
- `zus_subaccount_balance`: Accumulated funds in ZUS subaccount  
- `sick_leave_days_per_year`: Average annual sick leave days

## API Response Format

```json
{
  "current_pension_projection": 3500.00,
  "indexed_pension_projection": 2800.00,
  "replacement_rate": 65.5,
  "years_to_work_longer": null,
  "sick_leave_impact": -150.00,
  "salary_variability_impact": 200.00,
  "minimum_pension_gap": null,
  "calculation_details": {
    "contribution_rate": "19.52%",
    "total_contributions_estimated": 850000.00,
    "valorization_rate": "3.5%",
    "life_expectancy_months": 210,
    "assumptions": ["Current ZUS regulations", "3.5% valorization", "2.5% inflation"]
  },
  "metadata": {
    "calculation_date": "2025-10-04T13:25:00",
    "user_age": 23,
    "user_gender": "male",
    "current_salary": 12000.0,
    "api_model": "llama-3.1-sonar-large-128k-online"
  }
}
```

## Docker Deployment

### Build and Run
```powershell
# Build image
docker build -t pension-calculator .

# Run container
docker run -p 5000:5000 -e PPLX_API_KEY=your_key_here pension-calculator
```

### Using Docker Compose (create docker-compose.yml)
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - PPLX_API_KEY=${PPLX_API_KEY}
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

Run with:
```powershell
docker-compose up -d
```

## ZUS Pension Calculation Background

### Polish Pension System Overview
The Polish pension system operates on a defined contribution basis where:

- **Contribution Rate**: 19.52% of gross salary (split between employee and employer)
- **Valorization**: Annual adjustment of accumulated contributions (typically 3-4%)
- **Life Expectancy Tables**: GUS publishes annual tables used for pension calculations
- **Minimum Pension**: Guaranteed minimum amount (1,780.96 PLN in 2025)

### Calculation Formula
```
Pension = Total Contributions / Average Life Expectancy (in months)
```

Where:
- Total Contributions = Valorized contributions + Initial capital + Subaccount funds
- Average Life Expectancy = GUS tables based on gender and retirement age

### Key Factors Affecting Pension Amount
1. **Salary Level**: Higher salaries = higher contributions = higher pension
2. **Years Worked**: Longer career = more contributions
3. **Retirement Age**: Later retirement = fewer expected payout months = higher monthly pension
4. **Sick Leaves**: Unpaid leaves reduce contribution periods
5. **Salary Growth**: Career progression increases contributions over time

## Error Handling

The application includes comprehensive error handling:

- **API Key Validation**: Checks for valid Perplexity API key
- **Data Validation**: Validates all user input parameters
- **JSON Parsing**: Handles malformed API responses gracefully
- **Logging**: Detailed logging for troubleshooting
- **Fallback Responses**: Provides meaningful error messages

## Logging

The application includes comprehensive logging at multiple levels:

- **INFO**: General application flow and important events
- **DEBUG**: Detailed calculation parameters and internal state
- **WARNING**: Potential issues (missing optional data, etc.)
- **ERROR**: Errors with full stack traces

Configure log level in `.env`:
```
LOG_LEVEL=DEBUG  # For development
LOG_LEVEL=INFO   # For production
```

Logs include:
- Request processing details
- API call timing
- Calculation parameters
- Error traces with context

## Configuration

All configuration is managed in `config.py`:

- **Perplexity API**: Model selection, temperature, API key
- **Flask Settings**: Host, port, debug mode
- **Logging**: Format and level
- **ZUS Constants**: Contribution rates, retirement ages, life expectancy
- **Pension Parameters**: Minimum pension, calculation factors

Override defaults using environment variables in `.env`

## Support and Documentation

### API Documentation
- [Perplexity API Docs](https://docs.perplexity.ai)
- [LangChain Perplexity Integration](https://python.langchain.com/docs/integrations/chat/perplexity/)

### ZUS Resources
- [ZUS Pension Calculator](https://www.zus.pl/swiadczenia/emerytury/kalkulatory-emerytalne)
- [Polish Pension System Overview](https://www.zus.pl/swiadczenia/emerytury)

### Troubleshooting
Common issues and solutions:

**"No API key provided"**
- Set PPLX_API_KEY environment variable
- Verify API key is valid and active

**"JSON parsing error"**
- Check Perplexity API response format
- Verify prompt generates valid JSON response

**"Invalid user data"**
- Ensure all required fields are provided
- Check data types match expected format

## License

This project is provided as-is for educational and development purposes. Please ensure compliance with Perplexity API terms of service and Polish data protection regulations when using in production.

## Contributing

Contributions welcome! Areas for improvement:
- Integration with official ZUS APIs
- Enhanced pension calculation algorithms
- Additional language support
- Performance optimizations
- Extended test coverage

---

*Created for Polish pension calculation automation using Perplexity AI and LangChain.*
