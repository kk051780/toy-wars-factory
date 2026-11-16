#!/usr/bin/env python3
"""Source-selective ITEM-only overlay on #484 original 26-script composer output.

No new game/ART/SCORE/AI composer, no direct RC/merge/publish writes. Build a
private SOURCE-EXACT Place proof using the original composer and one #489 item.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ITEM_NAME = "EGGRUMBLE_FieldItemPickups"
EXPECTED = 26
GAME = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"


def scripts(manifest: Path):
    tree = json.loads(manifest.read_text(encoding="utf-8"))["tree"]
    def walk(node, chain):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            path = (manifest.parent / node["$path"]).resolve(strict=True)
            yield chain, path
        else:
            for name, child in node.items():
                if not name.startswith("$"):
                    yield from walk(child, chain + (name,))
    return list(walk(tree, ()))


def ids(manifest: Path):
    entries = scripts(manifest)
    assert len(entries) == EXPECTED, ("expected 26 sources", len(entries))
    out = {}
    for lineage, path in entries:
        key = lineage[-1]
        assert key not in out, ("duplicate module identity", key)
        assert lineage[0] in ("ServerScriptService", "StarterPlayer"), lineage
        out[key] = (lineage, path)
    assert ITEM_NAME in out
    assert out[ITEM_NAME][0] == ("ServerScriptService", ITEM_NAME)
    assert len(out) == EXPECTED
    return out


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(original: Path, output: Path, item: Path, receipt: Path,
            item_head: str, quality_head: str, author_head: str):
    before = ids(original)
    data = json.loads(original.read_text(encoding="utf-8"))
    old = before[ITEM_NAME][1]
    item = item.resolve(strict=True)
    assert item != old and item.name == "EGGRUMBLE_FieldItemPickups.luau"
    patched = item.read_text(encoding="utf-8")
    original_code = old.read_text(encoding="utf-8")
    assert patched != original_code, "forgot ITEM hunk: author's unmodified source"
    for required in (
        'function Items.start(session:any,positions:{Vector3}):()',
        'interactionGuard.allow(player,part,"拾う",part.Name)',
        'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end',
        'if not matchActive() or player.Character~=buffCharacter then return end',
        'task.delay(RESPAWN_SECONDS,function()',
    ):
        assert required in patched, ("quality item contract missing", required)
    assert original_code.endswith("return Items\n") or original_code.rstrip().endswith("return Items")
    assert patched.rstrip().endswith("return Items")
    output.parent.mkdir(parents=True, exist_ok=True)
    data["name"] = "EGGRUMBLE_GQ_ITEM26_PRIVATE_NONPUBLIC_NOT_OFFICIAL_RC"
    data["tree"]["ServerScriptService"][ITEM_NAME]["$path"] = os.path.relpath(
        item, output.parent).replace(os.sep, "/")
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after = ids(output)
    assert set(after) == set(before)
    assert len(after) == EXPECTED
    for name, (_, path) in before.items():
        if name != ITEM_NAME:
            assert after[name][1] == path, ("unowned source rewritten", name)
            assert sha(after[name][1]) == sha(path)
    assert after[ITEM_NAME][1] == item
    provenance = json.loads(receipt.read_text(encoding="utf-8"))
    assert provenance["script_count"] == EXPECTED
    assert set(provenance["source_sha256"]) == set(after)
    for name, (_, path) in before.items():
        assert provenance["source_sha256"][name] == sha(path), ("upstream receipt changed", name)
    provenance["source_sha256"][ITEM_NAME] = sha(item)
    provenance.update({
        "status": "PRIVATE_ITEM26_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "item_original_sha256": sha(old),
        "item_gq_sha256": sha(item),
        "item_gq_commit": item_head,
        "quality_composer_commit": quality_head,
        "game_author_commit": author_head,
        "item_overrides_only": [ITEM_NAME],
        "other_twenty_five_byte_unchanged": True,
        "studio": "NOT_TESTED", "android": "NOT_TESTED", "owner_accepted": False,
    })
    receipt.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ITEM_26_OVERLAY_ONLY_PASS", EXPECTED, sha(old), sha(item))


def compile_all(project: Path, compiler: Path):
    for name, (_, path) in sorted(ids(project).items()):
        subprocess.run([str(compiler), "--text", str(path)],
                       stdout=subprocess.DEVNULL, check=True)
        print("NATIVE_PARSE", name)
    print("ITEM_26_NATIVE_PARSE_PASS", EXPECTED)


def verify(project: Path, place: Path, receipt: Path):
    candidates = ids(project)
    expected = {}
    for name, (_, path) in candidates.items():
        cl = ("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else
              "ModuleScript")
        expected[name] = (cl, path.read_text(encoding="utf-8").replace("\r\n", "\n"))
    actual = {}
    for node in ET.fromstring(place.read_bytes()).iter("Item"):
        cl = node.attrib.get("class")
        if cl not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = node.find("Properties")
        if props is None:
            continue
        name = props.findtext("string[@name='Name']")
        assert name not in actual, ("double-installed module", name)
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        assert source is not None, ("compiled source missing", name)
        actual[name] = (cl, source.replace("\r\n", "\n"))
    assert expected == actual, {
        "missing": sorted(set(expected) - set(actual)),
        "extra": sorted(set(actual) - set(expected)),
        "different": sorted(k for k in set(expected)&set(actual)
                            if expected[k] != actual[k]),
    }
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert data["item_overrides_only"] == [ITEM_NAME]
    for name, (_, path) in candidates.items():
        assert data["source_sha256"][name] == sha(path), ("source receipt drift", name)
    data["place_bytes"] = place.stat().st_size
    data["place_sha256"] = sha(place)
    data["source_exact"] = f"{EXPECTED}/{EXPECTED}"
    receipt.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ITEM_26_ROJO_SOURCE_EXACT_PASS", EXPECTED, data["place_bytes"], data["place_sha256"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("prepare", "compile", "verify"))
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--item", type=Path)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--item-head")
    ap.add_argument("--quality-head")
    ap.add_argument("--author-head")
    ap.add_argument("--compiler", type=Path)
    ap.add_argument("--place", type=Path)
    args = ap.parse_args()
    if args.mode == "prepare":
        assert all((args.out, args.item, args.receipt, args.item_head,
                    args.quality_head, args.author_head))
        prepare(args.project, args.out, args.item, args.receipt, args.item_head,
                args.quality_head, args.author_head)
    elif args.mode == "compile":
        assert args.compiler
        compile_all(args.project, args.compiler)
    else:
        assert args.place and args.receipt
        verify(args.project, args.place, args.receipt)


if __name__ == "__main__":
    main()
