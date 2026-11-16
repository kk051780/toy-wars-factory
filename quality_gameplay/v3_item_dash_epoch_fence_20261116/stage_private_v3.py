#!/usr/bin/env python3
"""Read-only source-exact original 21 -> private 22 Rojo stage; NEVER official RC."""
import argparse
import hashlib
import json
from pathlib import Path

from compose_dash import AUTHOR_BLOB, AUTHOR_PATH, compose, git_blob_sha

BASE = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")
PROJECT = BASE / "EGGRUMBLE_V3_STUDIO.project.json"
PROJECT_BLOB = "1d3e5bdc9ac2ac3fb6e70110ff3c6636d70fc714"


def stage(destination: Path, enabled: bool) -> dict:
    if git_blob_sha(PROJECT.read_bytes()) != PROJECT_BLOB:
        raise ValueError("author V3 Rojo project changed")
    project = json.loads(PROJECT.read_text())
    copied = {}
    target_src = destination / "src"
    target_src.mkdir(parents=True, exist_ok=True)

    def visit(node: dict):
        for key, value in node.items():
            if not isinstance(value, dict):
                continue
            if "$path" in value:
                rel = value["$path"]
                origin = BASE / rel
                raw = origin.read_bytes()
                if rel == "EGGRUMBLE_FieldItemPickups.luau":
                    if git_blob_sha(raw) != AUTHOR_BLOB:
                        raise ValueError("ITEM original blob mismatch")
                    raw = compose(raw, enabled)
                (target_src / Path(rel).name).write_bytes(raw)
                copied[key] = {
                    "filename": Path(rel).name,
                    "class": "LocalScript" if rel.endswith(".client.luau") else ("Script" if rel.endswith(".server.luau") else "ModuleScript"),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "author_original": git_blob_sha(origin.read_bytes()),
                }
                value["$path"] = "src/" + Path(rel).name
            else:
                visit(value)
    visit(project["tree"])
    if len(copied) != 21:
        raise AssertionError(f"source-exact original project expected 21 files, saw {len(copied)}")
    if enabled:
        name = "EGGRUMBLE_DashLease"
        rel = name + ".luau"
        original = Path(__file__).resolve().parent / rel
        raw = original.read_bytes()
        (target_src / rel).write_bytes(raw)
        project["tree"]["ServerScriptService"][name] = {"$path": "src/" + rel}
        copied[name] = {"filename":rel, "class":"ModuleScript", "sha256":hashlib.sha256(raw).hexdigest(), "author_original":None}
    if len(copied) != (22 if enabled else 21):
        raise AssertionError("incorrect private source cardinality")
    (destination / "private_v3.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2) + "\n")
    receipt = {"enabled":enabled,"source_count":len(copied),"original_project_blob":PROJECT_BLOB,
        "original_item_blob":AUTHOR_BLOB,"scripts":copied,"formal_rc":False,"studio_tested":False}
    (destination / "source_lock_receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    p.add_argument("--enabled",action="store_true")
    args=p.parse_args()
    result=stage(Path(args.out),args.enabled)
    print(f"GQ_DASH_PRIVATE_STAGE_PASS on={args.enabled} scripts={result['source_count']}")
