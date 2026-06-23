"""Hydrometric coverage sampling — DOM vs metropolitan France.

Fetches active stations for every French department (96 metro + 5 DOM),
runs data_coverage() on each station, and writes results to a CSV file.

Progress is logged to stdout so it can be captured by a Jupyter notebook
or monitored in a terminal.

Usage:
    uv run python scripts/hydrometrie/coverage_sampling.py
    uv run python scripts/hydrometrie/coverage_sampling.py --output data/custom.csv
    uv run python scripts/hydrometrie/coverage_sampling.py --n-stations 10
"""

import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from hubeau_data.async_client import AsyncHubeauClient
from hubeau_data.client import HubeauClient
from hubeau_data.models.hydrometrie import Station, StationParams
from hubeau_data.models.pagination import PagedResponse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOM_DEPS = ["971", "972", "973", "974", "976"]
DOM_LABELS = {
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "Réunion",
    "976": "Mayotte",
}

METRO_DEPS = (
    [f"{i:02d}" for i in range(1, 20)]
    + ["2A", "2B"]
    + [f"{i:02d}" for i in range(21, 96)]
)

ALL_DEPS = METRO_DEPS + DOM_DEPS

DEFAULT_OUTPUT = Path(__file__).parent.parent.parent / "data" / "coverage_dom_metro.csv"
DEFAULT_N_STATIONS = 20


# ---------------------------------------------------------------------------
# Step 1 — fetch station lists (async)
# ---------------------------------------------------------------------------


async def fetch_all_stations(deps: list[str], n: int) -> dict[str, list[Station]]:
    """Fetch up to n active stations per department, concurrently."""
    print(f"[1/2] Fetching station lists for {len(deps)} departments...", flush=True)
    async with AsyncHubeauClient(max_concurrent=5) as client:
        results = await asyncio.gather(
            *[
                client.hydrometrie.get_stations(
                    StationParams(code_departement=dep, en_service=True, size=n)
                )
                for dep in deps
            ],
            return_exceptions=True,
        )
    stations_by_dep: dict[str, list[Station]] = {}
    for dep, r in zip(deps, results):
        if isinstance(r, Exception):
            print(f"  ✗ {dep}: {type(r).__name__}: {r}", flush=True)
            stations_by_dep[dep] = []
        else:
            assert isinstance(r, PagedResponse)
            stations_by_dep[dep] = r.data
    total = sum(len(v) for v in stations_by_dep.values())
    print(f"  → {total} stations across {len(deps)} departments", flush=True)
    return stations_by_dep


# ---------------------------------------------------------------------------
# Step 2 — data_coverage per station (sync)
# ---------------------------------------------------------------------------


def run_coverage(stations_by_dep: dict[str, list[Station]]) -> list[dict[str, object]]:
    """Run data_coverage() for every station, logging progress to stdout."""
    client = HubeauClient()
    rows: list[dict[str, object]] = []

    all_pairs = [
        (dep, s) for dep, stations in stations_by_dep.items() for s in stations
    ]
    total = len(all_pairs)
    print(f"[2/2] Running data_coverage on {total} stations...", flush=True)

    for i, (dep, s) in enumerate(all_pairs, start=1):
        zone = "DOM" if dep in DOM_DEPS else "Metropole"
        label = DOM_LABELS.get(dep, dep)

        if i % 50 == 0 or i == total:
            print(f"  {i}/{total} — dep {dep} {label}", flush=True)

        try:
            cov = client.hydrometrie.data_coverage(code_station=s.code_station)
            for w in cov.windows:
                if w.endpoint == "observations_tr":
                    rows.append(
                        {
                            "dep": dep,
                            "zone": zone,
                            "label": label,
                            "code_station": s.code_station,
                            "libelle_station": s.libelle_station,
                            "latitude": s.latitude_station,
                            "longitude": s.longitude_station,
                            "count": w.count,
                            "latest": w.latest,
                            "error": w.error,
                        }
                    )
        except Exception as e:
            rows.append(
                {
                    "dep": dep,
                    "zone": zone,
                    "label": label,
                    "code_station": s.code_station,
                    "libelle_station": getattr(s, "libelle_station", ""),
                    "latitude": getattr(s, "latitude_station", None),
                    "longitude": getattr(s, "longitude_station", None),
                    "count": None,
                    "latest": None,
                    "error": type(e).__name__,
                }
            )

    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--n-stations",
        type=int,
        default=DEFAULT_N_STATIONS,
        help=f"Stations to sample per department (default: {DEFAULT_N_STATIONS})",
    )
    args = parser.parse_args()

    started_at = datetime.now(timezone.utc)
    print(
        f"coverage_sampling started at {started_at.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        flush=True,
    )
    print(
        f"  departments: {len(ALL_DEPS)} ({len(METRO_DEPS)} metro "
        f"+ {len(DOM_DEPS)} DOM)",
        flush=True,
    )
    print(f"  stations per department: {args.n_stations}", flush=True)
    print(f"  output: {args.output}", flush=True)
    print(flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    stations_by_dep = asyncio.run(fetch_all_stations(ALL_DEPS, args.n_stations))
    rows = run_coverage(stations_by_dep)

    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)

    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    print(flush=True)
    print(
        f"Done — {len(df)} rows written to {args.output} in {elapsed:.0f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
