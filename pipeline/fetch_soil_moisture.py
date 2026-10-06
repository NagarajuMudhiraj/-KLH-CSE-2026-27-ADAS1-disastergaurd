import os
import json
import time
import requests
import pandas as pd

def main():
    print("=== Fetching ECMWF ERA5 Soil Moisture for Dataset ===")
    v9_path = os.path.join("data", "processed", "road_risk_dataset_v9.csv")
    df = pd.read_csv(v9_path)
    
    unique_pts = df[['event_date', 'latitude', 'longitude']].drop_duplicates().reset_index(drop=True)
    print(f"Total unique point-date queries: {len(unique_pts)}")
    
    cache_file = os.path.join("data", "intermediate", "soil_moisture_cache.json")
    cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)
            
    url = "https://archive-api.open-meteo.com/v1/archive"
    new_fetches = 0
    for idx, row in unique_pts.iterrows():
        lat = round(float(row['latitude']), 4)
        lon = round(float(row['longitude']), 4)
        date_str = str(row['event_date'])
        key = f"{date_str}_{lat:.4f}_{lon:.4f}"
        
        if key in cache:
            continue
            
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "daily": ["soil_moisture_0_to_7cm_mean"],
            "timezone": "Asia/Kolkata"
        }
        success = False
        for attempt in range(4):
            try:
                r = requests.get(url, params=params, timeout=12)
                if r.status_code == 200:
                    vals = r.json().get("daily", {}).get("soil_moisture_0_to_7cm_mean", [])
                    if vals and vals[0] is not None:
                        cache[key] = round(float(vals[0]), 3)
                        new_fetches += 1
                        success = True
                    break
                elif r.status_code == 429:
                    time.sleep(1.5 * (attempt + 1))
            except Exception:
                time.sleep(1.0 * (attempt + 1))
        if not success:
            print(f"Warning: Failed to fetch for {key}")
        time.sleep(0.15)
        
    os.makedirs(os.path.join("data", "intermediate"), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)
        
    print(f"Soil moisture fetch complete. Total cached: {len(cache)}, New: {new_fetches}")

if __name__ == "__main__":
    main()
