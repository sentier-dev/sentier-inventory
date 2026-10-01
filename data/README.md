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
(BAFU, Agribalyse, …) each span many sectors, so a folder may hold rows from
several sources. Every process row is tagged with its `source` (and optional
`source_version`), and each folder's `metadata.json` lists the `sources` present,
so a consumer can pick folders by metadata and rows by column. Precedence between
folders is by rank; within a folder the consumer selects by `source` (there is no
intra-folder precedence rule). The import log of which upstream file produced
which rows stays in `sentier-importers`.

### Source ids

`source` is a lower-kebab datasource id, `<publisher>-<edition>`, matching the
vocab Source IRI slug (`https://vocab.sentier.dev/sources/<source>`) and the
sentier-mappings pair-folder prefix. The publisher's release goes in
`source_version`, never in the id, so a re-release does not rename the database a
consumer's project depends on.

| datasource | `source` | `source_version` |
|---|---|---|
| BAFU:2026 v1 LCI database | `bafu-2026` | `v1` |

> Background datasets that exist only as link targets (e.g. ecoinvent) are not a
> sector; they are resolved through `sentier-mappings`, not stored here as their
> own folder.

Each folder holds `processes.parquet`, `exchanges.parquet`, and `metadata.json`.
See [../schema/](../schema/) for column definitions. Parquet payloads are pushed
by `sentier-importers` / `sentier-models`; the skeleton ships `.gitkeep` +
`metadata.json` stubs only.
