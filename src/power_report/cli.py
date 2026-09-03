from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .fit_loader import discover_fit_files, load_fit
from .metrics import analyze_activity
from .report import write_activities_csv, write_html
from .trends import compare_windows


def run_analyze(args) -> int:
    config = load_config(args.config)
    files = discover_fit_files(args.input)
    metrics = []
    skipped = 0
    for index, path in enumerate(files, 1):
        activity = load_fit(path)
        if activity is None:
            skipped += 1
            continue
        metrics.append(analyze_activity(activity, config))
        if index % 50 == 0:
            print(f"Processed {index}/{len(files)} files")
    metrics.sort(key=lambda item: item.start_time)
    trends = compare_windows(metrics, config.comparison_window_days, config.minimum_efforts_per_window)
    output = Path(args.output)
    write_html(config, metrics, trends, output, skipped)
    write_activities_csv(metrics, output.with_name("activities.csv"))
    print(f"Report: {output}")
    print(f"Activities: {output.with_name('activities.csv')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="power-report")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="analyze FIT files and produce an HTML report")
    analyze.add_argument("input", help="directory containing .fit or .fit.gz files")
    analyze.add_argument("--config", required=True, help="athlete JSON configuration")
    analyze.add_argument("--output", default="output/report.html", help="HTML report path")
    analyze.set_defaults(func=run_analyze)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
