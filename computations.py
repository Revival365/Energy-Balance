import numpy as np
from utils import calculate_confidence, propagate_uncertainty, DEFAULT_BIAS_FACTOR, DEFAULT_EXP_CORRECTION, TEF_RATE, CAL_PER_KG_FAT, CALIBRATION_WINDOW

def calculate_rmr_mifflin(weight_kg, height_cm, age, gender):
    """Calculate RMR using Mifflin-St Jeor equation."""
    s = 5 if gender.lower() == "male" else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s

def refine_rmr_with_hr(rmr_baseline, resting_hr, hrv):
    """Refine RMR using resting HR and HRV."""
    factor = 1 + (60 - resting_hr) / 100  # Lower HR increases efficiency
    if hrv and hrv > 50:
        factor += 0.05  # High HRV slight boost
    return rmr_baseline * factor

def calculate_tef(intake_kcal):
    """Calculate Thermic Effect of Food (10% of intake)."""
    return TEF_RATE * intake_kcal

def calibrate_factors(historical_ebs, observed_weight_changes):
    """Placeholder for Bayesian calibration (defaults used)."""
    return DEFAULT_BIAS_FACTOR, DEFAULT_EXP_CORRECTION

def compute_daily_metrics(date_str, profile, band_data, health_metrics, historical_weights=None, current_weight=None, bias_factor=DEFAULT_BIAS_FACTOR, exp_correction=DEFAULT_EXP_CORRECTION):
    """Compute daily energy balance metrics."""
    # Extract profile
    weight_kg = current_weight if current_weight else profile.get("weight_kg", 70)
    age = profile.get("age", 30)
    height_cm = profile.get("height_cm", 170)
    gender = profile.get("gender", "male")

        # Intake from health metrics (safe lookup)
    def safe_metric_lookup(metrics, target):
        for m in metrics:
            # Case 1: flat metric dict
            if "metric" in m:
                if m["metric"] == target:
                    return m.get("value", 0)

            # Case 2: nested "metrics" dict
            elif "metrics" in m:
                inner = m["metrics"].get(target)
                if inner:
                    return inner.get("value", 0)

            else:
                print("⚠️ Metric missing in health_metrics entry:", m)

        return 0

    intake_kcal = safe_metric_lookup(health_metrics, "energy_intake_total_kcal")
    protein_g = safe_metric_lookup(health_metrics, "protein_total_g")
    carbs_g = safe_metric_lookup(health_metrics, "carbs_total_g")
    fat_g = safe_metric_lookup(health_metrics, "fat_total_g")
    adjusted_intake = intake_kcal * bias_factor

    # RMR
    rmr_baseline = calculate_rmr_mifflin(weight_kg, height_cm, age, gender)
    hr_readings = band_data.get("hr", [])
    resting_hr = min([r["value"] for r in hr_readings] or [60]) if hr_readings else 60
    hrv_readings = band_data.get("hrv", [])
    hrv = np.mean([r["value"] for r in hrv_readings]) if hrv_readings else 50
    rmr = refine_rmr_with_hr(rmr_baseline, resting_hr, hrv)

    # AEE from activity API
    activity_readings = band_data.get("activity", [])
    aee = sum(a["totalCaloriesBurned"] for a in activity_readings) if activity_readings else 0
    if not aee:
        steps = next((m["value"] for m in health_metrics if m["metric"] == "steps_total"), 0)
        aee = steps * 0.04  # Rough kcal/step estimate

    # TEF
    tef = calculate_tef(adjusted_intake)

    # TEE
    tee = (rmr + aee + tef) * exp_correction

    # Energy Balance
    eb = adjusted_intake - tee

    # Uncertainty
    epsilon_in, epsilon_out = propagate_uncertainty(rmr, aee, tef, adjusted_intake)
    eb_low = eb - epsilon_in - epsilon_out
    eb_high = eb + epsilon_in + epsilon_out

    # Confidence and flags
    flags = []
    if intake_kcal == 0:
        flags.append("food_log_missing")
    if not band_data.get("hr"):
        flags.append("wearable_HR_incomplete")
    if not historical_weights:
        flags.append("weight_history_missing")
    conf_intake = calculate_confidence(flags)
    conf_exp = 0.85 if not flags else 0.75
    conf_body = 0.9 if current_weight or historical_weights else 0.7

    # CGM
    glucose_readings = band_data.get("cgm", [])
    cgm_mean = np.mean([r["value"] for r in glucose_readings]) if glucose_readings else None
    cgm_var = np.std([r["value"] for r in glucose_readings]) if glucose_readings else None
    insulin_flag = "stable"
    if cgm_mean and cgm_mean > 100:
        insulin_flag = "monitor" if cgm_var and cgm_var > 15 else "stable"

    # Weight trend
    weight_trend_14d = 0.0
    trend_14d = "balance"
    if historical_weights and len(historical_weights) >= 2:
        weights = [w for d, w in sorted(historical_weights.items())]
        weight_trend_14d = weights[-1] - weights[0]
        trend_14d = "deficit" if weight_trend_14d < 0 else "surplus" if weight_trend_14d > 0 else "balance"

    return {
        "date": date_str,
        "energy_balance": {
            "estimate_kcal": round(eb),
            "confidence_range_kcal": [round(eb_low), round(eb_high)],
            "trend_14d": trend_14d,
            "risk_flags": flags
        },
        "intake": {
            "logged_kcal": round(intake_kcal),
            "bias_adjusted_kcal": round(adjusted_intake),
            "macros": {"protein_g": round(protein_g), "carbs_g": round(carbs_g), "fat_g": round(fat_g)},
            "confidence": conf_intake
        },
        "expenditure": {
            "RMR_kcal": round(rmr),
            "AEE_kcal": round(aee),
            "TEF_kcal": round(tef),
            "TEE_kcal": round(tee),
            "confidence": conf_exp
        },
        "body_metrics": {
            "weight_kg": weight_kg,
            "weight_trend_14d": round(weight_trend_14d, 1),
            "confidence": conf_body
        },
        "calibration": {
            "intake_bias_factor": round(bias_factor, 2),
            "expenditure_correction_factor": round(exp_correction, 2)
        },
        "optional_metrics": {
            "cgm_mean_glucose": round(cgm_mean) if cgm_mean else None,
            "cgm_variability": round(cgm_var) if cgm_var else None,
            "insulin_sensitivity_flag": insulin_flag
        }
    }