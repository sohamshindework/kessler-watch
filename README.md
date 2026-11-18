# ◎ Kessler Watch

An open space-traffic research dashboard: public catalogue ingestion, reproducible SGP4 close-approach screening, orbit consistency research and an interactive 3D globe.

**[Dashboard](https://sohamshindework.github.io/kessler-watch/) · [Methodology](docs/methodology.md) · [Research roadmap](docs/roadmap.md)**

This is a working research foundation for the accompanying 12-week proposal. It is not an operational traffic controller. The dashboard reports actual coverage and data freshness; it does not invent collision probabilities or AI improvements.

## Run locally

Requires Python 3.11+ and Node 22+.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
npm ci
npm run dev
```

The committed snapshot lets the website run immediately. Refresh it with:

```sh
# Download the active public catalogue, screen a bounded subset.
kessler-watch --group active --limit 500 --days 7
# All active objects research run; significantly more compute.
kessler-watch --group active --limit 0 --days 7 --step-seconds 60
# Reproduce with a saved OMM JSON catalogue, without network access.
kessler-watch --input catalogue.json --limit 100 --days 1
```

`--limit` selects the lowest NORAD IDs deterministically; this is not a representative risk sample. Broader OMM catalogues can be supplied with `--input`; the upstream `GROUP=all` endpoint is not valid. The globe displays all successfully propagated downloaded objects. Screened count and catalogue count are separate. A full-catalogue run is still sampled in time and **not exhaustive**.

## What works

- CelesTrak OMM JSON ingestion, validation and daily compressed immutable history.
- WGS72 SGP4 propagation in TEME; explicit failed propagation accounting.
- KD-tree candidate discovery and bounded closest-approach refinement, seven-day configurable horizon.
- Daily GitHub Actions refresh and GitHub Pages publication; CI tests and production build.
- 3D globe with client SGP4 propagation, forecast slider, rotation controls, searchable and sortable encounter inspector, snapshot export and mobile layout.
- Ridge baseline trained on public-element residual history with time + object holdout and honest RMSE, once enough history exists.
- Unvalidated manoeuvre discontinuity candidates and a labelled toy displacement lower bound.

## Automation and storage

`.github/workflows/daily.yml` runs at **04:23 UTC daily**, with a 90-minute timeout. It downloads `active`, screens 500 objects by default, archives the catalogue under `data/history/YYYY-MM-DD.json.gz`, evaluates research baselines and atomically updates `web/public/data/latest.json`. GitHub scheduling can be delayed and public-repository schedules may be disabled after inactivity. Failed ingestion leaves the last good snapshot unchanged; the dashboard marks snapshots older than 36 hours as stale.

`pages.yml` publishes on `main` pushes and after successful daily runs (Actions-token commits do not trigger push workflows). Enable **Settings → Pages → Source → GitHub Actions**. `Verify` runs the Python tests and esbuild production build on pushes and PRs.

History is gzip JSON to minimize the first-version dependency footprint. Long-running projects should migrate snapshots to Parquet / an external dataset store before repository history grows too large. No account, secrets, GPU or paid service is required. Free service limits and external data availability still apply.

## Verification

```sh
pytest -q
npm run build
```

The scientific test suite checks the published Vallado SGP4 reference vector, co-orbital encounter screening, snapshot immutability, invalid parameters and honest insufficient-history results.

## Limits

Public elements have unknown and correlated errors. No reliable covariance means no collision probability. A coarse grid can miss fast encounters outside the candidate radius, and only the nearest sampled neighbourhood per pair is refined. The displayed list is **closest in the screened sample**, not the world's riskiest objects. The ridge target is consistency with later fitted public elements, not actual position error. Manoeuvre labels are heuristic and unvalidated. The displacement estimate ignores orbital mechanics and is not a command or safe dodge plan.

GPU dSGP4 scaling, calibrated uncertainty, independent manoeuvre benchmark validation, constrained orbital dodge optimisation and a long-running public service remain research milestones. See [the roadmap](docs/roadmap.md).

## Data and attribution

[Public CelesTrak GP data](https://celestrak.org/NORAD/elements/) · [SGP4](https://pypi.org/project/sgp4/) · [satellite.js](https://github.com/shashwatak/satellite-js) · [Three.js](https://threejs.org/).

Respect CelesTrak's access policy. The updater requests one catalogue per run; do not aggressively poll. Software is MIT licensed; upstream data and dependency terms remain their own. Space-Track integration is intentionally omitted until the account owner accepts its agreement; never commit account credentials.
