#!/usr/bin/env python3
"""P0D-018 PRIVATE capture overlay on exact RC66. Source-only; never edits official."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parent
GAME="server/Game.server.luau"
MODULE="server/CapturePolicy.luau"
POLICY=ROOT/"features/capture/CapturePolicy.luau"
MANIFEST=ROOT/"features/capture/PREP_SOURCE_LOCK.json"
def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def scripts(dist):
    return {p.relative_to(dist/"src").as_posix():p.read_bytes()
            for p in sorted((dist/"src").rglob("*.luau"))}
def change(txt,old,new):
    assert txt.count(old)==1,("CAPTURE_GAME_ANCHOR_DRIFT",old[:70],txt.count(old))
    return txt.replace(old,new,1)
HELPER=r'''
-- PREP P0D-018: no client target/coordinate, no extra Remote or scheduler.
local function tryTrapperCapture(player:Player,root:BasePart,team:string,now:number)
    local flag=ServerStorage:FindFirstChild("P0D_CAPTURE_PVP_V1")
    if not RunService:IsStudio() or studioSoloRoundStarted
        or not flag or not flag:IsA("BoolValue") or flag.Value~=true
        or match.phase~="ACTIVE" or slowed[player]~=nil then return end
    local nearest=nil
    local nearestRoot=nil
    local nearestHum=nil
    local best=Capture.RANGE+.01
    for _,other in ipairs(Players:GetPlayers()) do
        if other~=player and getTeamName(other)==Rules.opponent(team)
            and slowed[other]==nil and carry[other]==nil then
            local alive,otherRoot,otherHum=healthy(other)
            if alive and otherRoot and otherHum
                and now>=(invulnUntil[other] or 0) then
                local delta=otherRoot.Position-root.Position
                local distance=delta.Magnitude
                local forward=if distance>.001 then root.CFrame.LookVector:Dot(delta.Unit) else 1
                if distance<best and forward>=.25 then
                    local params=RaycastParams.new()
                    params.FilterType=Enum.RaycastFilterType.Exclude
                    params.FilterDescendantsInstances={player.Character :: Model,horde.folder}
                    local hit=workspace:Raycast(root.Position,delta,params)
                    if hit==nil or (other.Character~=nil
                        and hit.Instance:IsDescendantOf(other.Character)) then
                        nearest=other;nearestRoot=otherRoot;nearestHum=otherHum;best=distance
                    end
                end
            end
        end
    end
    if not nearest or not nearestRoot or not nearestHum then return end
    local accepted=Capture.begin(player,nearest,{
        now=now,epoch=match.serial,phase=match.phase,role="TRAPPER",
        attackerTeam=team,targetTeam=getTeamName(nearest),
        attackerAlive=true,targetAlive=true,
        targetInvulnerable=now<(invulnUntil[nearest] or 0),
        attackerCarrying=carry[player]~=nil,targetCarrying=carry[nearest]~=nil,
        serverLineOfSight=true,serverDistance=best,
    })
    if not accepted then return end
    stopWind(nearest) -- original NET also clears speed boosts before binding
    local glow=Instance.new("Highlight")
    glow.Name="P0D018_CAPTURE_VISIBLE"
    glow.FillColor=Color3.fromRGB(225,123,245)
    glow.OutlineColor=Color3.fromRGB(255,255,255)
    glow.FillTransparency=.63
    glow.Parent=nearest.Character
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="P0D018_RESCUE"
    prompt.ActionText="救出"
    prompt.ObjectText="仲間"
    prompt.HoldDuration=.25
    prompt.RequiresLineOfSight=true
    prompt.MaxActivationDistance=Capture.RESCUE_RANGE
    prompt.Parent=nearestRoot
    -- Existing single Game restoreSlow/tickTraps owns all movement restoration.
    slowed[nearest]={hum=nearestHum,untilAt=now+Capture.DURATION,
        kind="P0D_CAPTURE",owner=player,startedAt=now,
        jumpPower=nearestHum.JumpPower,jumpHeight=nearestHum.JumpHeight,
        highlight=glow,prompt=prompt}
    nearestHum.WalkSpeed=0
    nearestHum.JumpPower=0
    nearestHum.JumpHeight=0
    prompt.Triggered:Connect(function(rescuer:Player)
        local record=slowed[nearest]
        if not record or record.kind~="P0D_CAPTURE"
            or record.hum~=nearestHum or record.owner~=player
            or match.phase~="ACTIVE" or studioSoloRoundStarted
            or flag.Parent==nil or flag.Value~=true or slowed[rescuer]~=nil then return end
        local alive,from=healthy(rescuer)
        local targetAlive,to=healthy(nearest)
        if not alive or not targetAlive or not from or not to then return end
        local direction=to.Position-from.Position
        if direction.Magnitude>Capture.RESCUE_RANGE then return end
        local params=RaycastParams.new()
        params.FilterType=Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances={rescuer.Character :: Model,horde.folder}
        local hit=workspace:Raycast(from.Position,direction,params)
        if hit and (nearest.Character==nil
            or not hit.Instance:IsDescendantOf(nearest.Character)) then return end
        if Capture.rescue(rescuer,nearest,{
            now=serverNow(),epoch=match.serial,phase=match.phase,
            rescuerAlive=alive,targetAlive=targetAlive,
            rescuerTeam=getTeamName(rescuer),serverDistance=direction.Magnitude,
        }) then restoreSlow(nearest);broadcast() end
    end)
    broadcast()
end
'''
def patch_game(txt):
    txt=change(txt,'local MusouBind = require(script.Parent:WaitForChild("MusouBindRules"))',
        'local MusouBind = require(script.Parent:WaitForChild("MusouBindRules"))\n'
        'local Capture = require(script.Parent:WaitForChild("CapturePolicy"))')
    txt=change(txt,
        'local function restoreSlow(player: Player)\n    local record = slowed[player]\n    slowed[player] = nil',
        'local function restoreSlow(player: Player)\n    local record = slowed[player]\n'
        '    slowed[player] = nil\n'
        '    if record and record.kind=="P0D_CAPTURE" then\n'
        '        Capture.release(player)\n'
        '        if record.prompt and record.prompt.Parent then record.prompt:Destroy() end\n'
        '    end')
    txt=change(txt,'    for player, _ in pairs(slowed) do restoreSlow(player) end\nend',
        '    for player, _ in pairs(slowed) do restoreSlow(player) end\n'
        '    Capture.clearRound()\nend')
    txt=change(txt,'local function useSevenJob(player:Player,data:any)',
        HELPER+'local function useSevenJob(player:Player,data:any)')
    txt=change(txt,'    sevenJobLastUse[player]=now',
        '    if job=="TRAPPER" then tryTrapperCapture(player,root,team,now) end\n'
        '    sevenJobLastUse[player]=now')
    txt=change(txt,
        'TrapRules.shouldTrigger({',
        '(slowed[player]==nil or slowed[player].kind~="P0D_CAPTURE") and TrapRules.shouldTrigger({')
    txt=change(txt,
        '    tickTraps(now)\n',
        '    tickTraps(now)\n'
        '    local captureGate=ServerStorage:FindFirstChild("P0D_CAPTURE_PVP_V1")\n'
        '    if captureGate==nil or not captureGate:IsA("BoolValue")\n'
        '        or captureGate.Value~=true then\n'
        '        for other,record in pairs(slowed) do\n'
        '            if record.kind=="P0D_CAPTURE" then restoreSlow(other) end\n'
        '        end\n'
        '    end\n')
    txt=change(txt,'Players.PlayerRemoving:Connect(function(player)',
        'Players.PlayerRemoving:Connect(function(player)\n'
        '    for other,rec in pairs(slowed) do\n'
        '        if rec.kind=="P0D_CAPTURE" and rec.owner==player then restoreSlow(other) end\n'
        '    end\n'
        '    Capture.forget(player)')
    txt=change(txt,'player.CharacterAdded:Connect(function(character)',
        'player.CharacterAdded:Connect(function(character)\n'
        '        if slowed[player] and slowed[player].kind=="P0D_CAPTURE" then\n'
        '            restoreSlow(player)\n'
        '        end')
    assert txt.count('remote.OnServerEvent:Connect(')==1
    assert txt.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert txt.count('local function tryTrapperCapture(')==1
    assert txt.count('Capture.begin(player,nearest,')==1
    assert txt.count('Capture.rescue(rescuer,nearest,')==1
    assert txt.count('Capture.clearRound()')==1
    assert 'elseif data.action == "NET_THROW" then applyNet(player,data)' in txt
    assert 'elseif data.action == "JOB_SKILL" then useSevenJob(player,data)' in txt
    return txt
def apply(dist,enabled):
    if not enabled:
        print("P0D018_CAPTURE_OFF_PRESERVES_EXACT_RC66_ALL_BYTES")
        return False
    manifest=json.loads(MANIFEST.read_text("utf8"))
    assert manifest["feature_id"]=="P0D-018" and manifest["game_wired"] is False
    original=scripts(dist)
    assert len(original)==66 and GAME in original and MODULE not in original
    source_lock=dist/"SOURCE_LOCK.json"
    feature_lock=dist/"RC_FEATURE_LOCK.json"
    project=dist/"default.project.json"
    s=json.loads(source_lock.read_text("utf8"))
    f=json.loads(feature_lock.read_text("utf8"))
    cfg=json.loads(project.read_text("utf8"))
    pins={p:blob(b) for p,b in sorted(original.items())}
    assert s["total_scripts"]==66 and s["blobs"]==pins
    assert f["total_sources"]==66 and f["source_gitblobs"]==pins
    assert s["rc_twin_bond_overlay"]["new_game_blob"]==pins[GAME]
    assert f["feature_flags"]["TWIN_BOND_PVE_COMPANION_V1"] is True
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    assert "P0D_CAPTURE_PVP_V1" not in cfg["tree"]["ServerStorage"]
    pure=POLICY.read_bytes()
    assert blob(pure)==manifest["module_blob"]
    updated=patch_game(original[GAME].decode("utf8")).encode("utf8")
    new={**original,GAME:updated,MODULE:pure}
    assert len(new)==67
    assert all(new[p]==original[p] for p in original if p!=GAME)
    assert updated.count(b'Instance.new("RemoteEvent")')==original[GAME].count(b'Instance.new("RemoteEvent")')
    next_pins={p:blob(b) for p,b in sorted(new.items())}
    cfg["tree"]["ServerStorage"]["P0D_CAPTURE_PVP_V1"]={
        "$className":"BoolValue","$properties":{"Value":True}}
    s["total_scripts"]=67;s["blobs"]=next_pins
    s["rc_capture_prep_overlay"]={"id":"P0D-018","from":66,"to":67,
        "original_Game":pins[GAME],"patched_Game":next_pins[GAME],
        "pure_module":next_pins[MODULE],"single_Game_Remote_Store":True,
        "studio":"NOT_TESTED","official_rc_adopted":False,
        "rollback":"disable overlay; exact source/project/locks from RC66 unchanged"}
    f["total_sources"]=67;f["source_gitblobs"]=next_pins
    f["feature_flags"]["P0D_CAPTURE_PVP_V1"]=True
    # Mutation only after source-exact preflight; always on the separate scratch dist.
    (dist/"src"/GAME).write_bytes(updated)
    (dist/"src"/MODULE).write_bytes(pure)
    project.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n","utf8")
    source_lock.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n","utf8")
    feature_lock.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n","utf8")
    assert scripts(dist)==new
    print("P0D018_PRIVATE67_EXISTING_GAME_CAPTURE_ONE_CHANGED_ONE_MODULE_PASS")
    return True
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dist",type=Path,required=True)
    parser.add_argument("--enabled",choices=("true","false"),required=True)
    args=parser.parse_args()
    apply(args.dist,args.enabled=="true")
