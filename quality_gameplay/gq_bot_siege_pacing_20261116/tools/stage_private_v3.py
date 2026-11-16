#!/usr/bin/env python3
"""Source-selective private V3 composition; never writes upstream or official RC."""
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
UPSTREAM = REPO / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
OWN = REPO / "quality_gameplay/gq_bot_siege_pacing_20261116"
AUTHOR_BOT_BLOB = "fa38f24a26a619238e4c6a62b3ee582dc14cfe7a"
OLD_REQUIRE = 'local Router=require(script.Parent:WaitForChild("EGGRUMBLE_BotPathRouter"))'
NEW_REQUIRE = OLD_REQUIRE + '\nlocal SiegePacing=require(script.Parent:WaitForChild("EGGRUMBLE_SiegePacing"))'
OLD_GATE = 'elseif now-(lastSiege[id] or 0)>=SIEGE_INTERVAL then'
NEW_GATE = ('elseif now-(lastSiege[id] or 0)>=SIEGE_INTERVAL '
            'and SiegePacing.allow(session,enemy.id,id,now) then')


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(("blob " + str(len(raw))).encode() + bytes([0]) + raw).hexdigest()


def stage(output: Path) -> dict:
    original_project = json.loads((UPSTREAM / "EGGRUMBLE_V3_STUDIO.project.json").read_text())
    project = json.loads(json.dumps(original_project))
    source_entries = []

    def remap(node):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            path = node["$path"]
            if "/" in path or not path.endswith(".luau"):
                raise ValueError(f"unexpected author project path: {path}")
            source_entries.append(path)
            node["$path"] = "src/" + path
        for child in node.values():
            remap(child)

    remap(project)
    if len(source_entries) != 21 or len(set(source_entries)) != 21:
        raise ValueError(f"source manifest drift: {len(source_entries)} not exact 21")
    source_dir = output / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    original_hashes = {}
    staged_hashes = {}
    for name in source_entries:
        raw = (UPSTREAM / name).read_bytes()
        original_hashes[name] = sha256(raw)
        if name == "EGGRUMBLE_BotActors.luau":
            if git_blob(raw) != AUTHOR_BOT_BLOB:
                raise ValueError("original BotActors source SHA mismatch; re-CLAIM before patch")
            text = raw.decode("utf-8")
            for old in [OLD_REQUIRE, OLD_GATE]:
                if text.count(old) != 1:
                    raise ValueError("author anchor drift: " + old)
            text = text.replace(OLD_REQUIRE, NEW_REQUIRE).replace(OLD_GATE, NEW_GATE)
            raw = text.encode("utf-8")
        (source_dir / name).write_bytes(raw)
        staged_hashes[name] = sha256(raw)

    module = (OWN / "EGGRUMBLE_BotSiegePacing.luau").read_bytes()
    (source_dir / "EGGRUMBLE_SiegePacing.luau").write_bytes(module)
    project["tree"]["ServerScriptService"]["EGGRUMBLE_SiegePacing"] = {
        "$path": "src/EGGRUMBLE_SiegePacing.luau"
    }
    (output / "private_v3.project.json").write_text(
        json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "status": "PRIVATE_SOURCE_CANDIDATE_NOT_RC",
        "original_author_ref": "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
        "original_bot_blob": AUTHOR_BOT_BLOB,
        "upstream_sources": 21,
        "staged_sources": 22,
        "original_sha256": original_hashes,
        "staged_sha256": staged_hashes,
        "one_modified_original": "EGGRUMBLE_BotActors.luau",
        "one_new_module": "EGGRUMBLE_SiegePacing.luau",
        "module_sha256": sha256(module),
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "official_rc": "NOT_INTEGRATED",
    }
    (output / "source_lock.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    manifest = stage(Path(args.out).resolve())
    print("PRIVATE_V3_SOURCE_EXACT_READY", manifest["staged_sources"],
          "original 20 exact + 1 minimal patched + 1 new. NO OFFICIAL RC.")


if __name__ == "__main__":
    main()
