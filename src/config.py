"""Configuration settings for the pension calculator API"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
PERPLEXITY_API_KEY = os.environ.get("PPLX_API_KEY")
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_TEMPERATURE = 0.1

# Flask Configuration
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Pension System Constants
PENSION_CONTRIBUTION_RATE = 0.1952  # 19.52%
PENSION_CONTRIBUTION_MAIN_ACCOUNT = 0.1222  # 12.22% - konto główne
PENSION_CONTRIBUTION_SUB_ACCOUNT = 0.073   # 7.3% - subkonto
MINIMUM_PENSION_2025 = 1780.96  # PLN

# Retirement Ages
RETIREMENT_AGE = {
    "male": 65,
    "female": 60
}

# Average Life Expectancy (months after retirement) - GUS 2024
LIFE_EXPECTANCY_MONTHS = {
    "male": 210,      # ~17.5 years
    "female": 254.3   # ~21.2 years
}
