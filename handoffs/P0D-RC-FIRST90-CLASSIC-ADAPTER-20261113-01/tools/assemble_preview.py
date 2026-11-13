#!/usr/bin/env python3
"""Source-lock exact official S1 Game and embed first90 in own unpublished preview.
Never writes releases/**, official RC, main, or another handoff.
"""
import argparse
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SOURCE = REPO / "releases" / "P0D_S1_KIDS_RC01"
DIST = ROOT / "dist" / "TRAP_RAIDERS_S1_FIRST90_CLASSIC_PRIVATE_UNPUBLISHED"
FROZEN_RC_SHA = "1263a03701211a652b99b91d2339575dc8104eff"
LOCK = {
    "src/server/Game.server.luau": "7c5229f600f17537bc1bbbb0b96b6a2435875374",
    "src/client/FirstMinuteCoach.client.luau": "63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9",
    "src/shared/FirstMinuteModel.luau": "fcdc399bf95b6cd0532691718f5a54e8a4fd84b4",
    "default.project.json": "ec2918829fa6d87610e42fdcd681a1a31335d962",
}

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def require_exactly_once(content, needle, label):
    if content.count(needle) != 1:
        raise ValueError(f"{label} expected 1 anchor, got {content.count(needle)}")
    return content

def position(name):
    return (
        "{x = " + name + ".Position.X, y = " + name + ".Position.Y, z = "
        + name + ".Position.Z}"
    )

def server_patch(source):
    require_exactly_once(source,
        'local TrapRules = require(script.Parent:WaitForChild("S1TrapRules"))',
        "original rules require")
    source = source.replace(
        'local TrapRules = require(script.Parent:WaitForChild("S1TrapRules"))',
        'local TrapRules = require(script.Parent:WaitForChild("S1TrapRules"))\n'
        'local First90Classic = require(script.Parent:WaitForChild("S1First90ClassicWaypointRules"))',
        1)
    anchor = '    return {\n        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,'
    require_exactly_once(source, anchor, "original snapshotFor table")
    addition = '''
    -- First90 preview: ONLY original Game owns this snapshot, objective and Remote.
    -- Derive exact positions from canonical MapBuilder, never from client requests.
    local ownTeam = getTeamName(player)
    local enemyTeam = if ownTeam == "RED" then "BLUE"
        elseif ownTeam == "BLUE" then "RED" else nil
    local ownBase = map.teams[ownTeam]
    local enemyBase = if enemyTeam then map.teams[enemyTeam] else nil
    local isAlive = healthy(player)
    local ownScore = if ownBase then ownBase.scorePad else nil
    local enemyEgg = if enemyBase then enemyBase.egg else nil
    local first90Target = First90Classic.select({
        serial = match.serial, phase = match.phase, team = ownTeam,
        alive = isAlive, elapsedSeconds = now - match.startedAt,
        carryingEgg = carry[player] ~= nil,
        ownEggHome = ownBase ~= nil and match.eggOwners[ownTeam] == nil,
        ownScorePad = if ownScore then {x = ownScore.Position.X,
            y = ownScore.Position.Y, z = ownScore.Position.Z} else nil,
        enemyEggFree = enemyTeam ~= nil and match.eggOwners[enemyTeam] == nil,
        enemyPromptEnabled = enemyBase ~= nil and enemyBase.eggPrompt.Enabled,
        enemyEggVisible = enemyEgg ~= nil and enemyEgg.Transparency == 0,
        enemyEgg = if enemyEgg then {x = enemyEgg.Position.X,
            y = enemyEgg.Position.Y, z = enemyEgg.Position.Z} else nil,
    })
'''
    source = source.replace(anchor, addition + anchor, 1)
    require_exactly_once(source, '        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,', "snapshot")
    source = source.replace(
        '        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,',
        '        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,\n'
        '        first90Target = first90Target,', 1)
    # Nonpublished Studio SOLO onboarding. Public server still uses original min2,
    # two populated teams and original TEAM_EMPTY outcomes.
    require_exactly_once(source, 'local Players = game:GetService("Players")', "original Players service")
    source = source.replace('local Players = game:GetService("Players")',
        'local Players = game:GetService("Players")\\n'
        'local RunService = game:GetService("RunService")', 1)
    require_exactly_once(source, 'local First90Classic = require(script.Parent:WaitForChild("S1First90ClassicWaypointRules"))', "new target rules")
    source = source.replace(
        'local First90Classic = require(script.Parent:WaitForChild("S1First90ClassicWaypointRules"))',
        'local First90Classic = require(script.Parent:WaitForChild("S1First90ClassicWaypointRules"))\\n'
        'local StudioSolo = require(script.Parent:WaitForChild("StudioSoloPreviewRules"))', 1)
    solo_checks = [
        ('if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then',
         'if StudioSolo.canStart(RunService:IsStudio(), count, teamCount("RED"),\\n'
         '                teamCount("BLUE"), Config.MinPlayers) then'),
        ('if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then',
         'if not StudioSolo.canStart(RunService:IsStudio(), count, teamCount("RED"),\\n'
         '                teamCount("BLUE"), Config.MinPlayers) then'),
        ('if teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")\\n'
         '        elseif teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")\\n'
         '        elseif now >= match.deadline then',
         'local emptyWinner = StudioSolo.emptyWinner(RunService:IsStudio(), count,\\n'
         '            teamCount("RED"), teamCount("BLUE"))\\n'
         '        if emptyWinner then stopRound(emptyWinner, "TEAM_EMPTY")\\n'
         '        elseif now >= match.deadline then'),
    ]
    for old, new in solo_checks:
        require_exactly_once(source, old, "original public countdown/empty team gate")
        source = source.replace(old, new, 1)
    return source

