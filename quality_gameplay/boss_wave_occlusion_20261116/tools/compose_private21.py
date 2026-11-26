#!/usr/bin/env python3
"""Build scratch 21-source project reusing the entire pinned #482 V3 author roster."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from compose_patch import ORIGINAL_COMMIT, ORIGINAL_BLOB, git_blob_sha, patch_bytes

PROJECT = "EGGRUMBLE_V3_STUDIO.project.json"
BOSS = "EGGRUMBLE_NeutralStoneGiant.luau"


def mapped_paths(node: dict) -> dict[str, str]:
    result = {}
    def visit(part: dict, location: tuple[str, ...] = ()):
        for name, child in part.items():
            if name.startswith("$") or not isinstance(child, dict):
                continue
            key = location + (name,)
            if "$path" in child:
                assert key[-1] not in result, ("duplicate source name", name)
                result[key[-1]] = child["$path"]
            else:
                visit(child, key)
    visit(node)
    return result


def compose(original: Path, scratch: Path) -> dict:
    info = json.loads((original / PROJECT).read_text("utf-8"))
    refs = mapped_paths(info["tree"])
    assert len(refs) == 21, f"expected original author 21 mapped scripts, not {len(refs)}"
    assert refs.get("EGGRUMBLE_NeutralStoneGiant") == BOSS
    assert refs.get("EGGRUMBLE_LobbyCastleModesPreview") == "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    assert all(".." not in Path(rel).parts and not Path(rel).is_absolute() for rel in refs.values())
    assert len(set(refs.values())) == 21
    scratch.mkdir(parents=True, exist_ok=True)
    receipts = {}
    for name, rel in sorted(refs.items()):
        origin = original / rel
        raw = origin.read_bytes()
        expected = git_blob_sha(raw)
        if rel == BOSS:
            assert expected == ORIGINAL_BLOB, "boss original drift"
            changed = patch_bytes(raw)
        else:
            changed = raw
        destination = scratch / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(changed)
        receipts[name] = {
            "path": rel,
            "author_git_blob": expected,
            "selected_sha256": hashlib.sha256(changed).hexdigest(),
            "amended": rel == BOSS,
        }
    (scratch / PROJECT).write_bytes((original / PROJECT).read_bytes())
    assert sum(x["amended"] for x in receipts.values()) == 1
    output = {
        "schema": "GQ_BOSS_WAVE_ORIGINAL21_SOURCE_EXACT_V1",
        "author_commit": ORIGINAL_COMMIT,
        "author_script_count": 21,
        "original_scripts_unchanged": 20,
        "selected_modified_original_script": BOSS,
        "scope": "one original boss shockwave LOS only",
        "studio_play": "NOT_RUN",
        "android": "NOT_RUN",
        "official_rc_adopted": False,
        "owner_accepted": False,
        "script_sources": receipts,
    }
    (scratch / "source_receipt.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = compose(args.original, args.output)
    print(f"GQ_PRIVATE21_SELECTIVE_COMPOSE_PASS {len(receipt['script_sources'])}/21; original 20 unchanged")
    print("Source only; no RC/Studio/Android/OWNER acceptance")


if __name__ == "__main__":
    main()
