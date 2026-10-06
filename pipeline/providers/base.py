"""Base provider interfaces and data structures for ADAS road-risk pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class ProviderMode(str, Enum):
    LIVE = "LIVE"
    SIMULATOR = "SIMULATOR"
    FIXTURE = "FIXTURE"
    UNAVAILABLE = "UNAVAILABLE"


class SourceClassification(str, Enum):
    REAL = "REAL"
    REALISTIC_SIMULATION = "REALISTIC_SIMULATION"
    SYNTHETIC_BENCHMARK = "SYNTHETIC_BENCHMARK"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ProviderResult:
    """Standardized response from any data provider."""
    provider_name: str
    mode: ProviderMode
    source_classification: SourceClassification
    timestamp_utc: str
    data: Dict[str, Any]
    raw_payload: Optional[Dict[str, Any]] = None
    is_available: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Explicit provenance contract. timestamp_utc remains for backwards
    # compatibility with Phase 1-7 callers; the fields below are authoritative.
    source_name: Optional[str] = None
    observed_at: Optional[str] = None
    retrieved_at: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    data_quality: str = "UNKNOWN"

    def __post_init__(self) -> None:
        self.source_name = self.source_name or self.provider_name
        self.retrieved_at = self.retrieved_at or self.timestamp_utc
        self.observed_at = self.observed_at or self.timestamp_utc
        if self.location is None and "latitude" in self.metadata and "longitude" in self.metadata:
            self.location = {"latitude": self.metadata["latitude"], "longitude": self.metadata["longitude"]}
        if self.source_classification == SourceClassification.UNAVAILABLE:
            self.is_available = False
            self.data_quality = "UNAVAILABLE"
        elif self.data_quality == "UNKNOWN":
            self.data_quality = "HIGH" if self.source_classification == SourceClassification.REAL else "SIMULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "mode": self.mode.value,
            "source_classification": self.source_classification.value,
            "timestamp_utc": self.timestamp_utc,
            "source_name": self.source_name,
            "observed_at": self.observed_at,
            "retrieved_at": self.retrieved_at,
            "location": self.location,
            "provenance": self.provenance,
            "data_quality": self.data_quality,
            "data": self.data,
            "is_available": self.is_available,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class BaseProvider(ABC):
    """Abstract base provider for all ADAS environmental and vehicle data sources."""

    def __init__(self, mode: ProviderMode = ProviderMode.LIVE, name: Optional[str] = None) -> None:
        self.mode = mode
        self.name = name or self.__class__.__name__

    @abstractmethod
    def fetch(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        """Fetch data for a given spatial coordinate and timestamp."""
        pass

    @property
    @abstractmethod
    def supported_features(self) -> list[str]:
        """List of canonical feature names this provider is responsible for."""
        pass
