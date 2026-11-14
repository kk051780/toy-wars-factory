#!/usr/bin/env python3
"""P0 #361: reversible official-build game-core repair, after RC66 overlay assembly.

No new Game, Remote, Store, damage, XP or egg authority.  This patch affects only
the existing Game, Config, HUD. OFF is strictly byte-for-byte no-op.
The solo match here is still NOT bot-playable; acceptance remains FUN_NO_GO.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

ID = "P0_GAMECORE_READY_15M_HUD_V1"
GAME = "server/Game.server.luau"
CONFIG = "shared/Config.luau"
HUD = "client/HUD.client.luau"

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def inventory(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*.luau"))}

def sub_once(text: str, old: str, new: str) -> str:
    hits = text.count(old)
    assert hits == 1, ("CORE_PATCH_ANCHOR_DRIFT", old[:100], hits)
    return text.replace(old, new, 1)

def re_once(text: str, pattern: str, replacement: str, flags=0) -> str:
    value, hits = re.subn(pattern, replacement, text, count=1, flags=flags)
    assert hits == 1, ("CORE_PATCH_REGEX_ANCHOR_DRIFT", pattern, hits)
    return value

def patch_game(text: str) -> str:
    assert "local readyForMatch: {[Player]: boolean}" not in text, "DUPLICATE_P0_READY_PATCH"
    assert text.count("remote.OnServerEvent:Connect(") == 1, "DUPLICATE_GAME_REMOTE"
    assert "local function snapshotFor(player: Player)" in text, ("ACTUAL_SNAPSHOT_LINES", [ln for ln in text.splitlines() if "snapshot" in ln.lower() or "OnServerEvent:Connect(" in ln][:35])
    assert "local function tickRound()" in text
    assert "local function stopRound(" in text
    text = sub_once(text, "local function snapshotFor(player: Player)",
        """local readyForMatch: {[Player]: boolean} = {}

local function snapshotFor(player: Player)""")
    text = re_once(text, r'(kind\s*=\s*"SNAPSHOT"\s*,)',
        r'\1 ready = readyForMatch[player] == true,')
    text = sub_once(text, "local function onJoin(player: Player)",
        """local function onJoin(player: Player)
    -- Join never implies consent to join a match.
    readyForMatch[player] = false""")
    text = re_once(text,
        r'(Players\.PlayerRemoving:Connect\(function\(player(?:: Player)?\)\s*\n)',
        r'\1    readyForMatch[player] = nil\n')
    # On each finish clear every person's readiness, including the winning team.
    text = re_once(text,
        r'(local function stopRound\(winner: string, reason: string\)\s*\n\s*if match\.phase ~= "ACTIVE" then return end)',
        r'\1\n    for _, participant in ipairs(Players:GetPlayers()) do\n        readyForMatch[participant] = false\n    end')
    ready_handler = """local function toggleMatchReady(player: Player, data)
    if type(data) ~= "table" or data.action ~= "READY_TOGGLE" then return end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq
    if match.phase ~= "LOBBY" then return end
    local side = getTeamName(player)
    if side ~= "RED" and side ~= "BLUE" then return end
    readyForMatch[player] = not (readyForMatch[player] == true)
    broadcast()
end

"""
    text = re_once(text, r'(remote\.OnServerEvent:Connect\(function\(player: Player, data\))',
        ready_handler + r'\1')
    text = re_once(text,
        r'(remote\.OnServerEvent:Connect\(function\(player: Player, data\)\s*\n\s*if type\(data\) ~= "table" then return end)',
        r'\1\n    if data.action == "READY_TOGGLE" then toggleMatchReady(player, data); return end')

    eligible = """local function allPlayersReadyForRound(): boolean
    local online = Players:GetPlayers()
    if #online == 0 then return false end
    if #online == 1 then
        -- Studio-only practice is opt-in too; a neutral horde is not an AI opponent.
        return RunService:IsStudio() and readyForMatch[online[1]] == true
    end
    if #online < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then
        return false
    end
    for _, participant in ipairs(online) do
        if readyForMatch[participant] ~= true then return false end
    end
    return true
