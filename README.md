# hubeau-lab

Real-world usage notebooks for [`hubeau-data`](https://pypi.org/project/hubeau-data/), installed from PyPI.
Goal: exercise the client in real conditions, surface friction points back into `hubeau-data`.

## Setup

```bash
uv sync
uv run jupyter lab
```

## Notebooks

- `01_quickstart.ipynb` — first API call, parsing Pydantic models
- `02_async_bulk_ingest.ipynb` — `asyncio.gather` → SQLite ingestion
- `03_health_dashboard.ipynb` — `check_health()` across all 11 APIs
- `04_data_coverage_explorer.ipynb` — `data_coverage()` + pandas/matplotlib visualization

## Data

`data/` is gitignored except small sample files. SQLite databases are generated locally.
