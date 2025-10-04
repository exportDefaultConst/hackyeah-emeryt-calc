# Polish Pension Calculator API

A minimalistic Flask API that calculates Polish pension projections using the Perplexity API and LangChain. Provides detailed retirement calculations based on ZUS (Polish Social Insurance) regulations.

## Features

- ✅ **Clean Architecture**: Separated concerns (config, models, calculator, API)
- ✅ **Comprehensive Logging**: Built-in logging at all levels
- ✅ **Perplexity API Integration**: Uses LangChain for AI-powered calculations
- ✅ **Polish ZUS Calculations**: Accurate pension projections based on Polish regulations
- ✅ **Docker Support**: Production-ready containerization with Gunicorn
- ✅ **Health Check Endpoint**: Monitor service status
- ✅ **Environment Configuration**: Easy setup with .env files

## Project Structure

```
hackyeah-emeryt-calc/
├── src/                   # Source code directory
│   ├── __init__.py       # Package initialization
│   ├── config.py         # Configuration and constants
│   ├── models.py         # Data models (UserData, Request, Result)
│   ├── calculator.py     # Pension calculation logic
│   ├── api.py            # Flask API endpoints
│   └── example_usage.py  # Example usage script
├── run.py                # Main runner script (start here!)
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
├── setup.ps1            # Automated setup script
├── .env.example         # Environment variables template
└── README.md            # This file
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

### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T13:25:00",
  "calculator_initialized": true
}
```

### `POST /calculate_pension`
Calculate pension projection

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
    "api_model": "llama-3.1-sonar-large-128k-online"
  }
}
```

## Usage Examples

### Using curl
```powershell
curl -X POST http://localhost:5000/calculate_pension `
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

### Using Python script
```powershell
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
