#!/usr/bin/env python3
"""P0D-URGENT-READY: reversible candidate overlay on compiled canonical RC66.

A-lane PREP only. NOT invoked by the official sole-writer build. No new
RemoteEvent, controller, DataStore, reward, payment or Studio release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FEATURE = "P0D_URGENT_READY_900_V1"
TARGET = {
    "server/Game.server.luau",
    "client/HUD.client.luau",
    "shared/Config.luau",
}


def gitblob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def once(body: str, old: str, new: str) -> str:
    count = body.count(old)
    if count != 1:
        raise AssertionError(("P0D_READY_SOURCE_DRIFT", old[:100], count))
    return body.replace(old, new, 1)


def patch_config(src: str) -> str:
    assert FEATURE not in src, "ALREADY_PATCHED"
    return once(src, "MatchSeconds = 360,", "MatchSeconds = 900, -- 15 minutes (OWNER P0)")


def patch_game(src: str) -> str:
    assert FEATURE not in src, "ALREADY_PATCHED"
    src = once(src, "local roles: {[Player]: string} = {}", '''local roles: {[Player]: string} = {}
-- P0D_URGENT_READY_900_V1: READY intent exists only on the original server Game.
local roundReady: {[Player]: boolean} = {}
local function everybodyReady(): boolean
    local online = Players:GetPlayers()
    if #online == 0 then return false end
    for _, player in ipairs(online) do
        if roundReady[player] ~= true then return false end
    end
    return true
end''')
    src = once(src, 'kind = "SNAPSHOT", serial = match.serial, phase = match.phase,',
        'kind = "SNAPSHOT", serial = match.serial, phase = match.phase,\n'
        '        ready = roundReady[player] == true,')
    src = once(src, '    match.phase = "RESULTS"', '''    match.phase = "RESULTS"
    -- Every finished match must require a NEW, voluntary READY event.
    for _, player in ipairs(Players:GetPlayers()) do roundReady[player] = false end''')
    src = once(src, '    roles[player] = "RAIDER"',
        '    roles[player] = "RAIDER"\n    roundReady[player] = false')
    src = once(src, '    roles[player] = nil',
        '    roles[player] = nil\n    roundReady[player] = nil')
    handler = 'remote.OnServerEvent:Connect(function(player: Player, data)'
    added = '''-- One authenticated Remote; READY cannot change score, damage or match duration.
local function applyReady(player: Player, data)
    if data.action ~= "READY" or type(data.ready) ~= "boolean" then return end
    -- Rejected READY packets must NEVER burn the shared combat input sequence.
    if match.phase ~= "LOBBY" and match.phase ~= "COUNTDOWN" then return end
    -- During COUNTDOWN only cancellation is allowed, never late opt-in.
    if match.phase == "COUNTDOWN" and data.ready then return end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq
    roundReady[player] = data.ready
    -- A player withdrawing consent immediately cancels the COUNTDOWN;
    -- all peers receive the updated authoritative phase, not only the sender.
    if match.phase == "COUNTDOWN" and not data.ready then
        match.phase = "LOBBY"
        match.phaseUntil = 0
    end
    broadcast()
end

'''
    src = once(src, handler, added + handler)
    src = once(src, '    if type(data) ~= "table" then return end\n    if data.action == "ATTACK" then',
        '    if type(data) ~= "table" then return end\n'
        '    if data.action == "READY" then applyReady(player, data) return end\n'
        '    if data.action == "ATTACK" then')
    # Modify only tickRound's phase machine: never disturb other LOBBY callbacks.
    marker = 'local function tickRound()'
    if src.count(marker) != 1:
        raise AssertionError("tickRound_missing_or_ambiguous")
    prefix, phase = src.split(marker, 1)
    # 2026-11-14 integration-only correction: current assembled RC66 uses
    # StudioSolo.canStart(..), not the original pre-Solo MinPlayers-only gate.
    # Keep existing one-human Studio policy and add voluntary READY outside it.
    phase = once(phase, '        if StudioSolo.canStart(',
        '        if everybodyReady() and StudioSolo.canStart(')
    phase = once(phase, '    elseif match.phase == "COUNTDOWN" then',
        '    elseif match.phase == "COUNTDOWN" then\n'
        '        if not everybodyReady() then\n'
        '            match.phase = "LOBBY"\n'
        '            match.phaseUntil = 0\n'
        '            broadcast()\n'
        '            return\n'
        '        end')
    src = prefix + marker + phase
    assert src.count('remote.OnServerEvent:Connect(') == 1
    assert src.count('remote.Name = "TrapRaidersS1Remote"') == 1
    assert src.count('local function tickRound()') == 1
    assert src.count('local function applyReady(') == 1
    return src


def patch_hud(src: str) -> str:
    assert FEATURE not in src, "ALREADY_PATCHED"
    src = once(src, 'local seq = 0', '''-- P0D_URGENT_READY_900_V1: lobby-only opt-in, invisible during battle.
local readyButton = button(gui, "VoluntaryReady", "▶ 出撃する",
    UDim2.fromOffset(158, 50), UDim2.new(.5, -79, 0, 151),
    Color3.fromRGB(42, 153, 111))
readyButton.Visible = false
local isReady = false
local seq = 0''')
    src = once(src, 'attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)',
        'readyButton.MouseButton1Click:Connect(function()\n'
        '    if not readyButton.Visible then return end\n'
        '    seq += 1\n'
        '    isReady = not isReady -- optimistic toggle handles rapid cancel before SNAPSHOT\n'
        '    readyButton.Text = if isReady then "✓ 出撃予約中\\n押すと取消" else "▶ 出撃する"\n'
        '    remote:FireServer({action="READY", ready=isReady, seq=seq})\n'
        'end)\n'
        'attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)')
    src = once(src, 'local function phaseText(s): string', '''local function phaseText(s): string
    if s.phase == "LOBBY" then
        return if s.ready == true then "出撃予約済。全員の準備を待っています"
            else "敵城の卵を奪い自城へ！ 出撃するにはボタンを押す"
    end''')
    src = once(src, '    if s.kind ~= "SNAPSHOT" then return end',
        '    if s.kind ~= "SNAPSHOT" then return end\n'
        '    if type(s.phase) == "string" then\n'
        '        isReady = s.ready == true\n'
        '        readyButton.Visible = s.phase == "LOBBY" or s.phase == "COUNTDOWN"\n'
        '        readyButton.Text = if isReady then "✓ 出撃予約中\\n押すと取消" else "▶ 出撃する"\n'
        '    end')
    assert src.count('FireServer({action="READY"') == 1
    return src


def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}


def apply(dist: Path, enabled: bool) -> bool:
    # OFF is intentionally a byte-for-byte no-op on all compiled source and locks.
    if not enabled:
        print("P0D_READY_OFF_ALL_BYTES_UNCHANGED")
        return False
    before = sources(dist)
    assert len(before) == 66, ("REQUIRES_EXACT_RC66", len(before))
    assert TARGET.issubset(before.keys()), "REQUIRED_ORIGINAL_OWNER_PATHS_MISSING"
    lp = dist / "SOURCE_LOCK.json"
    fp = dist / "RC_FEATURE_LOCK.json"
    lock = json.loads(lp.read_text("utf8"))
    feature = json.loads(fp.read_text("utf8"))
    pins = {p: gitblob(v) for p, v in sorted(before.items())}
    assert lock["total_scripts"] == 66 and lock["blobs"] == pins
    assert feature["total_sources"] == 66 and feature["source_gitblobs"] == pins
    assert FEATURE not in feature["feature_flags"]
    updates = {
        "server/Game.server.luau": patch_game(before["server/Game.server.luau"].decode("utf8")),
        "client/HUD.client.luau": patch_hud(before["client/HUD.client.luau"].decode("utf8")),
        "shared/Config.luau": patch_config(before["shared/Config.luau"].decode("utf8")),
    }
    after = {**before, **{p: v.encode("utf8") for p, v in updates.items()}}
    assert {p for p in before if before[p] != after[p]} == TARGET
    assert len(after) == 66 and set(before) == set(after)
    lock["blobs"] = {p: gitblob(b) for p, b in sorted(after.items())}
    lock["rc_urgent_ready"] = {
        "id": FEATURE, "changed": sorted(TARGET), "source_count": 66,
        "unchanged_sources": 63, "server_ready_authority": True,
        "new_remote": False, "saved_profile_change": False,
        "roll_back": "omit this overlay to retain exact canonical66",
        "studio_2client": "NOT_TESTED", "owner_fun": "NOT_TESTED",
    }
    feature["source_gitblobs"] = lock["blobs"]
    feature["feature_flags"][FEATURE] = True
    for p, body in updates.items():
        (dist / "src" / p).write_text(body, encoding="utf8")
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    fp.write_text(json.dumps(feature, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    assert sources(dist) == after
    print("P0D_READY_900_SOURCE_CHANGED_3_OTHER_63_IDENTICAL_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--enabled", required=True, choices=("true", "false"))
    args = parser.parse_args()
    apply(args.dist, args.enabled == "true")