end

"""
    text = sub_once(text, "local function tickRound()", eligible + "local function tickRound()")
    # Only replace the expression directly preceding this authoritative transition.
    pivot = text.index("local function tickRound()")
    prefix, tail = text[:pivot], text[pivot:]
    lobby_start = tail.index('if match.phase == "LOBBY" then')
    countdown_start = tail.index('elseif match.phase == "COUNTDOWN" then', lobby_start)
    active_start = tail.index('elseif match.phase == "ACTIVE" then', countdown_start)
    lobby = tail[lobby_start:countdown_start]
    countdown = tail[countdown_start:active_start]
    cond = r'\bif\b(?:(?!\bif\b).){0,450}?\bthen(?=\s*\n\s*match\.phase\s*=\s*"COUNTDOWN")'
    lobby = re_once(lobby, cond, "if allPlayersReadyForRound() then", flags=re.S)
    # A countdown also aborts on roster changes rather than forcing an unready entrant.
    cond_cancel = r'\bif\b(?:(?!\bif\b).){0,450}?\bthen(?=\s*\n\s*match\.phase\s*=\s*"LOBBY")'
    countdown = re_once(countdown, cond_cancel, "if not allPlayersReadyForRound() then", flags=re.S)
    text = prefix + tail[:lobby_start] + lobby + countdown + tail[active_start:]
    assert "if allPlayersReadyForRound() then" in text
    assert "if not allPlayersReadyForRound() then" in text
    assert text.count("remote.OnServerEvent:Connect(") == 1
    return text

def patch_config(text: str) -> str:
    return re_once(text, r'\bMatchSeconds\s*=\s*360\b',
                   "MatchSeconds = 900")

def patch_hud(text: str) -> str:
    assert 'local function action(' in text
    start = """-- P0 OWNER: deliberate lobby departure and a small, readable battle HUD.
local readyButton = button(gui, "OwnerReady", "▶ 出撃する",
    UDim2.fromOffset(154, 60), UDim2.new(.5, 0, .53, 0),
    Color3.fromRGB(45, 155, 105))
readyButton.AnchorPoint = Vector2.new(.5, .5)
readyButton.Visible = false
readyButton.MouseButton1Click:Connect(function() action("READY_TOGGLE", nil) end)
local lobbyHelp = label(gui, "OwnerLobbyGuide", UDim2.new(.72, 0, 0, 65),
    UDim2.new(.14, 0, .35, 0), Color3.fromRGB(246, 241, 208), 15)
lobbyHelp.Text = "敵城の卵を奪って自城へ！ または敵城を破壊！\\n攻撃：F／タップ　罠：T　ロビーで職業選択"
lobbyHelp.BackgroundTransparency = .4
lobbyHelp.Visible = false
local selfHp = label(gui, "OwnerNumericHP", UDim2.fromOffset(128, 28),
    UDim2.new(0, 12, 1, -112), Color3.fromRGB(255, 255, 255), 14)
selfHp.Visible = false
local function attachHealth(character: Model)
    local hum = character:WaitForChild("Humanoid", 10)
    if not hum or not hum:IsA("Humanoid") then return end
    local function renderHp()
        if hum.Parent then
            selfHp.Text = string.format("HP %d/%d",
                math.max(0, math.ceil(hum.Health)), math.ceil(hum.MaxHealth))
        end
    end
    renderHp()
    hum.HealthChanged:Connect(renderHp)
    hum:GetPropertyChangedSignal("MaxHealth"):Connect(renderHp)
end
player.CharacterAdded:Connect(attachHealth)
if player.Character then task.spawn(attachHealth, player.Character) end

