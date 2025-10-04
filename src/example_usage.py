"""Example usage of the pension calculator"""
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.calculator import PensionCalculator
from src.models import PensionCalculationRequest

# Set your API key (or use environment variable)
# os.environ["PPLX_API_KEY"] = "your_api_key_here"

def main():
    """Run example pension calculation"""
    
    # Example user data
    example_user_data = {
        "age": 35,
        "gender": "male",
        "gross_salary": 8000.0,
        "work_start_year": 2010,
        "work_end_year": 2045,
        "industry": "IT",
        "position": "Senior Developer",
        "company": "Tech Company",
        "zus_account_balance": 50000.0,
        "zus_subaccount_balance": 15000.0,
        "sick_leave_days_per_year": 5.0
    }

    # Create request
    request = PensionCalculationRequest(
        user_data=example_user_data,
        prompt=""  # Will use default prompt generation
    )

    # Initialize calculator (requires PPLX_API_KEY environment variable)
    try:
        print("Initializing calculator...")
        calculator = PensionCalculator()

        print("Processing pension calculation...")
        result = calculator.process_request(request)

        print("\n" + "="*60)
        print("PENSION CALCULATION RESULT")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("="*60 + "\n")

    except ValueError as e:
        print(f"Error: {e}")
        print("Please set PPLX_API_KEY environment variable with your Perplexity API key")


if __name__ == "__main__":
    main()
