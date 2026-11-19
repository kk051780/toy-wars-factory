#!/usr/bin/env python3
"""P0D #470/FB005: safe lobby re-entry when a spectator has no valid team.

This is a source-exact, Game-only A-PREP child of the *existing* #471 cumulative
82-source private artifact. It does NOT write the official RC, main or Studio.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from role7_respawn_guard import extract, verify, blob

RC_HEAD = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PARENT_PLACE = "P0D_ROLE7_ACK_WIND_BUILDER_COMBO_RESPAWN_SPECTATOR_RC82.rbxlx"
PARENT_PLACE_SHA = "bbb9c919cb11cfc5147a75a9d8f8e770eb5a7d540acfffeb650010f5710e0d1c"
PARENT_GAME_BLOB = "6848da45a10242e5908a102bd9db47b9d3f30023"
GAME_PATH = "server/Game.server.luau"
OUTPUT_PLACE = "P0D_ROLE7_LOBBY_REENTRY_TEAM_SAFE_RC82.rbxlx"
EXPECTED_PLACE_SHA = "00fb3eb899495e9978636bb2f81aaae68271bfd834841ccac1251555e54ce1e1"
EXPECTED_PLACE_BYTES = 779343
EXPECTED_GAME_BLOB = "ab5576a406b23bbd3903c76a64d3f5cc54f950a3"
OLD = (
    'root.CFrame=if RunService:IsStudio()\n'
    '                            then LobbyIsland.spawn(getTeamName(entrant))\n'
    '                            else map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0)'
)
NEW = (
    'root.CFrame=if RunService:IsStudio()\n'
    '                            then LobbyIsland.spawn(getTeamName(entrant))\n'
    '                            -- A late spectator can still lack a valid RED/BLUE team.\n'
    '                            -- Preserve the avatar position rather than index nil.\n'
    '                            else (map.teams[getTeamName(entrant)]\n'
    '                                and (map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0))\n'
    '                                or root.CFrame)'
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safe_members(z: ZipFile):
    names = z.namelist()
    if len(names) != len(set(names)) or any(
        n.startswith("/") or ".." in Path(n).parts for n in names
    ):
        raise ValueError("UNSAFE_ZIP_MEMBERS")
    return names

def replace_game(game_source: str) -> str:
    if game_source.count(OLD) != 1 or NEW in game_source:
        raise ValueError("LOBBY_REENTRY_ANCHOR_DRIFT")
    out = game_source.replace(OLD, NEW, 1)
    assert out.count("root.CFrame=if RunService:IsStudio()") == 1
    for essential in (
        "sevenJobPickAckSeq[player]~=selectedAck",
        "player.Character~=castCharacter",
        "root.Parent~=castCharacter",
        "horde:tick(now,eligibleSoloPlayers(),healthy)",
        "personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1",
    ):
        if essential not in out:
            raise ValueError("PARENT_GAMEPLAY_REGRESSION:" + essential)
    return out

def build(parent_file: Path, output_file: Path, extract_dir: Path | None = None) -> dict:
    with ZipFile(parent_file) as z:
        names = safe_members(z)
        if PARENT_PLACE not in names:
            raise ValueError("PARENT_PLACE_MISSING")
        place = z.read(PARENT_PLACE)
        lock = json.loads(z.read("SOURCE_LOCK.json"))
        feature = json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt = json.loads(z.read("RECEIPT.json"))
    if sha(place) != PARENT_PLACE_SHA or lock.get("blobs", {}).get(GAME_PATH) != PARENT_GAME_BLOB:
        raise ValueError("UNPINNED_PARENT_GAME")
    if receipt.get("official_rc_head") != RC_HEAD:
        raise ValueError("UNPINNED_OFFICIAL_HEAD")
    before = verify(place, lock, feature)
    root, source_nodes = extract(place)
    old_game = before["Game"].text
    new_game = replace_game(old_game)
    source_nodes["Game"].text = new_game
    output_place = ET.tostring(root, encoding="utf-8")
    after = extract(output_place)[1]
    if len(after) != 82 or any(
        after[name].text != before[name].text for name in before if name != "Game"
    ):
        raise ValueError("OTHER_GAME_SCRIPTS_CHANGED")
    # Keep the entire authority-bearing egg/score path byte-exact.
    begin = 'map.teams[team].eggPrompt.Triggered:Connect(function(player: Player)'
    end = "\n-- P0D_SAVED_PVE_MASTERY_V1:"
    if old_game[old_game.index(begin):old_game.index(end)] != new_game[new_game.index(begin):new_game.index(end)]:
        raise ValueError("EGG_SCORE_REGRESSION")
    new_blob = blob(new_game)
    if new_blob != EXPECTED_GAME_BLOB or sha(output_place) != EXPECTED_PLACE_SHA \
            or len(output_place) != EXPECTED_PLACE_BYTES:
        raise ValueError("SOURCE_EXACT_FIXED_OUTPUT_DRIFT")
    lock["blobs"][GAME_PATH] = feature["source_gitblobs"][GAME_PATH] = new_blob
    verify(output_place, lock, feature)
    report = {
        "schema": "P0D_FB005_LOBBY_REENTRY_TEAM_FALLBACK_V1",
        "official_rc_head": RC_HEAD,
        "parent_place_sha256": PARENT_PLACE_SHA,
        "parent_game_gitblob": PARENT_GAME_BLOB,
        "place_sha256": sha(output_place),
        "place_bytes": len(output_place),
        "new_game_gitblob": new_blob,
        "source_count": 82,
        "unchanged_scripts": 81,
        "egg_score_authority_unchanged": True,
        "fixed": "NO_TEAM_OR_BAD_TEAM_LOBBY_REENTRY_NIL_INDEX",
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "owner": "NO_GO",
        "product": "NO_GO",
        "official_rc_write": False,
    }
    with ZipFile(output_file, "w", ZIP_DEFLATED) as z:
        z.writestr(OUTPUT_PLACE, output_place)
        z.writestr("SOURCE_LOCK.json", json.dumps(lock, ensure_ascii=False, indent=2) + "\n")
        z.writestr("RC_FEATURE_LOCK.json", json.dumps(feature, ensure_ascii=False, indent=2) + "\n")
        z.writestr("RECEIPT.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if extract_dir is not None:
        extract_dir.mkdir(parents=True, exist_ok=True)
        for name, item in after.items():
            (extract_dir / (name + ".luau")).write_text(item.text, encoding="utf-8")
    return report

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--extract", type=Path)
    args = p.parse_args()
    print(json.dumps(build(args.parent, args.out, args.extract), ensure_ascii=False, indent=2))
