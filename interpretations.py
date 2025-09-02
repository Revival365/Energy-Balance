def interpret_results(results_json):
    """
    Generate a more detailed, dynamic, and user-friendly interpretation 
    of the energy balance results as a string.
    """
    # --- Extract all necessary data points from the results ---
    eb = results_json["energy_balance"]["estimate_kcal"]
    range_low, range_high = results_json["energy_balance"]["confidence_range_kcal"]
    trend = results_json["energy_balance"]["trend_14d"]
    flags = results_json["energy_balance"]["risk_flags"]
    date = results_json["date"]

    logged_kcal = results_json["intake"]["logged_kcal"]
    adjusted_intake = results_json["intake"]["bias_adjusted_kcal"]
    protein_g = results_json["intake"]["macros"]["protein_g"]
    carbs_g = results_json["intake"]["macros"]["carbs_g"]
    fat_g = results_json["intake"]["macros"]["fat_g"]

    rmr = results_json["expenditure"]["RMR_kcal"]
    aee = results_json["expenditure"]["AEE_kcal"]
    tef = results_json["expenditure"]["TEF_kcal"]
    tee = results_json["expenditure"]["TEE_kcal"]

    cgm_mean = results_json["optional_metrics"]["cgm_mean_glucose"]
    cgm_var = results_json["optional_metrics"]["cgm_variability"]
    insulin_flag = results_json["optional_metrics"]["insulin_sensitivity_flag"]

    # --- Build the Interpretation String ---
    interpretation = f"💡 Your Daily Energy Balance Analysis for {date}\n\n"

    # --- Handle the "food_log_missing" case with CGM context ---
    if "food_log_missing" in flags:
        interpretation += "❗️ **Action Needed: Food Log is Empty**\n"
        if cgm_mean and cgm_var:
            # High variability suggests they ate but didn't log.
            if cgm_var > 18:
                interpretation += ("We noticed your food log is empty, but your glucose data shows significant activity. "
                                   "It looks like you may have had meals but forgot to log them.\n\n"
                                   "**Because of this, your calculated energy balance of a {abs(eb)} kcal deficit is likely inaccurate.** "
                                   "Logging your meals is the most important step for an accurate analysis. Let's try to log them tomorrow!")
                return interpretation
            # Low variability suggests they genuinely fasted.
            else:
                interpretation += ("We see your food log is empty, and your glucose levels were very stable, "
                                   "which suggests you may have been fasting or intentionally skipped meals today. "
                                   "This resulted in a significant energy deficit of approximately **{abs(eb)} kcal**.\n\n"
                                   "If this was a planned fast, great job! If not, remember that consistent fueling is key for performance and health.")
                return interpretation
        else:
            # No CGM data to make an intelligent guess.
            interpretation += ("To calculate your energy balance, we need to know what you ate. "
                               "Please make sure to log your food intake for a complete and accurate analysis.")
            return interpretation

    # --- Standard interpretation when food has been logged ---
    status = "Deficit" if eb < 0 else "Surplus" if eb > 0 else "Balance"
    interpretation += f"**Overall Status: You're in a {status} of {abs(eb)} kcal.**\n"
    interpretation += f"- Our analysis places your true energy balance between **{range_low} kcal and {range_high} kcal**.\n"
    interpretation += f"- Your 14-day trend is currently showing a state of **{trend.capitalize()}**.\n"

    interpretation += "\n🍽️ **Intake Summary:**\n"
    interpretation += f"- You logged **{logged_kcal} kcal**. Based on typical reporting patterns, we've adjusted this to **{adjusted_intake} kcal** for our calculations.\n"
    interpretation += f"- Your Macros: **{protein_g}g Protein**, **{carbs_g}g Carbs**, and **{fat_g}g Fat**.\n"

    interpretation += "\n⚡ **Expenditure Summary:**\n"
    interpretation += f"- Your body burned a total of **{tee} kcal** today. Here's the breakdown:\n"
    interpretation += f"  - **Resting Metabolism (RMR):** {rmr} kcal (calories burned at rest).\n"
    interpretation += f"  - **Activity (AEE):** {aee} kcal (calories from your movement and exercise).\n"
    interpretation += f"  - **Digesting Food (TEF):** {tef} kcal (the thermic effect of your meals).\n"

    interpretation += "\n🧠 **Health Guidance & Insights:**\n"
    # Dynamic guidance based on the size and direction of the energy balance
    if status == "Deficit":
        if abs(eb) > 500:
            interpretation += f"- A significant deficit like this is effective for weight loss. You logged **{protein_g}g of protein**; ensure you're getting enough to support muscle while in a deficit.\n"
        else:
            interpretation += "- You're in a small, controlled deficit. This is an excellent strategy for steady and sustainable slow paced fat loss without feeling deprived.\n"
    elif status == "Surplus":
        if eb > 400:
            interpretation += "- You're in a significant surplus, which is not ideal if your goal is to burn fat. If this was your goal, you might consider slightly reducing portion sizes.\n"
        else:
            interpretation += "- A slight surplus provides the energy needed for recovery and muscle growth, especially after tough workouts. If your goal is weight maintenance, this is a sign to watch closely - Note that you will not burn fat rapidly in this state if now workout is done.\n"
    else: # Balance
        interpretation += "- Fantastic job! You've matched your energy intake to your expenditure almost perfectly. This is the ideal state for maintaining your current weight and performance, but you will not see any fat burn or weight loss.\n"

    # Add CGM insights if available
    if cgm_mean:
        interpretation += f"- **Glucose Insights:** Your average glucose was **{cgm_mean} mg/dL** with a variability of **{cgm_var}**. "
        if insulin_flag == "monitor":
            interpretation += "Your glucose levels or variability were a bit high. It might be helpful to review and reduce the carbohydrate sources in your meals and see how your body responded.\n"
        else:
            interpretation += f"With an intake of **{carbs_g}g of carbs**, your glucose levels remained stable, which is a great sign of good metabolic health!\n"

    return interpretation