# sentier-inventory

## What it is

Standardized life cycle inventory (LCI) data for the Sentier platform.
Processes and their exchanges, stored as parquet. A Data Layer repo: artifacts only.

- Fed by `sentier-importers`, which opens PRs with validated parquet.
- Read by `sentier-brightway`, which loads every sector folder.
- Cross-source flow ids resolve via `sentier-mappings`.
- No Python package, no loader. The only code is the CI validator.

## Install

Nothing to install. Clone the repo and read the parquet files directly.

## Use

Validate all sector data against the schema contracts. This is what CI runs on every PR.

```bash
uv run --with "jsonschema[format],pyyaml,pyarrow" python scripts/validate.py
```

Inspect a delivered parquet payload.

```bash
uv run --with pandas,pyarrow python -c "import pandas as pd; print(pd.read_parquet('data/01-agriculture/processes.parquet'))"
```

## Layout

```
schema/                  # the data contract, read by sentier-importers
data/<NN>-<sector>/      # one folder per sector, ranked by NN
scripts/validate.py      # CI validator, self-contained
.github/workflows/ci.yml # runs scripts/validate.py on every PR and branch push
```

## Data

Inventory is organized by sector, not by source. Which source supplied which rows is logged in `sentier-importers`.

Each `data/<NN>-<sector>/` folder holds:

| file | rows |
|---|---|
| `processes.parquet` | one per process |
| `exchanges.parquet` | one per exchange (technosphere and biosphere edges) |
| `metadata.json` | sector, title, rank, schema_version, row_counts |

- The `NN` prefix orders sectors. Lower wins when records overlap.
- Sector ids are lower-kebab: `agriculture`, `electricity`, `chemicals`.
- Background link targets such as ecoinvent are not sectors. They resolve through `sentier-mappings`.
- Parquet is committed directly. No git-LFS, no release artifacts.

## Schema

Plain YAML. Each file lists the columns of one parquet table. LinkML is used only in `sentier-vocab`.

| file | describes |
|---|---|
| `schema/common.yaml` | shared enums: `flow_direction`, `flow_type`, `process_type` |
| `schema/process.yaml` | `processes.parquet`, primary key `process_id` |
| `schema/exchange.yaml` | `exchanges.parquet`, joins on `process_id` |
| `schema/metadata.schema.json` | JSON Schema for each sector's `metadata.json` |

CI checks columns, types, enums, `row_counts`, `process_id` uniqueness, and the exchange to process foreign key per sector.

## Contributing

Data changes arrive as PRs from `sentier-importers`, not by hand. Schema changes go through a PR here. CI must pass.

## License

MIT — open by default, client-loadable.
