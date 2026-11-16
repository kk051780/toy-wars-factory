#!/usr/bin/env python3
"""Append ONLY #514's two optional scripts to #484's original 26-source product.
Do not reimplement #484's composer, original GAME/ART/SCORE, or any shared authority.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWNED = {
    "EGGRUMBLE_BossCreditPolicy": HERE / "EGGRUMBLE_BossCreditPolicy.luau",
    "EGGRUMBLE_BossCreditRoundFence": HERE / "EGGRUMBLE_BossCreditRoundFence.server.luau",
}

def scripts(data):
    tree = data["tree"]
    server = tree["ServerScriptService"]
    client = tree["StarterPlayer"]["StarterPlayerScripts"]
    return server, client

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = args.original.resolve(strict=True)
    output = args.out.resolve()
    assert output.parent.is_dir()
    assert output.parent == original.parent and output != original, "keep author and extension in same artifacts folder"
    authored = json.loads(original.read_text(encoding="utf-8"))
    original_server, original_client = scripts(authored)
    assert len(original_server)-1 == 23 and len(original_client)-1 == 3, "author 26 layout drift"
    for k in OWNED:
        assert k not in original_server, "author owns our script: stop and reconcile"
    manifest = copy.deepcopy(authored)
    new_server, new_client = scripts(manifest)
    for name, source in OWNED.items():
        assert source.is_file()
        new_server[name] = {"$path": os.path.relpath(source, output.parent).replace(os.sep, "/")}
    assert len(new_server)-1 == 25 and len(new_client)-1 == 3
    for name, node in original_server.items():
        assert new_server[name] == node, ("changed original server mapping", name)
    assert new_client == original_client, "changed original client mapping"
    manifest["name"] = "EGGRUMBLE_GQ_BOSS_CREDIT_CURRENT28_PRIVATE_NOT_RC"
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    expected = json.loads((original.parent / "SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
    original_hashes = expected["source_sha256"]
    assert len(original_hashes) == 26
    for service in (original_server, original_client):
        for name, entry in service.items():
            if name == "$className":
                continue
            source = (original.parent / entry["$path"]).resolve(strict=True)
            assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hashes[name], name
    print("CURRENT28_GQ_COMPOSE: ORIGINAL26_SOURCE_IDENTICAL_PLUS2")
if __name__ == "__main__":
    main()
