# schema/

Plain-YAML definitions of the parquet tables in `../data/`. Each file maps to one
parquet artifact and lists its columns (`name`, `type`, `required`,
`description`). LinkML is used **only** in `sentier-vocab`; the Data Layer's
parquet repos describe columns directly.

| file | describes |
|---|---|
| `common.yaml` | shared enums (`flow_direction`, `flow_type`, `process_type`, `sector`) |
| `process.yaml` | `processes.parquet` |
| `exchange.yaml` | `exchanges.parquet` |
| `metadata.schema.json` | JSON Schema for each source folder's `metadata.json` |

Column types: `string` · `double` · `int` · `date` · `enum` (enum values live in
`common.yaml`). `processes.parquet` is the parent; `exchanges.parquet` joins on
`process_id`.
