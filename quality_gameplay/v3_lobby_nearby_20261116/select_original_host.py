#!/usr/bin/env python3
"""Source-select only GQ539's lobby/role plaque changes into ONE existing V3 Host.

No competing Game/Host, no remote, no writes to official RC, no merge/publish.
Intended as a post-composition selector for original-owner #530 31-source Rojo
project (optionally after #547 castle+vault overlay). The exact input Host blob
must be supplied and every mapped non-Host script must remain byte-identical.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

HOST = "EGGRUMBLE_LobbyCastleModesPreview"
SOURCE_COUNT_RC = 31
ORIGINAL_HOST_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
BOARD_FACTORY = '''local function board(at:BasePart,label:string)
 local b=Instance.new("BillboardGui");b.Size=UDim2.fromOffset(230,82);b.StudsOffset=Vector3.new(0,4.5,0)
 b.AlwaysOnTop=true;b.Parent=at
 local t=Instance.new("TextLabel");t.Size=UDim2.fromScale(1,1);t.TextScaled=true;t.TextWrapped=true
 t.BackgroundColor3=Color3.fromRGB(24,27,43);t.BackgroundTransparency=.12
 t.TextColor3=Color3.new(1,1,1);t.Font=Enum.Font.GothamBold;t.Text=label;t.Parent=b
end'''
HELPER = '''-- GQ539 LOBBY ONLY: preserve original world board authority and #547 castle/vault fix.
-- Reuse the existing BillboardGui; no duplicate labels, Game, Remote, or core HP logic.
local function nearbyBoard(at:BasePart,label:string,maxDistance:number):()
 board(at,label)
 local gui=at:FindFirstChildOfClass("BillboardGui")
 if not gui then return end
 gui.AlwaysOnTop=false
 gui.MaxDistance=math.clamp(maxDistance,16,52)
 gui.Size=UDim2.fromOffset(174,56)
 gui.StudsOffsetWorldSpace=Vector3.new(0,3.2,0)
 local title=gui:FindFirstChildOfClass("TextLabel")
 if title then
  title.TextScaled=false
  title.TextSize=14
  title.BackgroundTransparency=.54
 end
end'''
CALLS = (
    ('board(stand,data.name.."\\n"..data.weapon)',
     'nearbyBoard(stand,data.name.."\\n"..data.weapon,24)'),
    ('board(gateTeam,"EGGRUMBLE\\nチーム戦｜全味方城陥落で敗北")',
     'nearbyBoard(gateTeam,"EGGRUMBLE\\nチーム戦｜全味方城陥落で敗北",44)'),
    ('board(gateBR,"EGGRUMBLE\\nバトルロワイヤル｜最後の城が勝者")',
     'nearbyBoard(gateBR,"EGGRUMBLE\\nバトルロワイヤル｜最後の城が勝者",44)'),
    ('board(stand,name.."\\n出撃前の防衛選択")',
     'nearbyBoard(stand,name.."\\n出撃前の防衛選択",25)'),
)


def git_blob(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def patch(source: str) -> str:
    if source.count(BOARD_FACTORY) != 1:
        raise ValueError("RED original board factory changed; do not overwrite #547")
    if "local function nearbyBoard(" in source:
        raise ValueError("RED duplicate GQ539 lobby helper")
    if source.count('board(core,(entry.isAI and "AI " or "")') != 1:
        raise ValueError("RED castle core call drift")
    if source.count('board(vault,"卵倉庫")') != 1:
        raise ValueError("RED vault call drift")
    out = source.replace(BOARD_FACTORY, BOARD_FACTORY + "\n" + HELPER, 1)
    for prev, new in CALLS:
        if out.count(prev) != 1:
            raise ValueError("RED original role/mode/defense anchor changed: " + prev[:50])
        out = out.replace(prev, new, 1)
    return out


def undo(patched: str) -> str:
    if patched.count(BOARD_FACTORY + "\n" + HELPER) != 1:
        raise ValueError("RED no unique exact GQ539 helper")
    out = patched.replace(BOARD_FACTORY + "\n" + HELPER, BOARD_FACTORY, 1)
    for prev, new in CALLS:
        if out.count(new) != 1:
            raise ValueError("RED no unique exact GQ539 call: " + new[:50])
        out = out.replace(new, prev, 1)
    return out


def mapped(data: dict) -> dict[tuple[str, ...], dict]:
    entries: dict[tuple[str, ...], dict] = {}
    def walk(obj: dict, parts: tuple[str, ...] = ()) -> None:
        for key, v in obj.items():
            if not isinstance(v, dict):
                continue
            path = parts + (key,)
            if "$path" in v:
                if set(v.keys()) != {"$path"}:
                    raise ValueError("RED script source node has competing path")
                entries[path] = v
            else:
                walk(v, path)
    walk(data["tree"])
    return entries


def generate(project: Path, out: Path, host_blob: str, count: int) -> dict:
    if count != SOURCE_COUNT_RC:
        raise ValueError("RED official selector must operate on real 31-source companion")
    data = json.loads(project.read_text(encoding="utf-8"))
    source_nodes = mapped(data)
    if len(source_nodes) != SOURCE_COUNT_RC:
        raise ValueError(f"RED source count {len(source_nodes)} instead of 31")
    keys = [key for key in source_nodes if key[-1] == HOST]
    if len(keys) != 1:
        raise ValueError("RED duplicate/missing unique Host authority")
    host_key = keys[0]
    orig_file = (project.parent / source_nodes[host_key]["$path"]).resolve()
    if not orig_file.is_file() or not orig_file.name.endswith(".server.luau"):
        raise ValueError("RED missing original Host source or wrong Script class")
    orig_bytes = orig_file.read_bytes()
    if git_blob(orig_bytes) != host_blob:
        raise ValueError("RED pinned Host blob mismatch")
    output = patch(orig_bytes.decode("utf-8")).encode("utf-8")
    if undo(output.decode("utf-8")).encode("utf-8") != orig_bytes:
        raise ValueError("RED cannot losslessly rollback Host")
    copy_tree = copy.deepcopy(data)
    clone_nodes = mapped(copy_tree)
    out.mkdir(parents=True, exist_ok=True)
    local_host = out / "GQ539_LobbyHost.server.luau"
    local_host.write_bytes(output)
    for key, node in clone_nodes.items():
        original_path = (project.parent / source_nodes[key]["$path"]).resolve()
        if not original_path.is_file():
            raise ValueError("RED missing author source " + str(original_path))
        chosen = local_host if key == host_key else original_path
        node["$path"] = os.path.relpath(chosen, out).replace(os.sep, "/")
    verified_paths = mapped(copy_tree)
    if len(verified_paths) != 31:
        raise ValueError("RED selected count drift")
    for key, node in verified_paths.items():
        if key != host_key:
            path = (out / node["$path"]).resolve()
            old = (project.parent / source_nodes[key]["$path"]).resolve()
            if path.read_bytes() != old.read_bytes():
                raise ValueError("RED non-Host modified " + "/".join(key))
    staged = out / "GQ539_SELECTED31.project.json"
    staged.write_text(json.dumps(copy_tree, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "status": "PRIVATE_CANDIDATE_NOT_OFFICIAL_ADOPTED",
        "script_count": len(verified_paths),
        "host_source_path": "/".join(host_key),
        "host_before_blob": host_blob,
        "host_after_blob": git_blob(output),
        "before_sha256": hashlib.sha256(orig_bytes).hexdigest(),
        "after_sha256": hashlib.sha256(output).hexdigest(),
        "modified_source_count": 1,
        "untouched_source_count": 30,
        "rollback_byte_exact": True,
        "castle_egg_source_ownership": "PR547",
        "lobby_only_scope": "PR539",
        "studio_android_fun": "NOT_TESTED",
    }
    (out / "GQ539_SELECTED31_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--host-blob", required=True)
    parser.add_argument("--required-count", type=int, default=31)
    args = parser.parse_args()
    print(json.dumps(generate(args.project, args.out, args.host_blob, args.required_count),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
