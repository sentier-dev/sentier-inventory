# data/

Raw **parquet** inventory artifacts, **one subfolder per published release of one
datasource**:

```
data/
  bafu-2026-v1/   # BAFU:2026 v1 LCI database
```

Convention: `data/<source>-<source_version>/`, where `<source>` is the lower-kebab
datasource id `<publisher>-<edition>` and `<source_version>` is the publisher's release.
A folder holds exactly one source and one version. A delivery from `sentier-importers`
replaces the folder whole; sources never share a file, so nothing is ever merged. A
re-release is a new folder; the PR that adds it removes the old one unless both are meant
to be served.

Inventory is organized by **source**, with the **sector as a column**. Every process
row carries `source`, `source_version` and `sector` (enum in `../schema/common.yaml`:
`agriculture`, `electricity`, `chemicals`, `transport`, `energy`, `waste`,
`construction`, `materials`, `electronics`, `building-services`, `obsolete`). Each
folder's `metadata.json` carries the publisher, licence, required citation, the
`sectors` present and the row counts, so a consumer can pick a folder from metadata
alone and filter rows by sector. Within one source there is no precedence rule;
between sources the consumer chooses. The import log of which upstream file produced
which rows stays in `sentier-importers`.

### Source ids

`source` is a lower-kebab datasource id, `<publisher>-<edition>`, matching the
vocab Source IRI slug (`https://vocab.sentier.dev/sources/<source>`) and the
sentier-mappings pair-folder prefix. The publisher's release goes in
`source_version`, never in the id, so a re-release does not rename the database a
consumer's project depends on.

| datasource | `source` | `source_version` | folder |
|---|---|---|---|
| BAFU:2026 v1 LCI database | `bafu-2026` | `v1` | `bafu-2026-v1/` |

> Background datasets that exist only as link targets (e.g. ecoinvent) are not a
> source here; they are resolved through `sentier-mappings`, not stored as a folder.

Each folder holds `processes.parquet`, `exchanges.parquet`, and `metadata.json`.
See [../schema/](../schema/) for column definitions.