"""
    text = sub_once(text, "remote.OnClientEvent:Connect(function(s)", start + "remote.OnClientEvent:Connect(function(s)")
    append = """    -- Low-interference combat: one slim numeric scoreboard, no permanent status slab.
    readyButton.Visible = s.phase == "LOBBY"
    readyButton.Text = if s.ready == true then "✓ 準備解除" else "▶ 出撃する"
    lobbyHelp.Visible = s.phase == "LOBBY"
    selfHp.Visible = s.phase == "ACTIVE"
    if s.phase == "LOBBY" then
        status.Text = if s.ready == true then "出撃待機中：全員の準備完了で開始"
            else "自分で出撃を選ぶまで試合は始まりません"
    elseif s.phase == "ACTIVE" then
        local maximum = if type(s.maxHp) == "number" then s.maxHp else 300
        local t = if type(s.time) == "number" then math.max(0, math.floor(s.time)) else 0
        top.Text = string.format("🔴城%d/%d  🔵城%d/%d  🥚%d-%d  %d:%02d",
            s.hp.RED or 0, maximum, s.hp.BLUE or 0, maximum,
            s.scores.RED or 0, s.scores.BLUE or 0,
            math.floor(t / 60), t % 60)
        status.Visible = s.carrying ~= "" or s.alarm == "WARNING"
        if s.carrying ~= "" then
            status.Text = "🥚 卵を持っている！ 自陣へ戻ろう"
        end
    else
        status.Visible = true
    end
"""
    text = sub_once(text, "    status.Text = phaseText(s)",
        "    status.Text = phaseText(s)\n" + append)
    assert text.count('action("READY_TOGGLE", nil)') == 1
    return text

def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("P0_GAMECORE_OFF_BYTE_EXACT")
        return False
    before = inventory(dist)
    assert len(before) == 66, ("REQUIRE_OFFICIAL_RC66", len(before))
    assert all(path in before for path in (GAME, CONFIG, HUD))
    expected = {path: blob(raw) for path, raw in sorted(before.items())}
    lf, ff = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock = json.loads(lf.read_text("utf8"))
    feature = json.loads(ff.read_text("utf8"))
    assert lock["total_scripts"] == 66 and lock["blobs"] == expected, "SOURCE_LOCK_DRIFT"
    assert feature["total_sources"] == 66 and feature["source_gitblobs"] == expected, "FEATURE_LOCK_DRIFT"
    assert ID not in feature["feature_flags"], "DUPLICATE_APPLICATION"
    after = dict(before)
    after[GAME] = patch_game(before[GAME].decode("utf8")).encode("utf8")
    after[CONFIG] = patch_config(before[CONFIG].decode("utf8")).encode("utf8")
    after[HUD] = patch_hud(before[HUD].decode("utf8")).encode("utf8")
    assert {p for p in before if after[p] != before[p]} == {GAME, CONFIG, HUD}
    assert all(before[p] == after[p] for p in before if p not in {GAME, CONFIG, HUD})
    pins = {path: blob(raw) for path, raw in sorted(after.items())}
    lock["blobs"] = pins
    lock["p0_emergency_core"] = {
        "feature": ID, "modified": [GAME, CONFIG, HUD],
        "unchanged_source_count": 63, "total_sources": 66,
        "studio_bot_ai": "NOT_IMPLEMENTED", "castle_world": "NOT_REBUILT",
        "studio_owner_fun": "NOT_TESTED",
        "rollback": "omit final apply_p0_ready_15min.py step; original 66 source bytes restored"
    }
    feature["source_gitblobs"] = pins
    feature["feature_flags"][ID] = True
    # Validate transformations and old metadata before touching scratch dist.
    for path in (GAME, CONFIG, HUD):
        (dist / "src" / path).write_bytes(after[path])
    lf.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", "utf8")
    ff.write_text(json.dumps(feature, ensure_ascii=False, indent=2) + "\n", "utf8")
    assert inventory(dist) == after
    print("P0_GAMECORE_READY_15M_NUMERIC_HUD_SOURCE_LOCK_PASS_66")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--enabled", choices=("true", "false"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.enabled == "true")
