#!/usr/bin/env python3
"""Independently verify every actual Rojo .rbxlx executable source against 21 mapped files."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from compose_private21 import PROJECT, mapped_paths


def verify(project_dir: Path, place: Path):
    project = json.loads((project_dir / PROJECT).read_text("utf-8"))
    expected = mapped_paths(project["tree"])
    assert len(expected) == 21
    def script_class(path: str) -> str:
        return ("Script" if path.endswith(".server.luau") else
                "LocalScript" if path.endswith(".client.luau") else "ModuleScript")
    root = ET.fromstring(place.read_bytes())
    observed = {}
    for item in root.iter("Item"):
        cls = item.attrib.get("class")
        if cls not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        if props is None:
            raise AssertionError("script without properties")
        name = props.findtext("string[@name='Name']")
        code = props.findtext("ProtectedString[@name='Source']")
        if code is None:
            code = props.findtext("string[@name='Source']")
        assert name and code is not None, f"missing executable name/source: {name}"
        assert name not in observed, f"duplicated executable source: {name}"
        observed[name] = (cls, code.replace("\r\n", "\n"))
    assert len(observed) == 21, f"expected actual source21 not {len(observed)}"
    assert set(expected) == set(observed), f"source map drift: {set(expected)^set(observed)}"
    for name, rel in expected.items():
        cls, code = observed[name]
        assert cls == script_class(rel), (name, cls, script_class(rel))
        wanted = (project_dir / rel).read_text("utf-8").replace("\r\n", "\n")
        assert code == wanted, f"binary source mismatch: {name}"
    assert sum(cls == "Script" for cls, _ in observed.values()) == 1
    assert sum(cls == "LocalScript" for cls, _ in observed.values()) == 2
    assert sum(cls == "ModuleScript" for cls, _ in observed.values()) == 18
    return {"actual_place_bytes": place.stat().st_size,
            "actual_place_sha256": hashlib.sha256(place.read_bytes()).hexdigest(),
            "actual_embedded_sources_exact": len(observed),
            "original_sources_unchanged": 20, "original_boss_generated_overlay": 1,
            "official_rc": "NOT_INTEGRATED",
            "studio_engine": "NOT_RUN", "android": "NOT_RUN", "owner_accepted": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--place", type=Path, required=True)
    args = parser.parse_args()
    receipt = verify(args.project_dir, args.place)
    (args.project_dir / "place_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", "utf-8"
    )
    print("GQ_PRIVATE21_TRUE_ROJO_SOURCE_CLASS_EXACT_PASS 21/21")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
