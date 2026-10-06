import os
import time
import requests
import json
import urllib3
import pandas as pd
from shapely.geometry import LineString, Point

urllib3.disable_warnings()

def get_elevation(lat, lon):
    url = "https://api.open-meteo.com/v1/elevation"
    r = requests.get(url, params={"latitude": lat, "longitude": lon}, timeout=10)
    if r.status_code == 200:
        elevs = r.json().get("elevation", [])
        return elevs[0] if elevs else None
    return None

def get_historical_weather(lat, lon, date_str):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": ["precipitation_sum", "temperature_2m_mean", "wind_speed_10m_max"],
        "timezone": "Asia/Kolkata"
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code == 200:
        d = r.json().get("daily", {})
        precip = d.get("precipitation_sum", [None])[0]
        temp = d.get("temperature_2m_mean", [None])[0]
        wind = d.get("wind_speed_10m_max", [None])[0]
        return precip, temp, wind
    return None, None, None

print("Testing weather and elevation APIs...")
e = get_elevation(17.6681, 80.8772)
p, t, w = get_historical_weather(17.6681, 80.8772, "2019-08-09")
print(f"Elevation: {e}m, Precip: {p}mm, Temp: {t}C, Wind: {w}km/h")