def coach_patch(source):
    anchor = 'local state = Model.new()\nlocal function repaint()\n'
    require_exactly_once(source, anchor, "original only Coach state / repaint")
    extra = '''local state = Model.new()
-- Reuses the same existing Coach GUI and the same original snapshot remote.
-- The client's direction and distance are cosmetic: never game authority.
local function first90Text(packet)
    if type(packet) ~= "table" or packet.phase ~= "ACTIVE"
        or (packet.team ~= "RED" and packet.team ~= "BLUE") then return nil end
    local target = packet.first90Target
    if type(target) ~= "table" then return nil end
    if target.kind == "RECOVER" then
        return "🛡 自分の卵が盗まれた！ 取り返してから納品しよう"
    end
    if target.kind ~= "EGG" and target.kind ~= "HOME" then return nil end
    if type(target.x) ~= "number" or type(target.y) ~= "number"
        or type(target.z) ~= "number" or target.x ~= target.x
        or target.y ~= target.y or target.z ~= target.z
        or math.abs(target.x) > 200 or target.y < -50 or target.y > 100
        or math.abs(target.z) > 120 then return nil end
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root or not root:IsA("BasePart") then
        return if target.kind == "EGG" then "🥚 敵の卵を探そう！" else "🏰 自陣の納品台を探そう！"
    end
    local displacement = Vector3.new(target.x - root.Position.X,
        0, target.z - root.Position.Z)
    local meters = math.floor(displacement.Magnitude + .5)
    if meters > 10000 then return nil end
    local direction = "●"
    if meters >= 3 then
        local forward = root.CFrame.LookVector:Dot(displacement.Unit)
        local right = root.CFrame.RightVector:Dot(displacement.Unit)
        if forward > math.abs(right) * 0.6 then direction = "↑"
        elseif forward < -math.abs(right) * 0.6 then direction = "↓"
        elseif right >= 0 then direction = "→"
        else direction = "←" end
    end
    local kind = if target.kind == "EGG" then "🥚 敵の卵" else "🏰 納品台"
    return kind .. " " .. direction .. " 約" .. tostring(meters) .. "歩"
end

local function repaint()
'''
    source = source.replace(anchor, extra, 1)
    old = '''    local v = Model.view(state, time())
    panel.Visible = v ~= nil and v.visible
    help.Visible = state.latest ~= nil and not panel.Visible
    if not v or not v.visible then return end
    title.Text = v.title
    detail.Text = v.detail
    title.TextColor3 = if v.tone == "success" then Color3.fromRGB(156, 252, 178)
        else Color3.fromRGB(255, 222, 113)
'''
    require_exactly_once(source, old, "original Coach render body")
    new = '''    local v = Model.view(state, time())
    local route = first90Text(state.latest)
    local baseVisible = v ~= nil and v.visible
    local visible = not state.dismissed and (baseVisible or route ~= nil)
    panel.Visible = visible
    help.Visible = state.latest ~= nil and not visible
    if not visible then return end
    title.Text = if baseVisible then v.title else "次はこの目標へ！"
    detail.Text = if route and baseVisible then v.detail .. "\\\\n" .. route
        elseif route then route else v.detail
    title.TextColor3 = if baseVisible and v.tone == "success"
        then Color3.fromRGB(156, 252, 178)
        else Color3.fromRGB(255, 222, 113)
'''
    # Double-escaped above in Python source is deliberate: replacement Luau
    # source must have the "\n" token, not a literal line inside the string.
    new = new.replace('v.detail .. "\\\\n" .. route',
                      'v.detail .. "\\n" .. route')
    source = source.replace(old, new, 1)
    require_exactly_once(source, 'panel.Size = UDim2.new(0.62, 0, 0, 67)', "original panel height")
    source = source.replace('panel.Size = UDim2.new(0.62, 0, 0, 67)',
                            'panel.Size = UDim2.new(0.62, 0, 0, 86)', 1)
    source = source.replace('constraint.MaxSize = Vector2.new(530, 74)',
                            'constraint.MaxSize = Vector2.new(530, 96)', 1)
    source = source.replace('constraint.MinSize = Vector2.new(220, 63)',
                            'constraint.MinSize = Vector2.new(220, 80)', 1)
    return source

