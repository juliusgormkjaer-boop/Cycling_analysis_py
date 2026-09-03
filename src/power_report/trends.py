from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from statistics import median

from .models import ActivityMetrics


@dataclass(slots=True)
class TrendResult:
    duration_seconds: int
    early_watts: float | None
    late_watts: float | None
    change_percent: float | None
    early_count: int
    late_count: int
    confidence: str


def _performance_level(values: list[float]) -> float | None:
    """Median of the three best observations: robust to a single exceptional PR."""
    return median(sorted(values, reverse=True)[:3]) if values else None


def compare_windows(metrics: list[ActivityMetrics], window_days: int = 56, minimum_efforts: int = 3) -> list[TrendResult]:
    valid = sorted((item for item in metrics if item.power_seconds), key=lambda item: item.start_time)
    if not valid:
        return []
    first_date, last_date = valid[0].start_time, valid[-1].start_time
    early_end = first_date + timedelta(days=window_days)
    late_start = last_date - timedelta(days=window_days)
    results: list[TrendResult] = []
    for duration in next(iter(valid)).best_efforts:
        early = [item.best_efforts[duration] for item in valid if item.start_time <= early_end and item.best_efforts[duration] is not None]
        late = [item.best_efforts[duration] for item in valid if item.start_time >= late_start and item.best_efforts[duration] is not None]
        early_level, late_level = _performance_level(early), _performance_level(late)
        sufficient = len(early) >= minimum_efforts and len(late) >= minimum_efforts
        change = (late_level / early_level - 1) * 100 if sufficient and early_level and late_level else None
        confidence = "sufficient repeated observations" if sufficient else "insufficient data"
        results.append(TrendResult(duration, early_level, late_level, change, len(early), len(late), confidence))
    return results
