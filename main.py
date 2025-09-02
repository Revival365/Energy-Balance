import asyncio
import json
from datetime import datetime, timedelta
from fetching import fetch_user_profile, fetch_all_data_for_week_async, fetch_health_metrics
from computations import compute_daily_metrics, calibrate_factors
from interpretations import interpret_results
from utils import CALIBRATION_WINDOW


def load_macros_from_json():
    try:
        with open("values.json", "r") as f:
            data = json.load(f)
        
        # FIX: Access first array element
        if len(data) > 0 and "meals" in data[0] and len(data[0]["meals"]) > 0:
            meal = data[0]["meals"][0]
            return {
                "protein_g": meal.get("protein_g", 0),  # Correct key
                "carbs_g": meal.get("carbs_g", 0),      # Correct key
                "fat_g": meal.get("fat_g", 0)           # Correct key
            }
        return {}
    except Exception as e:
        print(f"Error loading macros from JSON: {str(e)}")
        return {}




import json
def format_output(metrics, macro_goals=None):
    intake = metrics.get("intake", {})
    expenditure = metrics.get("expenditure", {})

    # Load overrides from JSON
    macros_from_json = load_macros_from_json()
    macros = intake.get("macros", {})

    logged_kcal = intake.get("logged_kcal", 0)
    bias_adjusted_kcal = intake.get("bias_adjusted_kcal", logged_kcal)
    tee = expenditure.get("TEE_kcal", 0)
    rmr = expenditure.get("RMR_kcal", 0)

    todayMetrics = {
        "currentIntake": logged_kcal,
        "currentBurn": tee,
        "projectedIntake": bias_adjusted_kcal,
        "projectedBurn": tee,
        "currentDeficit": logged_kcal - tee,
        "projectedDeficit": bias_adjusted_kcal - tee
    }

    defaults = {
        "protein": {"goal": 140, "target": 117},
        "carbs": {"goal": 75, "target": 50},
        "fats": {"goal": 52, "target": 40}
    }

    # Get actual intake values
    actual_intake = {
        "protein": macros_from_json.get("protein_g", macros.get("protein_g", 0)),
        "carbs": macros_from_json.get("carbs_g", macros.get("carbs_g", 0)),
        "fats": macros_from_json.get("fat_g", macros.get("fat_g", 0))
    }

    # Get target values from profile or use defaults
    target_goals = {
        "protein": macro_goals.get("protein", defaults["protein"]) if macro_goals else defaults["protein"],
        "carbs": macro_goals.get("carbs", defaults["carbs"]) if macro_goals else defaults["carbs"],
        "fats": macro_goals.get("fat", defaults["fats"]) if macro_goals else defaults["fats"]
    }

    # Create target and intake sections
    target_intake_output = {
        "target": target_goals,
        "intake": actual_intake
    }

    # dailyFlow: simple placeholder distribution
    daily_data = [
        {"hour": h, "intake": 0, "burn": round(rmr/24)} for h in range(25)
    ]

    return {
        "todayMetrics": todayMetrics, 
        "macros": target_intake_output, 
        "dailyFlow": {"data": daily_data}
    }

async def main(user_id, date_str):
    """Compute energy balance and return JSON output with interpretation."""
    # Fetch profile
    profile_resp = fetch_user_profile(user_id)
    if "error" in profile_resp:
        return {"error": f"Profile fetch error:{profile_resp['error']}"}
    profile = profile_resp.get("content", {}).get("user", {"weight_kg": 70, "height_cm": 170, "age": 30, "gender": "male"})

    # Manual weight override
    profile_weight = profile.get("weight") or profile.get("weight_kg")

    if profile_weight:
        current_weight = profile_weight
    else:
        try:
            current_weight = float(input("Enter current weight (kg): ").strip())
        except ValueError:
            print("❌ No valid weight found in profile or input. Exiting.")
            sys.exit(1)

    # Fetch band data for current day
    start_date = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=CALIBRATION_WINDOW-1)).strftime("%Y-%m-%d")
    band_data_weekly = await fetch_all_data_for_week_async(user_id, start_date, CALIBRATION_WINDOW)
    band_data = {
        "cgm": band_data_weekly["cgm"][-1] if band_data_weekly["cgm"] else [],
        "hr": band_data_weekly["hr"][-1] if band_data_weekly["hr"] else [],
        "hrv": band_data_weekly["hrv"][-1] if band_data_weekly["hrv"] else [],
        "activity": band_data_weekly["activity"][-1] if band_data_weekly["activity"] else [],
        "sleep": band_data_weekly["sleep"][-1] if band_data_weekly["sleep"] else [],
        "stress": band_data_weekly["stress"][-1] if band_data_weekly["stress"] else []
    }

    # Fetch health metrics
    health_metrics = fetch_health_metrics(user_id, date_str)

    # Placeholder for historical weights
    historical_weights = {date_str: current_weight if current_weight else profile.get("weight_kg", 70)}

    # Calibration
    bias_factor, exp_correction = calibrate_factors([], list(historical_weights.values()))

    # Compute metrics
    results = compute_daily_metrics(date_str, profile, band_data, health_metrics, historical_weights, current_weight, bias_factor, exp_correction)

    # Format into your schema - FIXED: Use the updated format_output function
    final_output = format_output(results, macro_goals=profile.get("macro_goals", {}))

    return final_output


import sys

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <USER_ID> <DATE>")
        sys.exit(1)

    USER_ID = int(sys.argv[1])   # always from CLI
    DATE_STR = sys.argv[2]       # always from CLI

    result = asyncio.run(main(USER_ID, DATE_STR))
    print(json.dumps(result, indent=2))

    with open("energy_balance_output.json", "w") as f:
        json.dump(result, f, indent=2)
