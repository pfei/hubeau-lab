"""Bulk ingestion of hydrometric flow rate observations into SQLite.

Fetches 7 days of real-time flow rate (Q) observations for a set of
active stations in a given French department, concurrently via
AsyncHubeauClient, and stores the results in a local SQLite database.

Usage:
    uv run python scripts/hydrometrie/bulk_ingest.py
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hubeau_data.async_client import AsyncHubeauClient
from hubeau_data.models.hydrometrie import ObservationTrParams, StationParams

DEPARTMENT = "64"  # Pyrénées-Atlantiques
N_STATIONS = 5
WINDOW_DAYS = 7
DB_PATH = (
    Path(__file__).parent.parent.parent / "data" / "hydrometrie" / "observations.db"
)


async def fetch(department: str, n_stations: int, window_days: int) -> tuple:
    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    async with AsyncHubeauClient() as client:
        stations = await client.hydrometrie.get_stations(
            StationParams(en_service=True, code_departement=department, size=n_stations)
        )
        print(
            f"Fetching {window_days}d of Q observations for {len(stations)} stations..."
        )
        results = await asyncio.gather(
            *[
                client.hydrometrie.get_observations_tr(
                    ObservationTrParams(
                        code_entite=[s.code_station],
                        grandeur_hydro=["Q"],
                        date_debut_obs=since,
                        size=2000,
                        sort="asc",
                    )
                )
                for s in stations
            ]
        )
    return stations, results


def ingest(stations, results, db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            code_station    TEXT,
            libelle_station TEXT,
            date_obs        TEXT,
            resultat_obs    REAL,
            grandeur_hydro  TEXT
        )
    """)
    con.execute("DELETE FROM observations")
    rows = [
        (
            s.code_station,
            s.libelle_station,
            o.date_obs,
            o.resultat_obs,
            o.grandeur_hydro,
        )
        for s, obs in zip(stations, results)
        for o in obs
    ]
    con.executemany("INSERT INTO observations VALUES (?,?,?,?,?)", rows)
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    con.close()
    return total


def main() -> None:
    stations, results = asyncio.run(fetch(DEPARTMENT, N_STATIONS, WINDOW_DAYS))
    for s, obs in zip(stations, results):
        print(f"  {s.code_station} ({s.libelle_station}): {len(obs)} obs")
    n_rows = ingest(stations, results, DB_PATH)
    print(f"Inserted {n_rows} rows into {DB_PATH}")


if __name__ == "__main__":
    main()
