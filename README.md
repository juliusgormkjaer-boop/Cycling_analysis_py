# Cycling Analysis Py

An early, explainable Python analysis pipeline for serious amateur cyclists.
It reads Garmin `.fit` and `.fit.gz` files, extracts power and heart-rate data,
calculates activity metrics, compares development windows, evaluates watt goals,
and writes an HTML report plus an auditable CSV file.

The long-term product direction is an app or report that helps an "average joe"
cyclist understand strengths, weaknesses, and training priorities without needing
to become a coach first.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
cp athlete.example.json athlete.json
```

Edit `athlete.json`, particularly the dated FTP values, then run:

```bash
PYTHONPATH=src python -m power_report.cli analyze . --config athlete.json --output output/report.html
```

Run the tests with:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

The generated `output/report.html` includes:

- data coverage checks for power and heart-rate samples
- average power, normalized power, intensity factor, TSS and work in kJ
- best 5-second, 1-minute, 5-minute, 20-minute and 60-minute efforts
- power-zone exposure based on dated FTP values
- early-versus-late development indicators
- goal gaps from `power_goals`
- practical rider-profile insights

## Athlete configuration

`athlete.json` is deliberately ignored by Git because it may contain personal
data. Start from `athlete.example.json`.

Power goal keys are durations in seconds. For example, `"300": 360` means a
goal of 360 W for 5 minutes.

The MVP deliberately separates observations from interpretations. A trend is
only reported when both comparison windows contain enough valid efforts.

## Current limitations

- Power is expected at approximately one-second resolution.
- TSS is calculated only where a dated FTP is configured.
- The development comparison uses early and late 8-week windows. It is an
  association, not proof that a particular kind of training caused the change.
- Reference-group rankings are not part of the first version.
