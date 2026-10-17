#!/usr/bin/env python3
"""Offline, deterministic, fail-closed index build for ASTRA R6 GitHub batches.

Only normalized game-world facts enter the public knowledge index. Any malformed
or conflicting batch fails the workflow. No installed Python dependencies.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import pathlib
import re

KINDS = {"NPC", "LOC", "GROUND", "EDGE", "UI_SCHEMA"}
SAFE_TEXT = re.compile(r"^[A-Za-z0-9 .'()_=;,-]{0,120}$")


def validate(record: dict) -> dict:
    if not isinstance(record, dict) or set(record) != {
        "key", "kind", "id", "x", "y", "plane", "name", "detail", "client_profile"
    }:
        raise ValueError("Invalid record fields")
    kind = record["kind"]
    if kind not in KINDS:
        raise ValueError("Invalid kind")
    for field, lower, upper in (
        ("id", 0, 10000000), ("x", 0, 65535), ("y", 0, 65535),
        ("plane", -1, 3)
    ):
        value = record[field]
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"Invalid {field}")
    for field, maximum in (("name", 80), ("detail", 120), ("client_profile", 80)):
        value = record[field]
        if type(value) is not str or len(value) > maximum or not SAFE_TEXT.fullmatch(value):
            raise ValueError(f"Invalid {field}")
    if (kind == "UI_SCHEMA") != (record["plane"] == -1):
        raise ValueError("UI records must use plane=-1 and world records must not")
    canonical = "|".join(str(record[field]) for field in (
        "kind", "id", "x", "y", "plane", "name", "detail", "client_profile"
    ))
    actual = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if record["key"] != actual:
        raise ValueError("Bad SHA-256 record key")
    return record


def merge(root: pathlib.Path) -> tuple[int, dict[str, int]]:
    batches = root / "data" / "v1" / "batches"
    registry = {}
    for path in sorted(batches.glob("*/*.json")):
        if path.stat().st_size > 128 * 1024:
            raise ValueError(f"Batch too large: {path}")
        doc = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(doc, dict) or set(doc) != {"schema", "format", "records"}
                or doc["schema"] != 1 or doc["format"] != "astra-world-observations"
                or not isinstance(doc["records"], list)
                or len(doc["records"]) > 80):
            raise ValueError(f"Invalid batch schema: {path}")
        normalized = [validate(row) for row in doc["records"]]
        digests = sorted(item["key"] for item in normalized)
        digest = hashlib.sha256(("".join(k + "\n" for k in digests)).encode()).hexdigest()
        if path.relative_to(batches).as_posix() != f"{digest[:2]}/{digest}.json":
            raise ValueError(f"Incorrect batch fingerprint: {path}")
        for entry in normalized:
            key = entry["key"]
            if key in registry and registry[key] != entry:
                raise ValueError("Record key collision / conflicting content")
            registry[key] = entry

    knowledge = root / "knowledge"
    knowledge.mkdir(parents=True, exist_ok=True)
    ordered = sorted(registry.values(), key=lambda row: (
        row["kind"], row["plane"], row["x"] // 64,
        row["y"] // 64, row["x"], row["y"], row["id"], row["key"]))
    output = knowledge / "world-v1.jsonl"
    output.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":"))
                              + "\n" for r in ordered), encoding="utf-8")
    count = dict(sorted(collections.Counter(r["kind"] for r in ordered).items()))
    (knowledge / "manifest.json").write_text(
        json.dumps({"schema": 1, "records": len(ordered), "kinds": count},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return len(ordered), count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    total, count = merge(pathlib.Path(args.root))
    print(f"Indexed {total} observations: {count}")


if __name__ == "__main__":
    main()
