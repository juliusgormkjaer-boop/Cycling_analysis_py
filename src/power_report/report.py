from __future__ import annotations

import csv
import html
from collections import defaultdict
from pathlib import Path

from .config import AthleteConfig
from .insights import athlete_profile, compare_goals
from .models import ActivityMetrics
from .trends import TrendResult


def _fmt(value, digits=0, suffix=""):
    return "—" if value is None else f"{value:.{digits}f}{suffix}"


def write_activities_csv(metrics: list[ActivityMetrics], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    effort_keys = sorted(metrics[0].best_efforts) if metrics else []
    fields = ["date", "sport", "duration_seconds", "power_seconds", "hr_seconds", "average_power", "normalized_power", "average_hr", "max_hr", "intensity_factor", "tss", "work_kj"] + [f"best_{key}s" for key in effort_keys] + ["warnings", "source"]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in metrics:
            row = {key: getattr(item, key) for key in fields if hasattr(item, key)}
            row.update({f"best_{key}s": item.best_efforts[key] for key in effort_keys})
            row.update(date=item.start_time.isoformat(), warnings="; ".join(item.warnings))
            writer.writerow(row)


def write_html(config: AthleteConfig, metrics: list[ActivityMetrics], trends: list[TrendResult], path: str | Path, skipped: int = 0) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    valid_power = [item for item in metrics if item.power_seconds]
    valid_hr = [item for item in metrics if item.hr_seconds]
    low_power_coverage = [item for item in metrics if "Power coverage below 80%" in item.warnings]
    total_tss = sum(item.tss or 0 for item in metrics)
    zone_totals = defaultdict(int)
    for item in metrics:
        for zone, seconds in item.zone_seconds.items():
            zone_totals[zone] += seconds
    goal_gaps = compare_goals(metrics, config)
    insights = athlete_profile(metrics, config)
    trend_rows = "".join(
        f"<tr><td>{item.duration_seconds}s</td><td>{_fmt(item.early_watts, 0, ' W')}</td><td>{_fmt(item.late_watts, 0, ' W')}</td><td>{_fmt(item.change_percent, 1, '%')}</td><td>{item.early_count}/{item.late_count}</td><td>{html.escape(item.confidence)}</td></tr>"
        for item in trends
    )
    zone_rows = "".join(f"<tr><td>{zone}</td><td>{seconds / 3600:.1f} h</td></tr>" for zone, seconds in sorted(zone_totals.items()))
    goal_rows = "".join(
        f"<tr><td>{item.duration_seconds}s</td><td>{_fmt(item.current_watts, 0, ' W')}</td><td>{_fmt(item.goal_watts, 0, ' W')}</td><td>{_fmt(item.gap_watts, 0, ' W')}</td><td>{_fmt(item.gap_percent, 1, '%')}</td></tr>"
        for item in goal_gaps
    )
    if not goal_rows:
        goal_rows = "<tr><td colspan=\"5\">No watt goals configured.</td></tr>"
    insight_rows = "".join(
        f"<section class=\"insight\"><h3>{html.escape(item.title)}</h3><p>{html.escape(item.message)}</p><p><strong>Training focus:</strong> {html.escape(item.recommendation)}</p></section>"
        for item in insights
    )
    interpretation = []
    for item in trends:
        if item.change_percent is None:
            continue
        direction = "improved" if item.change_percent >= 2 else "declined" if item.change_percent <= -2 else "was broadly stable"
        interpretation.append(f"The {item.duration_seconds}-second performance level {direction} ({item.change_percent:+.1f}%).")
    if not interpretation:
        interpretation.append("There is not enough repeated data in both comparison windows to make a reliable development statement.")
    bullets = "".join(f"<li>{html.escape(text)}</li>" for text in interpretation)
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Power report — {html.escape(config.name)}</title><style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 24px;color:#17202a}}h1,h2{{color:#102a43}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}.card{{background:#eef5f9;border-radius:10px;padding:16px}}.value{{font-size:1.7rem;font-weight:700}}table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}th,td{{padding:9px;border-bottom:1px solid #d9e2ec;text-align:right}}th:first-child,td:first-child{{text-align:left}}.insight{{border-left:4px solid #486581;padding:2px 0 2px 14px;margin:14px 0}}.insight h3{{margin-bottom:0}}.note{{background:#fff7df;padding:14px;border-left:4px solid #f0b429}}footer{{color:#627d98;font-size:.9rem}}</style></head><body>
<h1>Power report: {html.escape(config.name)}</h1><div class="cards"><div class="card"><div class="value">{len(metrics)}</div>parsed activities</div><div class="card"><div class="value">{len(valid_power)}</div>with power</div><div class="card"><div class="value">{sum(i.duration_seconds for i in metrics)/3600:.1f} h</div>recorded</div><div class="card"><div class="value">{total_tss:.0f}</div>TSS with configured FTP</div></div>
<h2>Data coverage</h2><p>{len(valid_power)} of {len(metrics)} activities contain valid power, {len(valid_hr)} contain valid heart rate, and {len(low_power_coverage)} power activities have less than 80% sample coverage. Conclusions below should be read in that context.</p>
<h2>Development indicators</h2><p>Each period uses the median of its three best activity-level efforts, reducing the influence of one exceptional ride.</p><table><thead><tr><th>Duration</th><th>Early</th><th>Late</th><th>Change</th><th>Efforts early/late</th><th>Evidence</th></tr></thead><tbody>{trend_rows}</tbody></table><ul>{bullets}</ul>
<h2>Goal gaps</h2><p>Configured watt goals are compared with the best observed efforts in this dataset.</p><table><thead><tr><th>Duration</th><th>Current best</th><th>Goal</th><th>Gap</th><th>Gap %</th></tr></thead><tbody>{goal_rows}</tbody></table>
<h2>Rider profile</h2>{insight_rows}
<h2>Power-zone exposure</h2><table><thead><tr><th>Zone</th><th>Time</th></tr></thead><tbody>{zone_rows}</tbody></table>
<p class="note"><strong>Interpretation boundary:</strong> these are observational indicators. FTP history, data coverage, equipment changes, terrain and workout selection can affect the result. Association between zone exposure and later performance is not proof of causation.</p>
<footer>{skipped} FIT files contained no usable activity records or could not be decoded. Detailed values are available in activities.csv.</footer></body></html>"""
    destination.write_text(document, encoding="utf-8")
