import os
import requests
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/api", tags=["Weather Telemetry"])

@router.get("/weather")
def get_live_weather_info(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180)):
    """
    Fetch real-time weather and rainfall telemetry from OpenWeatherMap API
    or Open-Meteo Live Free API based on exact GPS coordinates.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()

    # 1. Try OpenWeatherMap API if API key is provided
    if api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={api_key}&units=metric"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                rain_mm = data.get("rain", {}).get("1h", 0.0)
                return {
                    "provider": "OpenWeatherMap API (Live)",
                    "city": data.get("name", "GPS Location"),
                    "temp": round(data["main"]["temp"], 1),
                    "rainfall": round(rain_mm, 1),
                    "humidity": data["main"]["humidity"],
                    "windSpeed": round(data["wind"]["speed"] * 3.6, 1), # convert m/s to km/h
                    "description": data["weather"][0]["description"].title()
                }
        except Exception as e:
            print(f"OpenWeatherMap API error ({e}). Falling back to Open-Meteo Live API...")

    # 2. Keyless Live Real-Time Weather API: Open-Meteo
    try:
        open_meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,precipitation,rain,showers,wind_speed_10m&hourly=precipitation"
        resp = requests.get(open_meteo_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current", {})
            rain_val = current.get("precipitation", 0.0) or current.get("rain", 0.0)
            wind_kph = current.get("wind_speed_10m")
            temp = current.get("temperature_2m")
            hum = current.get("relative_humidity_2m")
            if wind_kph is None or temp is None or hum is None:
                raise ValueError("Live weather response is incomplete")

            # Derive weather description from live precipitation
            if rain_val > 10.0:
                desc = "Severe Downpour & Heavy Rain Alert"
            elif rain_val > 2.0:
                desc = "Moderate Rain & Surface Water"
            elif rain_val > 0.0:
                desc = "Light Rain & Damp Roads"
            else:
                desc = "Clear / Overcast - No Immediate Rain"

            return {
                "provider": "Open-Meteo Live Telemetry API",
                "city": f"GPS ({lat:.3f}, {lng:.3f})",
                "temp": round(temp, 1),
                "rainfall": round(rain_val, 1),
                "humidity": hum,
                "windSpeed": round(wind_kph, 1),
                "description": desc
            }
    except Exception as e:
        print(f"Open-Meteo Live API error: {e}")

    raise HTTPException(status_code=503, detail="Live weather providers are unavailable. Please try again shortly.")
