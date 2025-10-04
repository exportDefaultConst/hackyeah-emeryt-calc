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
MINIMUM_PENSION_2025 = 1780.96  # PLN

# Retirement Ages
RETIREMENT_AGE = {
    "male": 65,
    "female": 60
}

# Average Life Expectancy (months after retirement)
LIFE_EXPECTANCY_MONTHS = {
    "male": 210,
    "female": 254.3
}
