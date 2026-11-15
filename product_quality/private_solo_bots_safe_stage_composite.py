#!/usr/bin/env python3
"""#470 FB005 real Game cumulative: private SoloTeamBots + safe spectator island.

Compose distinct gameplay fixes from existing #297/#471 author candidates.
Pinned source-exact private A-PREP only; this never updates official RC/main.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
from role7_respawn_guard import extract, verify, blob

RC_HEAD = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PARENT = "P0D_ROLE7_SPECTATOR_PRIVATE_SOLO_BOTS_RC82.rbxlx"
OUT = "P0D_ROLE7_SOLO_BOTS_SAFE_SPECTATOR_RC82.rbxlx"
PARENT_SHA = "457cb3fb34d9fe72485e335aa0e7307c06fab75bcff09cffd6d45615d94bfde8"
PARENT_GAME_BLOB = "976d2a7118a0013f1dc32f414ec4fe54b9b84b31"
PARENT_BOTS_BLOB = "a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
GAME = "server/Game.server.luau"
BOTS = "server/SoloTeamBots.luau"

# Source anchored to the EXISTING original-author Game; only two non-overlap hunks.
SAFE_BEFORE = (
    'elseif RunService:IsStudio()\n'
    '            and player:GetAttribute("P0D_LateJoinSpectator")==true then\n'
    '            root.CFrame=LobbyIsland.spawn("RED")'
)
SAFE_AFTER = (
    'elseif player:GetAttribute("P0D_LateJoinSpectator")==true then\n'
    '            -- Physically isolate late spectators even in a private live match.\n'
    '            -- Build only on demand; public and ordinary joins remain unchanged.\n'
    '            if map.model:FindFirstChild("P0D_SAFE_LOBBY")==nil then\n'
    '                LobbyIsland.build(map.model)\n'
    '            end\n'
    '            root.CFrame=LobbyIsland.spawn("RED")'
)
REENTER_BEFORE = (
    'root.CFrame=if RunService:IsStudio()\n'
    '                            then LobbyIsland.spawn(getTeamName(entrant))\n'
    '                            else map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0)'
)
REENTER_AFTER = (
    'root.CFrame=if RunService:IsStudio()\n'
    '                            then LobbyIsland.spawn(getTeamName(entrant))\n'
    '                            -- Neutral spectator may have no RED/BLUE team.\n'
    '                            -- Reuse existing root position rather than index nil.\n'
    '                            else (map.teams[getTeamName(entrant)]\n'
    '                                and (map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0))\n'
    '                                or root.CFrame)'
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def swap(src: str, old: str, new: str, label: str) -> str:
    if src.count(old) != 1 or new in src:
        raise ValueError("UNPINNED_OR_ALREADY_APPLIED:" + label)
    return src.replace(old, new, 1)

def egg_authority_region(src: str) -> str:
    begin = 'for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
    end = '\n-- P0D_SAVED_PVE_MASTERY_V1:'
    return src[src.index(begin):src.index(end, src.index(begin))]

def compose(game_src: str) -> str:
    out = swap(game_src, SAFE_BEFORE, SAFE_AFTER, "SPECTATOR_PHYSICAL_ISLAND")
    out = swap(out, REENTER_BEFORE, REENTER_AFTER, "TEAMLESS_LOBBY_REENTRY")
    if egg_authority_region(game_src) != egg_authority_region(out):
        raise ValueError("EGG_WINNER_SCORE_AUTHORITY_CHANGED")
    for proof in (
        'pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)',
        'pcall(SoloTeamBots.tick,now)',
        'SoloTeamBots.tryHumanHit(team,root.Position,look',
        'privateSoloBotsTrialAllowed()',
        'SoloTeamBots.stop()',
        'PRIVATE_SOLO_BOTS_DISABLED',
        'horde:tick(now,eligibleSoloPlayers(),healthy)',
        'sevenJobPickAckSeq[player]~=selectedAck',
        'player.Character~=castCharacter',
        'personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1',
    ):
        if proof not in out:
            raise ValueError("LOST_AUTHOR_GAMEPLAY:" + proof)
    return out

def build(parent: Path, output: Path, extract_dir: Path | None = None) -> dict:
    with ZipFile(parent) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or any(
            n.startswith("/") or ".." in Path(n).parts for n in names
        ):
            raise ValueError("UNSAFE_PARENT_ZIP")
        raw = z.read(PARENT)
        lock = json.loads(z.read("SOURCE_LOCK.json"))
        feature_lock = json.loads(z.read("RC_FEATURE_LOCK.json"))
        previous = json.loads(z.read("RECEIPT.json"))
    if sha(raw) != PARENT_SHA:
        raise ValueError("BOT_PARENT_PLACE_DRIFT")
    if previous.get("official_rc_head") != RC_HEAD or not previous.get("private_only") or not previous.get("default_off"):
        raise ValueError("BOT_PARENT_NOT_PRIVATE_OR_NOT_PINNED")
    scripts = verify(raw, lock, feature_lock)
    root, nodes = extract(raw)
    if len(nodes) != 82 or lock["blobs"].get(GAME) != PARENT_GAME_BLOB \
            or lock["blobs"].get(BOTS) != PARENT_BOTS_BLOB:
        raise ValueError("WRONG_BOT_AUTHOR_GAME_BLOB")
    old_game = scripts["Game"].text
    new_game = compose(old_game)
    nodes["Game"].text = new_game
    place = ET.tostring(root, encoding="utf-8")
    final = extract(place)[1]
    if len(final) != 82 or any(final[name].text != scripts[name].text
                                for name in scripts if name != "Game"):
        raise ValueError("OTHER_81_SOURCE_CHANGED")
    new_blob = blob(new_game)
    lock["blobs"][GAME] = feature_lock["source_gitblobs"][GAME] = new_blob
    verify(place, lock, feature_lock)
    report = {
        "schema": "P0D_470_SOLO_BOTS_PLUS_SAFE_SPECTATOR_V1",
        "official_rc_head": RC_HEAD,
        "parent_place_sha256": PARENT_SHA,
        "place_sha256": sha(place),
        "place_bytes": len(place),
        "new_game_gitblob": new_blob,
        "solo_bots_gitblob_unchanged": PARENT_BOTS_BLOB,
        "scripts": 82,
        "unchanged_parent_scripts": 81,
        "changed": [GAME],
        "egg_score_winner_authority_unchanged": True,
        "source_lock_exact": True,
        "private_only": True,
        "default_off": True,
        "spectator_physical_island": True,
        "teamless_reentry_fallback": True,
        "source_native": "NOT_RUN",
        "studio": "NOT_RUN",
        "android": "NOT_RUN",
        "owner": False,
        "official_rc_write": False,
        "product": "NO_GO",
    }
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        z.writestr(OUT, place)
        z.writestr("SOURCE_LOCK.json", json.dumps(lock, ensure_ascii=False, indent=2) + "\n")
        z.writestr("RC_FEATURE_LOCK.json", json.dumps(feature_lock, ensure_ascii=False, indent=2) + "\n")
        z.writestr("RECEIPT.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if extract_dir is not None:
        extract_dir.mkdir(parents=True, exist_ok=True)
        for name, node in final.items():
            (extract_dir / (name + ".luau")).write_text(node.text, encoding="utf-8")
    return report

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--extract", type=Path)
    a = p.parse_args()
    print(json.dumps(build(a.parent, a.out, a.extract), ensure_ascii=False, indent=2))
