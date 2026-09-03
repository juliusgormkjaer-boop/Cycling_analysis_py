from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FtpEntry:
    from_date: date
    ftp: float


@dataclass(slots=True)
class AthleteConfig:
    name: str = "Athlete"
    weight_kg: float | None = None
    max_hr: int | None = None
    threshold_hr: int | None = None
    ftp_history: tuple[FtpEntry, ...] = ()
    power_goals: dict[int, float] = field(default_factory=dict)
    comparison_window_days: int = 56
    minimum_efforts_per_window: int = 3

    def ftp_at(self, value: datetime | date) -> float | None:
        target = value.date() if isinstance(value, datetime) else value
        applicable = [entry for entry in self.ftp_history if entry.from_date <= target]
        return max(applicable, key=lambda entry: entry.from_date).ftp if applicable else None


def load_config(path: str | Path) -> AthleteConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    history = tuple(
        sorted(
            (
                FtpEntry(datetime.strptime(item["from"], "%Y-%m-%d").date(), float(item["ftp"]))
                for item in raw.get("ftp_history", [])
            ),
            key=lambda item: item.from_date,
        )
    )
    return AthleteConfig(
        name=raw.get("name", "Athlete"),
        weight_kg=raw.get("weight_kg"),
        max_hr=raw.get("max_hr"),
        threshold_hr=raw.get("threshold_hr"),
        ftp_history=history,
        power_goals={int(key): float(value) for key, value in raw.get("power_goals", {}).items()},
        comparison_window_days=int(raw.get("comparison_window_days", 56)),
        minimum_efforts_per_window=int(raw.get("minimum_efforts_per_window", 3)),
    )