def assemble():
    for path, required_sha in LOCK.items():
        p = SOURCE / path
        actual = blob(p.read_bytes())
        assert actual == required_sha, f"frozen official RC source changed {path}: {actual}"

    assert (ROOT / "src/S1First90ClassicWaypointRules.luau").is_file()
    assert (ROOT / "src/StudioSoloPreviewRules.luau").is_file()
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SOURCE / "src", DIST / "src")
    shutil.copy2(SOURCE / "default.project.json", DIST / "default.project.json")
    original = sorted((SOURCE / "src").rglob("*.luau"))
    assert len(original) == 21, len(original)

    game = DIST / "src/server/Game.server.luau"
    coach = DIST / "src/client/FirstMinuteCoach.client.luau"
    game.write_text(server_patch(game.read_text(encoding="utf8")), encoding="utf8")
    coach.write_text(coach_patch(coach.read_text(encoding="utf8")), encoding="utf8")
    shutil.copy2(ROOT / "src/S1First90ClassicWaypointRules.luau",
                 DIST / "src/server/S1First90ClassicWaypointRules.luau")
    shutil.copy2(ROOT / "src/StudioSoloPreviewRules.luau",
                 DIST / "src/server/StudioSoloPreviewRules.luau")
    scripts = sorted((DIST / "src").rglob("*.luau"))
    assert len(scripts) == 23, len(scripts)
    changed = []
    for p in original:
        rel = p.relative_to(SOURCE)
        if p.read_bytes() != (DIST / rel).read_bytes():
            changed.append(rel.as_posix())
    assert changed == ["src/client/FirstMinuteCoach.client.luau",
                       "src/server/Game.server.luau"], changed
    assert blob((DIST / "src/shared/FirstMinuteModel.luau").read_bytes()) == LOCK["src/shared/FirstMinuteModel.luau"]
    runtime_game = game.read_text(encoding="utf8")
    assert runtime_game.count('Instance.new("RemoteEvent")') == 1
    assert runtime_game.count('remote.OnServerEvent:Connect') == 1
    assert runtime_game.count('local function snapshotFor(player: Player)') == 1
    assert runtime_game.count('first90Target = first90Target,') == 1
    assert len(list((DIST / "src/server").glob("Game.server.luau"))) == 1
    assert not any("DataStore" in p.name for p in (DIST / "src/server").glob("*First90*"))
    readme = (ROOT / "README_JP.md").read_text(encoding="utf8")
    assert "NOT_MOUNTED" in readme  # pre-existing adapter status, not preview
    manifest = {
        "status": "ONE_GAME_UNPUBLISHED_PREVIEW_NOT_OFFICIAL_RC",
        "official_rc_sha_frozen": FROZEN_RC_SHA,
        "source_count": len(scripts),
        "original_count": len(original),
        "unchanged_original_count": 19,
        "changed_original_paths": changed,
        "added_paths": ["src/server/S1First90ClassicWaypointRules.luau",
                        "src/server/StudioSoloPreviewRules.luau"],
        "studio_only_single_client_practice": True,
        "public_server_min_two_teams_unchanged": True,
        "single_game_remote": True,
        "first90_server_snapshot": True,
        "first90_visible_existing_coach": True,
        "official_rc_adopted": False,
        "real_roblox_studio_2client": "NOT_TESTED",
        "owner_fun": "NOT_TESTED",
        "published": False,
        "source_git_sha1": {
            p.relative_to(DIST).as_posix(): blob(p.read_bytes()) for p in scripts
        },
    }
    (DIST / "SOURCE_LOCK.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("P0D_S1_FIRST90_CLASSIC_ASSEMBLED_23_LUAU_19_ORIGINAL_UNCHANGED_PASS")
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--assemble", action="store_true")
    args = parser.parse_args()
    assert args.assemble, "explicit --assemble only"
    assemble()
