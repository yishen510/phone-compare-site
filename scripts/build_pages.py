#!/usr/bin/env python3
"""Build a minimal GitHub Pages artifact and fail closed on catalog/gate issues."""
from __future__ import annotations
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"


def main() -> None:
    catalog_path = ROOT / "data" / "phones.json"
    if not catalog_path.is_file():
        raise SystemExit("FAIL: data/phones.json missing")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, list) or not catalog:
        raise SystemExit("FAIL: catalog must be a non-empty JSON array")
    for name in ("index.html", "phone-compare-demo.html"):
        path = ROOT / name
        if not path.is_file():
            raise SystemExit(f"FAIL: {name} missing")
        source = path.read_text(encoding="utf-8")
        if "<html" not in source.lower() or "</html>" not in source.lower():
            raise SystemExit(f"FAIL: {name} does not look like a complete HTML document")
        if "PHONE_DATA" not in source:
            raise SystemExit(f"FAIL: {name} does not contain embedded PHONE_DATA")
    # Keep private QA data, scripts, API notes and source JSON out of the public artifact.
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name in ("index.html", "phone-compare-demo.html", "api-config.js"):
        path = ROOT / name
        if not path.is_file():
            raise SystemExit(f"FAIL: {name} missing")
        shutil.copy2(path, OUT / name)
    # Pages serves index.html at the project root; no API keys or raw audit files are copied.
    print(f"PASS: catalog={len(catalog)}; artifact files={sorted(p.name for p in OUT.iterdir())}")


if __name__ == "__main__":
    main()
