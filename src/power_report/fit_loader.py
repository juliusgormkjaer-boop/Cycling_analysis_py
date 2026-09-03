from __future__ import annotations

import gzip
import io
from datetime import timezone
from pathlib import Path

from .models import Activity, Sample


def _value(frame, name):
    try:
        return frame.get_value(name)
    except (KeyError, ValueError):
        return None


def load_fit(path: str | Path) -> Activity | None:
    try:
        import fitdecode
    except ImportError as exc:
        raise RuntimeError("FIT support requires `python -m pip install -e .`") from exc

    source = Path(path)
    data = gzip.open(source, "rb").read() if source.suffix == ".gz" else source.read_bytes()
    samples: list[Sample] = []
    sport = "unknown"
    start_time = None
    elapsed = None
    try:
        with fitdecode.FitReader(io.BytesIO(data)) as reader:
            for frame in reader:
                if frame.frame_type != fitdecode.FIT_FRAME_DATA:
                    continue
                if frame.name == "record":
                    timestamp = _value(frame, "timestamp")
                    if timestamp is not None:
                        samples.append(Sample(timestamp=timestamp, power=_value(frame, "power"), heart_rate=_value(frame, "heart_rate")))
                elif frame.name == "session":
                    sport = str(_value(frame, "sport") or sport)
                    start_time = _value(frame, "start_time") or start_time
                    elapsed = _value(frame, "total_elapsed_time") or elapsed
    except (fitdecode.FitError, EOFError, OSError):
        return None
    if not samples:
        return None
    start_time = start_time or samples[0].timestamp
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    return Activity(str(source), start_time, sport, samples, float(elapsed) if elapsed else None)


def discover_fit_files(root: str | Path) -> list[Path]:
    base = Path(root)
    # Prefer an uncompressed copy when both foo.fit and foo.fit.gz exist.
    unique: dict[str, Path] = {}
    for path in sorted((*base.rglob("*.fit.gz"), *base.rglob("*.fit"))):
        key = str(path)[:-3] if str(path).endswith(".gz") else str(path)
        if key not in unique or path.suffix == ".fit":
            unique[key] = path
    return sorted(unique.values())
