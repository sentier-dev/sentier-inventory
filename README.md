# sentier-inventory

Standardized **life cycle inventory** datasets for the Sentier platform —
processes and their exchanges. A **Data Layer** repo: it holds loadable
artifacts only, no fetch/parse/calculate code.

- **Fed by:** `sentier-importers` (PR / Push) and `sentier-models`.
- **Read by:** `sentier-platform` (GET LCI matrices).
- **Cross-source links** (technosphere, elementary flows) resolve via
  `sentier-mappings`.

## Layout

```
schema/   # YAML column definitions + JSON Schema for metadata
data/     # raw parquet, one subfolder per sector / data type (ranked)
```

## Data

Organized **by sector / data type** (`agriculture`, `electricity`, …) only. Which
upstream source supplied which rows is **not** recorded here — that import log
lives in `sentier-importers`. Each `data/<NN>-<sector>/` folder holds:

| file | rows |
|---|---|
| `processes.parquet` | one per process (activity / node) |
| `exchanges.parquet` | one per exchange (technosphere + biosphere edges) |
| `metadata.json` | sector identity (sector, title, rank, row counts) |

The `NN` rank prefix orders sectors and sets resolution precedence (lower wins).
Parquet payloads are pushed by the Application Layer — the skeleton ships only
folder structure, schemas, and `metadata.json` stubs.

## Schema

Plain-YAML table definitions (`schema/process.yaml`, `schema/exchange.yaml`,
shared enums in `schema/common.yaml`). LinkML is used only in `sentier-vocab`;
here schemas describe parquet columns directly.

These files are the **contract**, not code. `sentier-importers` reads them to
validate and cast incoming data before delivering parquet here. This repo ships
no Python package, loader, or tests — all ingestion logic lives in the importer,
the read side in `sentier-platform`.

## License

MIT — open by default, client-loadable.
