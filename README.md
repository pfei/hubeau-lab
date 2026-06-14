# hubeau-lab

Real-world usage notebooks for [`hubeau-data`](https://pypi.org/project/hubeau-data/), installed from PyPI.\
Goal: exercise the client in real conditions, surface friction points back into `hubeau-data`.

## Setup

```bash
uv sync
uv run jupyter lab
```

> Jupyter runs on a remote server? Use an SSH tunnel:
>
> ```bash
> # on the server
> uv run jupyter lab --no-browser --port 8888
> # on your machine
> ssh -L 8888:localhost:8888 user@server -p <port> -N
> ```
>
> Then open `http://localhost:8888` in your browser.

## Notebooks

| Notebook | Description |
|---|---|
| `01_quickstart.ipynb` | First API call — health check, real-time flow rate observations, pandas + matplotlib |
| `02_async_bulk_ingest.ipynb` | Concurrent fetch via `asyncio.gather` → SQLite ingestion, multi-station plot |
| `03_health_dashboard.ipynb` | `check_health()` across all 11 APIs — latency heatmap, healthy ratio |
| `04_data_coverage_explorer.ipynb` | `data_coverage()` across all 11 APIs — data freshness and record volume |

## Scripts

| Script | Description |
|---|---|
| `scripts/hydrometrie/bulk_ingest.py` | Async bulk fetch for department 64 stations → SQLite |
| `scripts/smoke_test.py` | Minimal real-API checks — run before bumping `hubeau-data` version |

## Data

`data/` is gitignored except small sample files. SQLite databases are generated locally by the scripts.

## Known limitations

- `data_coverage()` results for hydrometric APIs mix metropolitan France and overseas departments (DOM).
  Aggregate freshness figures should be interpreted with caution until a dedicated metropole/DOM
  comparison is available (see Roadmap).
- `data_coverage()` does not return a `latest` date for `qualite_rivieres`, `piezometrie`,
  `temperature`, and `ecoulement` — these APIs may use a different date field name in their response.

## Roadmap

- [ ] `05_metropole_vs_dom.ipynb` — compare data availability and freshness between metropolitan
  France and overseas departments across hydrometric APIs
- [ ] Extend smoke test to cover all 11 APIs
- [ ] Audit query parameter names across remaining APIs (follow-up to the `code_entite` fix in
  `hubeau-data` 0.1.0)
