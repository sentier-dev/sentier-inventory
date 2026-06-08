# data/

Raw **parquet** inventory artifacts, **one subfolder per sector / data type**,
ranked by a numeric prefix:

```
data/
  01-agriculture/   # rank 1 — highest resolution precedence
  02-electricity/   # Brightcon deliverable
  03-chemicals/     # chemicals & materials
```

Convention: `data/<NN>-<sector>/`, where `<sector>` is a lower-kebab sector /
data-type id (`agriculture`, `electricity`, `chemicals`) and `<NN>` sets folder
ordering / resolution precedence (lower wins when records overlap).

Inventory is organized by **sector, not by datasource**. Upstream sources
(BAFU, Agribalyse, …) each span many sectors, so the source is deliberately *not*
recorded in this repo — `sentier-importers` keeps the import log of which source
supplied which rows. This repo holds only the harmonized, sector-organized
result.

> Background datasets that exist only as link targets (e.g. ecoinvent) are not a
> sector; they are resolved through `sentier-mappings`, not stored here as their
> own folder.

Each folder holds `processes.parquet`, `exchanges.parquet`, and `metadata.json`.
See [../schema/](../schema/) for column definitions. Parquet payloads are pushed
by `sentier-importers` / `sentier-models`; the skeleton ships `.gitkeep` +
`metadata.json` stubs only.
