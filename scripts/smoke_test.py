"""Smoke test for hubeau-data installed from PyPI.

Runs a minimal set of real API calls to catch breaking changes before
bumping hubeau-data in hubeau-lab. No pytest — just plain asserts and
a clear exit code.

Usage:
    uv run python scripts/smoke_test.py
"""

import sys
from datetime import datetime, timedelta, timezone

from hubeau_data.client import HubeauClient
from hubeau_data.models.hydrometrie import ObservationTrParams

STATION = "O001004003"  # Garonne, Pyrenees — confirmed active

client = HubeauClient()
failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name}{': ' + detail if detail else ''}")
        failures.append(name)


print("\n── hydrometrie ──")

# Health check
health = client.hydrometrie.check_health()
check(
    "healthy_ratio == 1.0", health.healthy_ratio == 1.0, f"got {health.healthy_ratio}"
)
check(
    "all endpoints ok",
    all(e.ok for e in health.endpoints),
    str([e.name for e in health.endpoints if not e.ok]),
)

# Real-time observations
since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
params = ObservationTrParams(
    code_entite=[STATION],
    grandeur_hydro=["Q"],
    date_debut_obs=since,
    size=10,
    sort="asc",
)
obs = client.hydrometrie.get_observations_tr(params)
check("observations_tr returns data", len(obs.data) > 0, f"got {len(obs.data)}")
check(
    "code_entite filter works",
    all(o.code_station == STATION for o in obs.data if o.code_station is not None),
    "unexpected stations in response",
)
check(
    "resultat_obs is float",
    all(
        isinstance(o.resultat_obs, float)
        for o in obs.data
        if o.resultat_obs is not None
    ),
)

# Summary
print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    sys.exit(1)
else:
    print("All checks passed.")
