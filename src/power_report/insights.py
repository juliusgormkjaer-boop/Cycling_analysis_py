from __future__ import annotations

from dataclasses import dataclass

from .config import AthleteConfig
from .models import ActivityMetrics


@dataclass(slots=True)
class GoalGap:
    duration_seconds: int
    current_watts: float | None
    goal_watts: float
    gap_watts: float | None
    gap_percent: float | None


@dataclass(slots=True)
class Insight:
    title: str
    message: str
    recommendation: str


def best_power_by_duration(metrics: list[ActivityMetrics]) -> dict[int, float]:
    best: dict[int, float] = {}
    for item in metrics:
        for duration, watts in item.best_efforts.items():
            if watts is None:
                continue
            best[duration] = max(best.get(duration, 0.0), watts)
    return best


def compare_goals(metrics: list[ActivityMetrics], config: AthleteConfig) -> list[GoalGap]:
    best = best_power_by_duration(metrics)
    gaps: list[GoalGap] = []
    for duration, goal in sorted(config.power_goals.items()):
        current = best.get(duration)
        gap = goal - current if current is not None else None
        percent = gap / goal * 100 if gap is not None and goal else None
        gaps.append(GoalGap(duration, current, goal, gap, percent))
    return gaps


def athlete_profile(metrics: list[ActivityMetrics], config: AthleteConfig) -> list[Insight]:
    best = best_power_by_duration(metrics)
    insights: list[Insight] = []
    if not best:
        return [
            Insight(
                "No power profile yet",
                "The files parsed, but there are no valid power efforts to profile.",
                "Check that the input files include power meter or smart trainer watt data.",
            )
        ]

    short = _ratio(best.get(60), best.get(1200))
    five_to_twenty = _ratio(best.get(300), best.get(1200))
    threshold = best.get(1200) or best.get(3600)
    ftp = config.ftp_at(metrics[-1].start_time) if metrics else None

    if short is not None:
        if short >= 1.9:
            insights.append(
                Insight(
                    "Strong short-power punch",
                    f"Your 1-minute power is {short:.1f}x your 20-minute power, which points to good anaerobic punch.",
                    "Use this as a weapon, but keep threshold and aerobic work consistent so repeated hard efforts do not fade late in rides.",
                )
            )
        elif short <= 1.45:
            insights.append(
                Insight(
                    "Limited short-power reserve",
                    f"Your 1-minute power is {short:.1f}x your 20-minute power, so hard surges may cost more than they should.",
                    "Add controlled VO2max and anaerobic intervals once or twice per week when freshness allows.",
                )
            )

    if five_to_twenty is not None and five_to_twenty <= 1.12:
        insights.append(
            Insight(
                "VO2max may be the limiter",
                f"Your 5-minute power is only {five_to_twenty:.2f}x your 20-minute power.",
                "Build a block around 3- to 6-minute repeats above threshold, supported by easy endurance volume.",
            )
        )

    if threshold and ftp and threshold < ftp * 0.92:
        insights.append(
            Insight(
                "Threshold test coverage looks low",
                f"Best 20-minute power is {threshold:.0f} W versus a configured FTP of {ftp:.0f} W.",
                "Either the dataset lacks maximal threshold efforts, or the FTP value should be checked before using TSS and zones for planning.",
            )
        )

    if config.weight_kg and threshold:
        watts_per_kg = threshold / config.weight_kg
        insights.append(
            Insight(
                "Current climbing benchmark",
                f"Best threshold-like power is about {watts_per_kg:.1f} W/kg.",
                "Track this alongside absolute watts; flat speed and climbs reward different parts of the same engine.",
            )
        )

    if not insights:
        insights.append(
            Insight(
                "Balanced visible profile",
                "The current power curve does not show an obvious single outlier strength or weakness.",
                "Keep collecting data and add explicit goals so the report can compare your current power curve against target demands.",
            )
        )
    return insights


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator
