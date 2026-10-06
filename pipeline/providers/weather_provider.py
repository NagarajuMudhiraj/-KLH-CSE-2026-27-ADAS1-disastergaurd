"""Weather data provider for ADAS road-risk pipeline.
Supports Open-Meteo (keyless, real-time) and OpenWeatherMap (API key-based).
Also provides SIMULATOR and FIXTURE modes.
"""
from __future__ import annotations

import json
import logging
import os
import random
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pipeline.providers.base import BaseProvider, ProviderMode, ProviderResult, SourceClassification

logger = logging.getLogger(__name__)


class WeatherProvider(BaseProvider):
    """Provides weather-related observations:
    - rainfall_mm_h
    - rainfall_10min_mm
    - rainfall_1h_mm
    - visibility_m (clamped to <= 10000.0)
    - temperature_c
    - wind_speed_kmh
    """

    SUPPORTED_FEATURES = [
        "rainfall_mm_h",
        "rainfall_10min_mm",
        "rainfall_1h_mm",
        "visibility_m",
        "temperature_c",
        "wind_speed_kmh",
    ]

    def __init__(
        self,
        mode: ProviderMode = ProviderMode.LIVE,
        owm_api_key: Optional[str] = None,
        fixture_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mode=mode, name="WeatherProvider")
        self.owm_api_key = owm_api_key or os.getenv("OPENWEATHER_API_KEY")
        self.fixture_data = fixture_data or {}

    @property
    def supported_features(self) -> List[str]:
        return self.SUPPORTED_FEATURES

    def fetch(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
        scenario: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        now_utc = (timestamp or datetime.now(timezone.utc)).isoformat()

        if self.mode == ProviderMode.FIXTURE:
            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.SYNTHETIC_BENCHMARK,
                timestamp_utc=now_utc,
                data={feat: self.fixture_data.get(feat, 0.0) for feat in self.SUPPORTED_FEATURES},
                raw_payload=self.fixture_data,
                is_available=True,
                metadata={"source": "fixture"},
            )

        if self.mode == ProviderMode.SIMULATOR:
            return self._generate_simulated_weather(scenario=scenario, now_utc=now_utc)

        # The live forecast endpoint is not a historical archive. Refuse a
        # historical request instead of treating the caller's old timestamp as
        # the time of a current API response.
        if timestamp is not None:
            requested = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
            if requested < datetime.now(timezone.utc) - timedelta(days=1):
                return ProviderResult(
                    provider_name=self.name,
                    mode=ProviderMode.UNAVAILABLE,
                    source_classification=SourceClassification.UNAVAILABLE,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    data={},
                    is_available=False,
                    error_message="Historical weather requires an explicit archive join with source-native location and observation time.",
                    metadata={"feature_status": "UNAVAILABLE", "requested_observation_time": requested.isoformat()},
                )

        # LIVE MODE: First attempt Open-Meteo, fall back or augment with OWM
        return self._fetch_live(latitude=latitude, longitude=longitude, now_utc=now_utc)

    def _fetch_live(self, latitude: float, longitude: float, now_utc: str) -> ProviderResult:
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={latitude:.4f}&longitude={longitude:.4f}&"
                f"current=temperature_2m,precipitation,wind_speed_10m,visibility&"
                f"hourly=precipitation"
            )
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ADAS-Disaster-Assistant/1.0 (Research/Academic Project)"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                raw_data = json.loads(response.read().decode("utf-8"))

            current = raw_data.get("current", {})
            temp = float(current.get("temperature_2m", 25.0))
            precip = float(current.get("precipitation", 0.0))
            wind = float(current.get("wind_speed_10m", 0.0))
            raw_vis = float(current.get("visibility", 10000.0))
            # Meteorological standard clamp to 10000.0m
            visibility = min(10000.0, max(0.0, raw_vis))

            hourly = raw_data.get("hourly", {})
            hourly_precip = hourly.get("precipitation", [])
            rain_1h = float(hourly_precip[0]) if hourly_precip else precip
            rain_10m = round(precip / 6.0, 2)

            extracted = {
                "rainfall_mm_h": round(precip, 2),
                "rainfall_10min_mm": rain_10m,
                "rainfall_1h_mm": round(rain_1h, 2),
                "visibility_m": round(visibility, 1),
                "temperature_c": round(temp, 1),
                "wind_speed_kmh": round(wind, 1),
            }

            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.REAL,
                timestamp_utc=now_utc,
                data=extracted,
                raw_payload=raw_data,
                is_available=True,
                metadata={"api": "Open-Meteo", "url": url},
            )
        except Exception as e:
            logger.warning(f"Open-Meteo fetch failed ({e}). Attempting OpenWeatherMap if key is present...")
            if self.owm_api_key:
                return self._fetch_owm(latitude=latitude, longitude=longitude, now_utc=now_utc)

            # Do not substitute climate-like constants when an API fails.
            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.UNAVAILABLE,
                timestamp_utc=now_utc,
                data={},
                raw_payload=None,
                is_available=False,
                error_message=str(e),
                metadata={"error": str(e)},
            )

    def _fetch_owm(self, latitude: float, longitude: float, now_utc: str) -> ProviderResult:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={self.owm_api_key}&units=metric"
            req = urllib.request.Request(url, headers={"User-Agent": "ADAS-Disaster-Assistant/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                raw_data = json.loads(response.read().decode("utf-8"))

            main = raw_data.get("main", {})
            wind = raw_data.get("wind", {})
            rain = raw_data.get("rain", {})
            rain_1h = float(rain.get("1h", 0.0))
            raw_vis = float(raw_data.get("visibility", 10000.0))
            visibility = min(10000.0, max(0.0, raw_vis))

            extracted = {
                "rainfall_mm_h": round(rain_1h, 2),
                "rainfall_10min_mm": round(rain_1h / 6.0, 2),
                "rainfall_1h_mm": round(rain_1h, 2),
                "visibility_m": round(visibility, 1),
                "temperature_c": round(float(main.get("temp", 25.0)), 1),
                "wind_speed_kmh": round(float(wind.get("speed", 0.0)) * 3.6, 1),
            }

            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.UNAVAILABLE,
                timestamp_utc=now_utc,
                data=extracted,
                raw_payload=raw_data,
                is_available=True,
                metadata={"api": "OpenWeatherMap"},
            )
        except Exception as e:
            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.REAL,
                timestamp_utc=now_utc,
                data={},
                raw_payload=None,
                is_available=False,
                error_message=f"OWM fallback failed: {e}",
            )

    def _generate_simulated_weather(self, scenario: Optional[str], now_utc: str) -> ProviderResult:
        scenario = scenario or random.choice(["clear", "moderate_rain", "heavy_monsoon", "dense_fog", "cyclone"])

        if scenario == "clear":
            data = {
                "rainfall_mm_h": 0.0,
                "rainfall_10min_mm": 0.0,
                "rainfall_1h_mm": 0.0,
                "visibility_m": round(random.uniform(7000.0, 10000.0), 1),
                "temperature_c": round(random.uniform(22.0, 34.0), 1),
                "wind_speed_kmh": round(random.uniform(2.0, 15.0), 1),
            }
        elif scenario == "moderate_rain":
            r_h = round(random.uniform(5.0, 18.0), 2)
            data = {
                "rainfall_mm_h": r_h,
                "rainfall_10min_mm": round(r_h / 6.0, 2),
                "rainfall_1h_mm": round(random.uniform(8.0, 25.0), 2),
                "visibility_m": round(random.uniform(2500.0, 6000.0), 1),
                "temperature_c": round(random.uniform(20.0, 26.0), 1),
                "wind_speed_kmh": round(random.uniform(15.0, 35.0), 1),
            }
        elif scenario == "heavy_monsoon":
            r_h = round(random.uniform(35.0, 95.0), 2)
            data = {
                "rainfall_mm_h": r_h,
                "rainfall_10min_mm": round(r_h / 6.0, 2),
                "rainfall_1h_mm": round(random.uniform(40.0, 110.0), 2),
                "visibility_m": round(random.uniform(200.0, 1200.0), 1),
                "temperature_c": round(random.uniform(18.0, 24.0), 1),
                "wind_speed_kmh": round(random.uniform(30.0, 65.0), 1),
            }
        elif scenario == "dense_fog":
            data = {
                "rainfall_mm_h": 0.0,
                "rainfall_10min_mm": 0.0,
                "rainfall_1h_mm": 0.0,
                "visibility_m": round(random.uniform(80.0, 350.0), 1),
                "temperature_c": round(random.uniform(8.0, 16.0), 1),
                "wind_speed_kmh": round(random.uniform(0.5, 6.0), 1),
            }
        elif scenario == "cyclone":
            r_h = round(random.uniform(60.0, 140.0), 2)
            data = {
                "rainfall_mm_h": r_h,
                "rainfall_10min_mm": round(r_h / 6.0, 2),
                "rainfall_1h_mm": round(random.uniform(75.0, 160.0), 2),
                "visibility_m": round(random.uniform(100.0, 500.0), 1),
                "temperature_c": round(random.uniform(19.0, 23.0), 1),
                "wind_speed_kmh": round(random.uniform(70.0, 130.0), 1),
            }
        else:
            data = {
                "rainfall_mm_h": 0.0,
                "rainfall_10min_mm": 0.0,
                "rainfall_1h_mm": 0.0,
                "visibility_m": 8000.0,
                "temperature_c": 25.0,
                "wind_speed_kmh": 10.0,
            }

        return ProviderResult(
            provider_name=self.name,
            mode=self.mode,
            source_classification=SourceClassification.REALISTIC_SIMULATION,
            timestamp_utc=now_utc,
            data=data,
            raw_payload={"scenario": scenario},
            is_available=True,
            metadata={"scenario": scenario},
        )
