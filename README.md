# sentier-inventory

## What it is

Standardized life cycle inventory (LCI) data for the Sentier platform.
Processes and their exchanges, stored as parquet. A Data Layer repo: artifacts only.

- Fed by `sentier-importers`, which opens PRs with validated parquet.
- Read by `sentier-brightway`, which loads one source folder into one Brightway database.
- Cross-source flow ids resolve via `sentier-mappings`.
- No Python package, no loader. The only code is the CI validator.

## Install

Nothing to install. Clone the repo and read the parquet files directly.

## Use

Validate all source folders against the schema contracts. This is what CI runs on every PR.

```bash
uv run --with "jsonschema[format],pyyaml,pyarrow" python scripts/validate.py
```

Inspect a delivered parquet payload.

```bash
uv run --with pandas,pyarrow python -c "import pandas as pd; print(pd.read_parquet('data/bafu-2026-v1/processes.parquet'))"
```

## Layout

```
schema/                  # the data contract, read by sentier-importers
data/<source>-<version>/ # one folder per published release of one datasource
scripts/validate.py      # CI validator, self-contained
.github/workflows/ci.yml # runs scripts/validate.py on every PR and branch push
```

## Data

Inventory is organized by source. One folder per published release of one datasource, named `<source>-<source_version>` (`bafu-2026-v1`). A delivery replaces its source folder whole; sources never share a file. Every process row carries `source`, `source_version` and `sector`, so a consumer picks a folder by its `metadata.json` and filters rows by sector. See [data/README.md](data/README.md) for the id convention.

Each `data/<source>-<source_version>/` folder holds:

| file | rows |
|---|---|
| `processes.parquet` | one per process |
| `exchanges.parquet` | one per exchange (technosphere and biosphere edges) |
| `metadata.json` | source, source_version, title, publisher, license, citation, schema_version, sectors, row_counts |

- Sector ids are lower-kebab enum values in `schema/common.yaml`: `agriculture`, `electricity`, `chemicals`, ...
- Background link targets such as ecoinvent are not sources here. They resolve through `sentier-mappings`.
- Parquet is committed directly. No git-LFS, no release artifacts.

## Schema

Plain YAML. Each file lists the columns of one parquet table. LinkML is used only in `sentier-vocab`.

| file | describes |
|---|---|
| `schema/common.yaml` | shared enums: `flow_direction`, `flow_type`, `process_type`, `sector` |
| `schema/process.yaml` | `processes.parquet`, primary key `process_id` |
| `schema/exchange.yaml` | `exchanges.parquet`, joins on `process_id` |
| `schema/metadata.schema.json` | JSON Schema for each source folder's `metadata.json` |

CI checks columns, types, enums, `row_counts`, `process_id` uniqueness, the exchange to process foreign key, one `source`/`source_version` per folder matching its name, and `sectors` against the column.

## Contributing

Data changes arrive as PRs from `sentier-importers`, not by hand. Schema changes go through a PR here. CI must pass.

## License

MIT — open by default, client-loadable.
