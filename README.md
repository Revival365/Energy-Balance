Energy Balance Tracker
Overview

Energy Balance Tracker is a Python-based project designed to calculate, analyze, and interpret a person’s daily energy balance. It integrates nutritional data, activity expenditure, and health metrics into a single pipeline to provide a complete picture of caloric intake, energy burn, and macro distribution.

The goal of the project is to help users, athletes, or health researchers understand how their food intake compares against their daily energy needs, and whether they are in a surplus, deficit, or balanced state.

Features

Daily Energy Balance: Tracks calories consumed versus calories burned.

Macronutrient Analysis: Compares intake of proteins, carbs, and fats against set goals.

Projection Modeling: Estimates the projected intake and deficit for the rest of the day.

Hourly Flow Tracking: Provides a timeline of intake and burn throughout the day.

Customizable Metrics: Works with real or simulated inputs for meals, activity, and sleep.

Interpretations: Translates raw calculations into meaningful health and performance insights.

Project Structure

main.py – The entry point that runs the entire pipeline and generates the final energy balance report.

computations.py – Handles all mathematical calculations such as caloric deficits, macro comparisons, and projections.

fetching.py – Manages fetching of health, nutrition, and activity data. Supports asynchronous operations to collect data efficiently.

interpretations.py – Converts numeric results into human-readable insights, for example whether a user has exceeded their protein goals or is under their carb target.

utils.py – Stores reusable utility functions, configuration constants, and helper methods for authentication and API endpoints.

values.json – Example input file containing daily metrics, meals, activity logs, and health parameters.

energy_balance_output.json – Example output file summarizing calculated daily balance, macros, and hourly flow of intake versus burn.

Input Data

The system uses structured JSON input. It includes:

Daily metrics such as basal energy expenditure, steps, stress index, and sleep values.

Meals with macronutrient breakdown (protein, carbs, fats, fiber, sugar, etc.).

Timestamps for when meals are consumed or updated.

Optional physiological data like heart rate, blood pressure, and glucose levels.

This input serves as the foundation for calculations.

Processing Flow

Data Ingestion
Input JSON is loaded, containing metrics and meal logs.

Computation
Energy intake and energy expenditure are calculated. Deficits or surpluses are determined. Macronutrient values are compared against set goals.

Interpretation
The raw numbers are translated into insights such as:

"Protein intake exceeded target by 680g"

"Carbs are significantly above the goal"

"Daily deficit indicates projected weight loss"

Output Generation
A structured output JSON is produced that summarizes the day’s results and provides an hour-by-hour breakdown of intake versus burn.

Output Data

The output highlights:

Today’s Metrics – Current intake, burn, projected intake, and deficit.

Macronutrient Summary – Comparison of protein, carbs, and fats against targets and goals.

Daily Flow – Hourly tracking of intake and burn throughout the day, useful for visualizations.

This structured output makes it easy to build dashboards, charts, or further analytics.
