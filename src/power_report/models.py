from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Sample:
    timestamp: datetime
    power: float | None = None
    heart_rate: float | None = None


@dataclass(slots=True)
class Activity:
    source: str
    start_time: datetime
    sport: str
    samples: list[Sample] = field(default_factory=list)
    elapsed_seconds: float | None = None


@dataclass(slots=True)
class ActivityMetrics:
    source: str
    start_time: datetime
    sport: str
    duration_seconds: int
    power_seconds: int
    hr_seconds: int
    average_power: float | None
    normalized_power: float | None
    average_hr: float | None
    max_hr: float | None
    intensity_factor: float | None
    tss: float | None
    work_kj: float | None
    best_efforts: dict[int, float | None]
    zone_seconds: dict[str, int]
    warnings: list[str] = field(default_factory=list)
