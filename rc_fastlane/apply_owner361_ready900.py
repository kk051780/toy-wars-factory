#!/usr/bin/env python3
"""#361 P0-A isolated PREP: require explicit READY; default 900-second rounds.

Patch the *assembled* RC66 Game/Config/HUD, never the immutable release input.
No second Game/Remote/Store/damage writer is added. This is NOT the official
RC until the sole #220 integrator reviews and composes it on latest head.
OFF is a total no-op; any source drift causes a fail-closed assertion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FEATURE = "OWNER361_READY900_V1"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
CONFIG = "shared/Config.luau"
EXPECTED_COUNT = 66


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def replace_one(src: str, old: str, new: str) -> str:
    actual = src.count(old)
    if actual != 1:
        raise AssertionError(("P0D_OWNER361_SOURCE_DRIFT", old[:95], actual))
    return src.replace(old, new, 1)


def patch_game(src: str) -> str:
    assert src.count("remote.OnServerEvent:Connect(") == 1, "ONE_REMOTE_AUTHORITY"
    src = replace_one(src,
        "local carry: {[Player]: string} = {}\n",
        "local carry: {[Player]: string} = {}\n"
        "local voluntaryReady: {[Player]: boolean} = {} -- server-only human consent\n")
    src = replace_one(src,
        'kind = "SNAPSHOT", serial = match.serial, phase = match.phase,',
        'kind = "SNAPSHOT", serial = match.serial, phase = match.phase,\n'
        '        ready = voluntaryReady[player] == true,')
    helper = '''-- Explicit player consent is server-authoritative, including after RESULTS.
-- All connected humans must opt in. Existing StudioSolo permits one consenting
-- human to start, but this slice does NOT pretend to supply real ally/enemy AI.
local function allHumansReady(): boolean
    local humans = Players:GetPlayers()
    if #humans == 0 then return false end
    for _, human in ipairs(humans) do
        if voluntaryReady[human] ~= true then return false end
    end
    return true
end

local function applyVoluntaryReady(player: Player, data)
    if match.phase ~= "LOBBY" and match.phase ~= "COUNTDOWN" then return end
    if type(data.ready) ~= "boolean" then return end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq
    voluntaryReady[player] = data.ready
    remote:FireClient(player, snapshotFor(player))
end

'''
    src = replace_one(src, "remote.OnServerEvent:Connect(function(player: Player, data)\n",
        helper + "remote.OnServerEvent:Connect(function(player: Player, data)\n")
    src = replace_one(src,
        '    if data.action == "ATTACK" then applyAttack(player, data)\n',
        '    if data.action == "READY" then applyVoluntaryReady(player, data)\n'
        '    elseif data.action == "ATTACK" then applyAttack(player, data)\n')
    src = replace_one(src,
        "local function onJoin(player: Player)\n",
        "local function onJoin(player: Player)\n    voluntaryReady[player] = false\n")
    src = replace_one(src,
        "    roles[player] = nil\n",
        "    voluntaryReady[player] = nil\n    roles[player] = nil\n")
    src = replace_one(src,
        "        rebalanceLobbyTeams()\n",
        "        rebalanceLobbyTeams()\n"
        "        -- No READY means no countdown, regardless of existing StudioSolo.\n"
        "        if not allHumansReady() then return end\n")
    src = replace_one(src,
        '    elseif match.phase == "COUNTDOWN" then\n',
        '    elseif match.phase == "COUNTDOWN" then\n'
        '        if not allHumansReady() then\n'
        '            match.phase = "LOBBY"\n'
        '            match.phaseUntil = 0\n'
        '            return\n'
        '        end\n')
    src = replace_one(src,
        '        if now >= match.phaseUntil then\n            match.phase = "LOBBY"\n',
        '        if now >= match.phaseUntil then\n'
        '            -- Every new round requires a NEW tap, never forced auto-replay.\n'
        '            for _, human in ipairs(Players:GetPlayers()) do\n'
        '                voluntaryReady[human] = false\n'
        '            end\n'
        '            match.phase = "LOBBY"\n')
    assert src.count("remote.OnServerEvent:Connect(") == 1
    assert src.count('data.action == "READY"') == 1
    assert src.count('voluntaryReady[human] = false') == 1
    return src


def patch_hud(src: str) -> str:
    src = replace_one(src,
        "local seq = 0\n",
        '''-- Only visible outside combat; never cover Roblox touch/movement UI in ACTIVE.
local voluntaryReady = false
local readyButton = button(gui, "Owner361Ready", "▶ 出撃する",
    UDim2.fromOffset(168, 48), UDim2.new(.5, -84, 1, -108),
    Color3.fromRGB(44, 150, 113))
readyButton.Visible = false
local seq = 0
''')
    src = replace_one(src,
        '    remote:FireServer({action = kind, role = role, seq = seq})\n',
        '    remote:FireServer({action = kind, role = role, seq = seq,\n'
        '        ready = if kind == "READY" then not voluntaryReady else nil})\n')
    src = replace_one(src,
        'roleGuardian.MouseButton1Click:Connect(function() action("ROLE", "GUARDIAN") end)\n',
        'roleGuardian.MouseButton1Click:Connect(function() action("ROLE", "GUARDIAN") end)\n'
        'readyButton.MouseButton1Click:Connect(function() action("READY", nil) end)\n')
    src = replace_one(src,
        '    status.Text = phaseText(s)\n',
        '''    voluntaryReady = s.ready == true
    readyButton.Visible = s.phase == "LOBBY" or s.phase == "COUNTDOWN"
    readyButton.Text = if voluntaryReady then "✓ 準備完了（押すと取消）" else "▶ 出撃する"
    status.Text = phaseText(s)
    if s.phase == "LOBBY" then
        status.Text = if voluntaryReady
            then "出撃待ち｜相手の準備を待っています"
            else "敵城の卵を奪い自陣へ！ 城も攻撃可｜攻撃F／罠T｜出撃を押す"
    end
''')
    assert 'readyButton.Visible = s.phase == "LOBBY" or s.phase == "COUNTDOWN"' in src
    assert src.count('action("READY", nil)') == 1
    return src


def patch_config(src: str) -> str:
    return replace_one(src, "    MatchSeconds = 360,", "    MatchSeconds = 900,")


def scripts(dist: Path) -> dict[str, bytes]:
    return {
        p.relative_to(dist / "src").as_posix(): p.read_bytes()
        for p in sorted((dist / "src").rglob("*.luau"))
    }


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("OWNER361_READY900_OFF_BYTE_IDENTICAL_PASS")
        return False
    before = scripts(dist)
    assert len(before) == EXPECTED_COUNT, ("REQUIRE_RICH66", len(before))
    for path in (GAME, HUD, CONFIG):
        assert path in before, ("MISSING_RUNTIME_SOURCE", path)
    original = {path: gitblob(data) for path, data in sorted(before.items())}
    source_lock_path = dist / "SOURCE_LOCK.json"
    feature_lock_path = dist / "RC_FEATURE_LOCK.json"
    source_lock = json.loads(source_lock_path.read_text(encoding="utf8"))
    feature_lock = json.loads(feature_lock_path.read_text(encoding="utf8"))
    assert source_lock["total_scripts"] == EXPECTED_COUNT
    assert source_lock["blobs"] == original, "SOURCE_LOCK_INPUT_MISMATCH"
    assert feature_lock["total_sources"] == EXPECTED_COUNT
    assert feature_lock["source_gitblobs"] == original, "FEATURE_LOCK_INPUT_MISMATCH"
    assert FEATURE not in feature_lock.get("feature_flags", {}), "DOUBLE_PATCH"

    patched = dict(before)
    patched[GAME] = patch_game(before[GAME].decode("utf8")).encode("utf8")
    patched[HUD] = patch_hud(before[HUD].decode("utf8")).encode("utf8")
    patched[CONFIG] = patch_config(before[CONFIG].decode("utf8")).encode("utf8")
    assert len(patched) == EXPECTED_COUNT
    assert all(data == patched[path] for path, data in before.items()
               if path not in (GAME, HUD, CONFIG)), "UNAUTHORIZED_SOURCE_CHANGE"
    assert patched[GAME].count(b"remote.OnServerEvent:Connect(") == 1
    # All patches validated before writing anything.
    for path in (GAME, HUD, CONFIG):
        (dist / "src" / path).write_bytes(patched[path])

    result = {path: gitblob(data) for path, data in sorted(patched.items())}
    receipt = {
        "id": FEATURE,
        "base_source_count": EXPECTED_COUNT,
        "source_count": EXPECTED_COUNT,
        "affected": sorted([GAME, HUD, CONFIG]),
        "base_source_gitblobs": {path: original[path] for path in (GAME, HUD, CONFIG)},
        "post_source_gitblobs": {path: result[path] for path in (GAME, HUD, CONFIG)},
        "single_Game_and_Remote": True,
        "explicit_ready_after_results": True,
        "match_seconds": 900,
        "real_bots": "NOT_INCLUDED",
        "physical_lobby": "NOT_INCLUDED",
        "studio_engine": "NOT_TESTED",
    }
    source_lock["blobs"] = result
    source_lock["rc_owner361_entry"] = receipt
    feature_lock["source_gitblobs"] = result
    feature_lock["feature_flags"][FEATURE] = True
    feature_lock["rc_owner361_entry"] = receipt
    source_lock_path.write_text(
        json.dumps(source_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    feature_lock_path.write_text(
        json.dumps(feature_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("OWNER361_READY900_RICH66_SOURCE_LOCK_UPDATED_PASS")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--enabled", choices=("true", "false"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.enabled == "true")


if __name__ == "__main__":
    main()
