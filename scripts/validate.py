#!/usr/bin/env python3
"""Validate committed source data against the repo schema contracts.

Checks every ``data/<source>-<source_version>/`` folder:

- ``metadata.json`` validates against ``schema/metadata.schema.json`` and its
  ``row_counts`` match the actual parquet row counts;
- ``processes.parquet`` / ``exchanges.parquet`` conform to
  ``schema/process.yaml`` / ``schema/exchange.yaml``: no unknown columns,
  required columns present and non-null, column types match, enum columns only
  hold allowed values;
- ``processes.process_id`` is unique per folder and every
  ``exchanges.process_id`` resolves to a process in the same folder;
- ``processes.source`` and ``processes.source_version`` each hold exactly one value,
  equal to ``metadata.json`` ``source`` / ``source_version``, and the folder is named
  ``<source>-<source_version>``;
- the distinct ``processes.sector`` values equal ``metadata.json`` ``sectors`` (both
  directions), so consumers can select folders by metadata without opening parquet.

Columns declared optional may be omitted entirely. A column whose values are
all null passes the type check regardless of its physical type (an all-null
column carries no typed values to disagree with the contract).

Run from the repo root: ``python scripts/validate.py``.
Exits non-zero listing every violation found.
"""

import json
import sys
from pathlib import Path

import jsonschema
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schema"
DATA_DIR = ROOT / "data"

# schema type -> acceptable pyarrow type names
TYPE_MAP = {
    "string": {"string", "large_string"},
    "double": {"double", "float"},
    "int": {"int64", "int32", "int16", "int8"},
    "date": {"date32[day]", "date64[ms]", "timestamp[ms]", "timestamp[us]", "timestamp[ns]"},
}


def load_table_schema(name):
    spec = yaml.safe_load((SCHEMA_DIR / name).read_text())
    return {col["name"]: col for col in spec["columns"]}


def validate_table(folder, table_name, columns, enums, errors):
    path = folder / f"{table_name}.parquet"
    label = f"{folder.name}/{path.name}"
    if not path.exists():
        errors.append(f"{label}: file missing")
        return None
    table = pq.read_table(path)

    unknown = set(table.column_names) - set(columns)
    if unknown:
        errors.append(f"{label}: unknown columns {sorted(unknown)}")

    for name, col in columns.items():
        if name not in table.column_names:
            if col.get("required"):
                errors.append(f"{label}: required column '{name}' missing")
            continue
        data = table[name]
        nulls = data.null_count
        if col.get("required") and nulls:
            errors.append(f"{label}: required column '{name}' has {nulls} nulls")
        if nulls == len(data):
            continue  # all-null: no typed values to check
        expected = TYPE_MAP.get(col["type"]) if col["type"] != "enum" else TYPE_MAP["string"]
        if expected and str(data.type) not in expected:
            errors.append(f"{label}: column '{name}' is {data.type}, expected {col['type']}")
        if col["type"] == "enum":
            allowed = set(enums[col["enum"]])
            seen = set(pc.drop_null(data.combine_chunks()).unique().to_pylist())
            bad = seen - allowed
            if bad:
                errors.append(f"{label}: column '{name}' has values outside enum {col['enum']}: {sorted(bad)}")
    return table


def validate_folder(folder, process_cols, exchange_cols, enums, metadata_schema, errors):
    meta_path = folder / "metadata.json"
    if not meta_path.exists():
        errors.append(f"{folder.name}: metadata.json missing")
        meta = {}
    else:
        meta = json.loads(meta_path.read_text())
        try:
            jsonschema.validate(meta, metadata_schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{folder.name}/metadata.json: {exc.message}")

    processes = validate_table(folder, "processes", process_cols, enums, errors)
    exchanges = validate_table(folder, "exchanges", exchange_cols, enums, errors)

    for name, table in (("processes", processes), ("exchanges", exchanges)):
        declared = meta.get("row_counts", {}).get(f"{name}.parquet")
        if table is not None and declared is not None and declared != len(table):
            errors.append(
                f"{folder.name}/metadata.json: row_counts says {name}.parquet has "
                f"{declared} rows, actual {len(table)}"
            )

    if processes is not None and "process_id" in processes.column_names:
        ids = processes["process_id"]
        n_unique = len(pc.drop_null(ids.combine_chunks()).unique())
        if n_unique != len(ids):
            errors.append(f"{folder.name}/processes.parquet: process_id not unique")
        if exchanges is not None and "process_id" in exchanges.column_names:
            known = set(ids.to_pylist())
            referenced = set(pc.drop_null(exchanges["process_id"].combine_chunks()).unique().to_pylist())
            orphans = referenced - known
            if orphans:
                errors.append(
                    f"{folder.name}/exchanges.parquet: {len(orphans)} process_id values "
                    f"with no process row (e.g. {sorted(orphans)[:3]})"
                )

    if processes is not None:
        validate_source_identity(folder, processes, meta, errors)
        if "sector" in processes.column_names and "sectors" in meta:
            validate_sectors(folder, processes["sector"], meta["sectors"], errors)


def _distinct(column):
    return set(pc.drop_null(column.combine_chunks()).unique().to_pylist())


def validate_source_identity(folder, processes, meta, errors):
    """One source and one version per folder, agreeing with metadata and the folder name."""
    for key in ("source", "source_version"):
        if key not in processes.column_names:
            continue
        seen = _distinct(processes[key])
        if len(seen) != 1:
            errors.append(
                f"{folder.name}/processes.parquet: expected exactly one {key} value, "
                f"found {sorted(seen)}"
            )
        declared = meta.get(key)
        if declared is not None and seen != {declared}:
            errors.append(
                f"{folder.name}/processes.parquet: {key} values {sorted(seen)} differ from "
                f"metadata.json {key} {declared!r}"
            )
    if "source" in meta and "source_version" in meta:
        expected = f"{meta['source']}-{meta['source_version']}"
        if folder.name != expected:
            errors.append(
                f"{folder.name}/metadata.json: folder should be named {expected!r} "
                f"(<source>-<source_version>)"
            )


def validate_sectors(folder, sector_column, declared, errors):
    """``metadata.json`` ``sectors`` must equal the distinct ``processes.sector`` values."""
    seen = _distinct(sector_column)
    declared = set(declared)
    undeclared = seen - declared
    if undeclared:
        errors.append(
            f"{folder.name}/processes.parquet: sector values not declared in "
            f"metadata.json sectors: {sorted(undeclared)}"
        )
    absent = declared - seen
    if absent:
        errors.append(
            f"{folder.name}/metadata.json: sectors declared but absent from "
            f"processes.parquet: {sorted(absent)}"
        )


def main():
    process_cols = load_table_schema("process.yaml")
    exchange_cols = load_table_schema("exchange.yaml")
    enums = yaml.safe_load((SCHEMA_DIR / "common.yaml").read_text())["enums"]
    metadata_schema = json.loads((SCHEMA_DIR / "metadata.schema.json").read_text())

    folders = sorted(p for p in DATA_DIR.iterdir() if p.is_dir())
    if not folders:
        print("No source folders under data/ — nothing to validate.")
        return 0

    errors = []
    for folder in folders:
        validate_folder(folder, process_cols, exchange_cols, enums, metadata_schema, errors)

    if errors:
        print(f"FAIL — {len(errors)} violation(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK — {len(folders)} source folder(s) validate against the schema contracts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
