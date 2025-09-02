import math
import numpy as np

# Constants
API_BASE_URL = "https://devapi.revival365ai.com/data/chart"
LOGIN_URL = "https://devapi.revival365ai.com/admin/user/login"
PROFILE_URL = "https://devapi.revival365ai.com/user/getProfile"
#HEALTH_METRICS_URL = "http://13.232.23.208:8000/v1/health/metrics/daily"
EMAIL = "pythonapi@yopmail.com"  
PASSWORD = "Stixis@123"  
DEFAULT_BIAS_FACTOR = 1.20  # 20% underreporting
DEFAULT_EXP_CORRECTION = 1.00
UNCERTAINTY_FOOD = 0.25  # ±25%
UNCERTAINTY_WEARABLE = 0.20  # ±20%
UNCERTAINTY_RMR = 0.10  # ±10%
TEF_RATE = 0.10  # 10% of intake
CAL_PER_KG_FAT = 7700
CALIBRATION_WINDOW = 14

def calculate_confidence(missing_data_flags):
    """Calculate confidence score based on missing data."""
    conf = 1.0 - 0.1 * len(missing_data_flags)
    return max(0.5, conf)

def propagate_uncertainty(rmr, aee, tef, intake):
    """Propagate uncertainty for EB confidence range."""
    epsilon_out = math.sqrt((UNCERTAINTY_RMR * rmr)**2 + (UNCERTAINTY_WEARABLE * aee)**2 + (UNCERTAINTY_FOOD * tef)**2)
    epsilon_in = UNCERTAINTY_FOOD * intake
    return epsilon_in, epsilon_out

def parse_duration(duration_str):
    """Convert duration string (e.g., '3 H 6 Min') to hours."""
    if not duration_str:
        return 0.0
    hours, minutes = 0, 0
    parts = duration_str.lower().split()
    for i, part in enumerate(parts):
        if part.isdigit():
            if i + 1 < len(parts) and parts[i + 1].startswith('h'):
                hours = int(part)
            elif i + 1 < len(parts) and parts[i + 1].startswith('min'):
                minutes = int(part)
    return hours + minutes / 60.0