from __future__ import annotations

import math
from collections import deque
from statistics import fmean

from .config import AthleteConfig
from .models import Activity, ActivityMetrics

EFFORT_DURATIONS = (5, 60, 300, 1200, 3600)
ZONE_LIMITS = (("Z1", 0.55), ("Z2", 0.75), ("Z3", 0.90), ("Z4", 1.05), ("Z5", 1.20), ("Z6", 1.50))


def rolling_means(values: list[float], window: int) -> list[float]:
    if window <= 0 or len(values) < window:
        return []
    result: list[float] = []
    queue: deque[float] = deque()
    total = 0.0
    for value in values:
        queue.append(value)
        total += value
        if len(queue) > window:
            total -= queue.popleft()
        if len(queue) == window:
            result.append(total / window)
    return result


def normalized_power(power: list[float]) -> float | None:
    rolling = rolling_means(power, 30)
    return fmean(value**4 for value in rolling) ** 0.25 if rolling else None


def best_average(power: list[float], duration: int) -> float | None:
    values = rolling_means(power, duration)
    return max(values) if values else None


def power_zone(power: float, ftp: float) -> str:
    ratio = power / ftp
    for name, upper in ZONE_LIMITS:
        if ratio < upper:
            return name
    return "Z7"


def analyze_activity(activity: Activity, config: AthleteConfig) -> ActivityMetrics:
    ordered = sorted(activity.samples, key=lambda sample: sample.timestamp)
    valid_power_samples = [sample for sample in ordered if sample.power is not None and math.isfinite(sample.power) and 0 <= sample.power <= 3000]
    power = [float(sample.power) for sample in valid_power_samples]
    hr = [float(sample.heart_rate) for sample in ordered if sample.heart_rate is not None and 20 <= sample.heart_rate <= 250]
    ftp = config.ftp_at(activity.start_time)
    np_value = normalized_power(power)
    duration = int(activity.elapsed_seconds or ((ordered[-1].timestamp - ordered[0].timestamp).total_seconds() + 1 if len(ordered) > 1 else len(ordered)))
    intensity = np_value / ftp if np_value is not None and ftp else None
    tss = duration / 3600 * intensity**2 * 100 if intensity is not None else None
    zones = {f"Z{number}": 0 for number in range(1, 8)}
    if ftp:
        for value in power:
            zones[power_zone(value, ftp)] += 1
    warnings: list[str] = []
    rejected_power = sum(sample.power is not None for sample in ordered) - len(valid_power_samples)
    if rejected_power:
        warnings.append(f"Rejected {rejected_power} implausible power samples")
    if not power:
        warnings.append("No valid power data")
    elif duration and len(power) / duration < 0.8:
        warnings.append("Power coverage below 80%")
    if not hr:
        warnings.append("No valid heart-rate data")
    if ftp is None:
        warnings.append("No applicable FTP; IF, zones and TSS omitted")
    return ActivityMetrics(
        source=activity.source,
        start_time=activity.start_time,
        sport=activity.sport,
        duration_seconds=duration,
        power_seconds=len(power),
        hr_seconds=len(hr),
        average_power=fmean(power) if power else None,
        normalized_power=np_value,
        average_hr=fmean(hr) if hr else None,
        max_hr=max(hr) if hr else None,
        intensity_factor=intensity,
        tss=tss,
        work_kj=sum(power) / 1000 if power else None,
        best_efforts={duration: best_average(power, duration) for duration in EFFORT_DURATIONS},
        zone_seconds=zones,
        warnings=warnings,
    )
