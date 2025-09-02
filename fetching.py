import requests
import aiohttp
import asyncio
from datetime import datetime, timedelta
from utils import LOGIN_URL, PROFILE_URL, API_BASE_URL, EMAIL, PASSWORD
import json

ACCESS_TOKEN = None

async def fetch_single_reading_type_daily_async(session, user_id, date_str, reading_type, key, subkey):
    """Fetch single reading type (hr, hrv, cgm, etc.) for a day."""
    url = f"{API_BASE_URL}/{reading_type}_readings/{user_id}/{date_str}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {key: data.get(subkey, []) if subkey else data}
            return {key: []}
    except Exception as e:
        print(f"Error fetching {reading_type}: {str(e)}")
        return {key: []}

async def fetch_all_data_for_week_async(user_id, start_date_str, num_days):
    """Fetch all band data (hr, hrv, cgm, activity, stress, sleep) for a week."""
    all_data_promises = []
    start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
    async with aiohttp.ClientSession() as session:
        for i in range(num_days):
            current_date_obj = start_date_obj + timedelta(days=i)
            current_date_str = current_date_obj.strftime("%Y-%m-%d")
            all_data_promises.append(fetch_single_reading_type_daily_async(
                session, user_id, current_date_str, 'hr', 'hr', 'heartrate_readings'))
            all_data_promises.append(fetch_single_reading_type_daily_async(
                session, user_id, current_date_str, 'hrv', 'hrv', 'hrv_readings'))
            all_data_promises.append(fetch_single_reading_type_daily_async(
                session, user_id, current_date_str, 'cgm', 'cgm', 'glucose_readings'))
            all_data_promises.append(fetch_single_reading_type_daily_async(
                session, user_id, current_date_str, 'stress', 'stress', 'stress_readings'))
            all_data_promises.append(fetch_single_reading_type_daily_async(
                session, user_id, current_date_str, 'activity', 'activity', 'activityReadings'))
            all_data_promises.append(fetch_single_reading_type_daily_async(
                session, user_id, current_date_str, 'sleep', 'sleep', None))  # No subkey for sleep
        daily_results = await asyncio.gather(*all_data_promises, return_exceptions=True)
    
    weekly_data = {'cgm': [], 'hr': [], 'hrv': [], 'sleep': [], 'stress': [], 'activity': []}
    for result in daily_results:
        if isinstance(result, dict):
            for key in weekly_data:
                if key in result and result[key]:
                    weekly_data[key].append(result[key])
    return weekly_data

def get_access_token():
    """Fetch access token for profile API."""
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    login_payload = {"email": EMAIL, "password": PASSWORD}
    try:
        response = requests.post(LOGIN_URL, json=login_payload)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == 200:
            ACCESS_TOKEN = data["content"]["accessToken"]
            print("✅ Successfully obtained access token.")
            return ACCESS_TOKEN
        else:
            print("❌ Login failed:", data)
            return None
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", str(e))
        return None

def fetch_user_profile(user_id):
    """Fetch user profile (age, gender, height, weight)."""
    token = get_access_token()
    if not token:
        return {"error": "Failed to get access token"}
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{PROFILE_URL}/{user_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

#def fetch_health_metrics(user_id, date_str):
    """Fetch daily health metrics (kcal, macros, steps, etc.)."""
    headers = {"x-user-id": str(user_id)}
    try:
        response = requests.get(HEALTH_METRICS_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching health metrics: {str(e)}")
        return []
    
def fetch_health_metrics(user_id, date_str):
    try:
        with open("values.json", "r") as f:
            data = json.load(f)
        
        # FIX: Access first array element
        if len(data) > 0 and "meals" in data[0] and len(data[0]["meals"]) > 0:
            meal = data[0]["meals"][0]
            
            # Calculate calories with correct keys
            protein_kcal = meal.get("protein_g", 0) * 4
            carbs_kcal = meal.get("carbs_g", 0) * 4
            fat_kcal = meal.get("fat_g", 0) * 9
            total_kcal = protein_kcal + carbs_kcal + fat_kcal
            
            return [
                {"metric": "energy_intake_total_kcal", "value": total_kcal},
                {"metric": "protein_total_g", "value": meal.get("protein_g", 0)},
                {"metric": "carbs_total_g", "value": meal.get("carbs_g", 0)},
                {"metric": "fat_total_g", "value": meal.get("fat_g", 0)},
                {"metric": "steps_total", "value": 8000}
            ]
        return []
    except Exception as e:
        print(f"Error reading values.json: {str(e)}")
        return []


import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python fetching.py <user_id> <date(YYYY-MM-DD)>")
        sys.exit(1)

    user_id = sys.argv[1]
    date_str = sys.argv[2]

    print(f"Fetching health metrics for user {user_id} on {date_str}...\n")
    result = fetch_health_metrics(user_id, date_str)
    print("Health Metrics Output:\n", result)


if __name__ == "__main__":
    main()
