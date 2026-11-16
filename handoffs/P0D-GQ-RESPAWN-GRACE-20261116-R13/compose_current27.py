#!/usr/bin/env python3
"""Source-select R13 one-file protective Script onto ORIGINAL #484 26-script
real current Game+ART+SCORE composer output. PRIVATE / NO RC writes."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

NAME = "EGGRUMBLE_RespawnGrace"
OWN_PATH = Path(__file__).resolve().parent / "EGGRUMBLE_RespawnGrace.server.luau"


def files(project):
    parent = project.parent
    tree = json.loads(project.read_text(encoding="utf-8"))["tree"]
    def walk(node, parents):
        if isinstance(node, dict):
            if "$path" in node:
                assert set(node) == {"$path"}, (parents, node)
                yield parents, (parent / node["$path"]).resolve(strict=True)
            else:
                for name, item in node.items():
                    if not name.startswith("$"):
                        yield from walk(item, parents + (name,))
    yield from walk(tree, ())


def build(base, receipt_path, out):
    base = base.resolve(strict=True)
    receipt_path = receipt_path.resolve(strict=True)
    out = out.resolve()
    assert base != out and out.parent.is_dir()
    assert OWN_PATH.exists() and OWN_PATH.name.endswith(".server.luau")
    assert OWN_PATH.read_text(encoding="utf-8").startswith("--!strict")

    data = json.loads(base.read_text(encoding="utf-8"))
    tree = data["tree"]
    server = tree["ServerScriptService"]
    client = tree["StarterPlayer"]["StarterPlayerScripts"]
    assert server["$className"] == "ServerScriptService"
    assert len(server) - 1 == 23 and len(client) - 1 == 3
    assert NAME not in server
    before = list(files(base))
    assert len(before) == 26
    names = {path[-1] for path, _ in before}
    assert len(names) == 26

    original_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert original_receipt["status"] == "SOURCE_ONLY_NOT_OFFICIAL_RC"
    originals = original_receipt["source_sha256"]
    assert names == originals.keys()
    for chain, file in before:
        assert hashlib.sha256(file.read_bytes()).hexdigest() == originals[chain[-1]], chain

    new_data = copy.deepcopy(data)
    new_data["name"] = "EGGRUMBLE_V3_CURRENT27_R13_PRIVATE_NO_PUBLISH"
    new_server = new_data["tree"]["ServerScriptService"]
    new_server[NAME] = {
        "$path": os.path.relpath(OWN_PATH, out.parent).replace(os.sep, "/")
    }
    out.write_text(json.dumps(new_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after = list(files(out))
    assert len(after) == 27 and len({chain[-1] for chain, _ in after}) == 27

    # Mandatory immutability: original 26 exact mapped source paths and SHA
    # remain byte-for-byte what the independent original composer emitted.
    for chain, old_file in before:
        expected = next(new_file for new_chain, new_file in after if new_chain == chain)
        assert expected == old_file
        assert hashlib.sha256(expected.read_bytes()).hexdigest() == originals[chain[-1]]

    assert new_server[NAME] == {
        "$path": os.path.relpath(OWN_PATH, out.parent).replace(os.sep, "/")
    }
    added = [src for chain, src in after if chain[-1] == NAME]
    assert added == [OWN_PATH]
    receipt = {
        "status": "PRIVATE_SOURCE_QA_27_NOT_OFFICIAL_RC",
        "source_count": 27,
        "unchanged_original_game_art_score": 26,
        "added_server_script": NAME,
        "author_26_manifest_sha256": hashlib.sha256(base.read_bytes()).hexdigest(),
        "author_26_original_source_sha256": originals,
        "additional_source_sha256": hashlib.sha256(OWN_PATH.read_bytes()).hexdigest(),
        "studio_play": "NOT_TESTED",
        "android": "NOT_TESTED",
        "owner_fun": "NO_GO",
        "official_rc_adopted": False,
        "source_sha256": {
            chain[-1]: hashlib.sha256(src.read_bytes()).hexdigest()
            for chain, src in after
        },
    }
    receipt_file = out.parent / "SOURCE_RECEIPT_R13_CURRENT27.json"
    receipt_file.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GQ_R13_CURRENT27_COMPOSE_FROM_AUTHOR26_PLUS_ONE_PASS", len(after))
    return out, receipt_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author26", required=True, type=Path)
    ap.add_argument("--receipt26", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    build(args.author26, args.receipt26, args.out)


if __name__ == "__main__":
    main()
