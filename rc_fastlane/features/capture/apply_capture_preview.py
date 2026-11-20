#!/usr/bin/env python3
"""P0D-018: isolated 66->67 source-exact Studio capture preview.

Never write to official dist, any Git branch, or original 66-byte source.
Extends the ONE existing Game / Remote / slowed/restoreSlow; no second Game.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
CAPTURE=ROOT/"rc_fastlane/features/capture/CapturePolicy.luau"
PREP=ROOT/"rc_fastlane/features/capture/PREP_SOURCE_LOCK.json"
GAME="server/Game.server.luau"
MODULE="server/CapturePolicy.luau"
OFFICIAL_GAME_BLOB="e6f47b31e37a9209d2ddc5a52647498d0747ee79"
PARENT_COUNT=66

def blob(b: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def replace_once(txt: str, old: str, new: str)->str:
    if txt.count(old)!=1:
        raise AssertionError(("CAPTURE_GAME_ANCHOR_NOT_UNIQUE",old[:90],txt.count(old)))
    return txt.replace(old,new,1)

def patch_game(raw: bytes)->bytes:
    if blob(raw)!=OFFICIAL_GAME_BLOB:
        raise AssertionError("CAPTURE_ORIGINAL_CANONICAL66_GAME_BLOB_DRIFT")
    text=raw.decode("utf8")
    text=replace_once(text,
        'local MusouBind = require(script.Parent:WaitForChild("MusouBindRules"))',
        'local MusouBind = require(script.Parent:WaitForChild("MusouBindRules"))\n'
        'local Capture = require(script.Parent:WaitForChild("CapturePolicy"))')
    text=replace_once(text,
        'local record = slowed[player]\n    slowed[player] = nil',
        'local record = slowed[player]\n'
        '    if record and record.kind=="CAPTURE" then Capture.release(player) end\n'
        '    if record and record.captureVisual and record.captureVisual.Parent then\n'
        '        record.captureVisual:Destroy()\n'
        '    end\n'
        '    slowed[player] = nil')
    text=replace_once(text,
        '    table.clear(traps)\n    for player, _ in pairs(slowed) do restoreSlow(player) end',
        '    table.clear(traps)\n'
        '    for player, _ in pairs(slowed) do restoreSlow(player) end\n'
        '    Capture.clearRound()')
    text=replace_once(text,
        'if not alive or hum ~= record.hum or now >= record.untilAt then',
        'if not alive or hum ~= record.hum or now >= record.untilAt\n'
        '            or (record.kind=="CAPTURE" and Capture.status(player,now,match.serial)==nil) then')
    text=replace_once(text,
        'and not (slowed[player] and slowed[player].kind=="NET")',
        'and not (slowed[player] and (slowed[player].kind=="NET" or slowed[player].kind=="CAPTURE"))')
    text=replace_once(text,
        'if rec and rec.kind=="NET" and targetOk and targetRoot then\n'
        '                local delta=targetRoot.Position-root.Position\n'
        '                if delta.Magnitude<=MusouBind.RESCUE_RANGE then',
        'if rec and (rec.kind=="NET" or rec.kind=="CAPTURE") and targetOk and targetRoot then\n'
        '                local delta=targetRoot.Position-root.Position\n'
        '                local rescueRange=if rec.kind=="CAPTURE" then Capture.RESCUE_RANGE else MusouBind.RESCUE_RANGE\n'
        '                if delta.Magnitude<=rescueRange then')
    text=replace_once(text,
        'if other~=player and rec and rec.kind=="NET" then',
        'if other~=player and rec and (rec.kind=="NET" or rec.kind=="CAPTURE") then')
    rescue='''                if MusouBind.canRescue({
                    phase=match.phase,teammate=getTeamName(player)~="NONE"
                        and getTeamName(player)==getTeamName(other),
                    alive=alive,targetBound=true,visible=visible,
                    distance=delta.Magnitude,
                }) then
                    restoreSlow(other)
                    broadcast()
                    return
                end'''
    rescueNext='''                if rec.kind=="CAPTURE" then
                    -- Never trust client positions, rescue targets or LOS.
                    if visible and not slowed[player]
                        and Capture.rescue(player,other,{
                            now=now,epoch=match.serial,phase=match.phase,
                            rescuerAlive=alive,targetAlive=ok,
                            rescuerTeam=getTeamName(player),
                            serverDistance=delta.Magnitude,
                        }) then
                        restoreSlow(other)
                        broadcast()
                        return
                    end
                elseif MusouBind.canRescue({
                    phase=match.phase,teammate=getTeamName(player)~="NONE"
                        and getTeamName(player)==getTeamName(other),
                    alive=alive,targetBound=true,visible=visible,
                    distance=delta.Magnitude,
                }) then
                    restoreSlow(other)
                    broadcast()
                    return
                end'''
    text=replace_once(text,rescue,rescueNext)
    # Guaranteed owner-leave cleanup; tickTraps restores anybody whose bond is gone.
    text=replace_once(text,
        '    stopWind(player)\n    restoreSlow(player)\n    for i = #traps, 1, -1 do',
        '    stopWind(player)\n    restoreSlow(player)\n'
        '    Capture.forget(player)\n'
        '    for i = #traps, 1, -1 do')
    text=replace_once(text,
        '        hum.Died:Connect(function()\n            stopWind(player)\n            restoreSlow(player)',
        '        hum.Died:Connect(function()\n            stopWind(player)\n            restoreSlow(player)\n'
        '            Capture.forget(player)')
    helper='''-- P0D-018 optional advanced TRAPPER capture. Same Game/Remote/seq/movement authority.
-- The existing Guardian NET remains unchanged: 1.2s, independent RESCUE/BREAK_FREE.
local function tryAdvancedCapture(player:Player,now:number,root:BasePart,team:string)
    local captureFlag=ServerStorage:FindFirstChild("P0D_ENABLE_ADV_CAPTURE_V1")
    if not RunService:IsStudio() or not captureFlag
        or not captureFlag:IsA("BoolValue") or captureFlag.Value~=true
        or match.phase~="ACTIVE" or sevenJobs[player]~="TRAPPER"
        or carry[player]~=nil or slowed[player]~=nil then return end
    local enemyTeam=Rules.opponent(team)
    local nearest:Player?=nil
    local best=Capture.RANGE+.001
    local look=root.CFrame.LookVector
    for _,other in ipairs(Players:GetPlayers()) do
        if other~=player and getTeamName(other)==enemyTeam
            and slowed[other]==nil and carry[other]==nil then
            local ok,targetRoot=healthy(other)
            if ok and targetRoot then
                local delta=targetRoot.Position-root.Position
                local dist=delta.Magnitude
                local facing=if dist>.001 then look:Dot(delta.Unit) else 1
                if dist<best and facing>=.25
                    and now>=(invulnUntil[other] or 0) then
                    local params=RaycastParams.new()
                    params.FilterType=Enum.RaycastFilterType.Exclude
                    params.FilterDescendantsInstances={player.Character :: Model,horde.folder}
                    local hit=workspace:Raycast(root.Position,delta,params)
                    if hit==nil or (other.Character~=nil
                        and hit.Instance:IsDescendantOf(other.Character)) then
                        nearest=other
                        best=dist
                    end
                end
            end
        end
    end
    if not nearest then return end
    local alive,targetRoot,hum=healthy(nearest)
    if not alive or not targetRoot or not hum or slowed[nearest] then return end
    local accepted=Capture.begin(player,nearest,{
        now=now,epoch=match.serial,phase=match.phase,
        role=sevenJobs[player],attackerTeam=team,targetTeam=getTeamName(nearest),
        attackerAlive=true,targetAlive=alive,targetInvulnerable=now<(invulnUntil[nearest] or 0),
        attackerCarrying=carry[player]~=nil,targetCarrying=carry[nearest]~=nil,
        serverLineOfSight=true,serverDistance=best,
    })
    if not accepted then return end
    stopWind(nearest)
    local cage=Instance.new("Model")
    cage.Name="P0D_CAPTURE_VISIBLE_4S_ALLY_RESCUE"
    cage.Parent=nearest.Character
    -- Four bounded, non-colliding 3D bars welded to the real server target.
    for _,offset in ipairs({
        Vector3.new(1.8,0,1.8),Vector3.new(-1.8,0,1.8),
        Vector3.new(1.8,0,-1.8),Vector3.new(-1.8,0,-1.8)}) do
        local bar=Instance.new("Part")
        bar.Name="CAPTURE_CAGE_NEON_BAR"
        bar.Size=Vector3.new(.2,4,.2)
        bar.Material=Enum.Material.Neon
        bar.Color=Color3.fromRGB(249,169,67)
        bar.Anchored=false
        bar.Massless=true
        bar.CanCollide=false
        bar.CanTouch=false
        bar.CanQuery=false
        bar.CFrame=targetRoot.CFrame*CFrame.new(offset)
        bar.Parent=cage
        local weld=Instance.new("WeldConstraint")
        weld.Part0=targetRoot
        weld.Part1=bar
        weld.Parent=bar
    end
    local sign=Instance.new("BillboardGui")
    sign.Name="CAPTURE_SHORT_RESCUE_HINT"
    sign.Size=UDim2.fromOffset(160,35)
    sign.StudsOffsetWorldSpace=Vector3.new(0,3.6,0)
    sign.AlwaysOnTop=true
    sign.Adornee=targetRoot -- the GUI is grouped under the removable cage Model
    sign.Parent=cage
    local txt=Instance.new("TextLabel")
    txt.Size=UDim2.fromScale(1,1)
    txt.BackgroundTransparency=.3
    txt.BackgroundColor3=Color3.fromRGB(25,35,44)
    txt.TextColor3=Color3.fromRGB(255,235,171)
    txt.TextScaled=true
    txt.Text="🪤 捕獲！ 味方が救助"
    txt.Parent=sign
    slowed[nearest]={
        hum=hum,untilAt=now+Capture.DURATION,kind="CAPTURE",
        jumpPower=hum.JumpPower,jumpHeight=hum.JumpHeight,
        captureVisual=cage,owner=player,
    }
    hum.WalkSpeed=0
    hum.JumpPower=0
    hum.JumpHeight=0
    broadcast()
end

'''
    text=replace_once(text,
        'local function useSevenJob(player:Player,data:any)',
        helper+'local function useSevenJob(player:Player,data:any)')
    old='''    elseif job=="TRAPPER" then
        for _,d in ipairs({facing,-facing,Vector3.new(-facing.Z,0,facing.X),
            Vector3.new(facing.Z,0,-facing.X)}) do
            sevenJobStrike(player,root.Position,d,12)
        end'''
    new='''    elseif job=="TRAPPER" then
        for _,d in ipairs({facing,-facing,Vector3.new(-facing.Z,0,facing.X),
            Vector3.new(facing.Z,0,-facing.X)}) do
            sevenJobStrike(player,root.Position,d,12)
        end
        tryAdvancedCapture(player,now,root,team)'''
    text=replace_once(text,old,new)
    assert text.count('remote.OnServerEvent:Connect(')==1
    assert text.count('tryAdvancedCapture(player,now,root,team)')==1
    assert text.count('Capture.begin(')==1 and text.count('Capture.rescue(')==1
    assert text.count('slowed[nearest]={')==2 # original NET + advanced capture
    assert 'CanCollide=false' in text and 'CanQuery=false' in text
    assert 'P0D_ENABLE_ADV_CAPTURE_V1' in text
    return text.encode("utf8")

def snapshot(root:Path)->dict[str,bytes]:
    src=root/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def apply(srcdist:Path,out:Path,enabled:bool)->None:
    if not enabled:
        print("P0D018_OFF_ZERO_WRITE_TO_SOURCE_OR_OUTPUT_PASS")
        return
    if srcdist.resolve()==out.resolve() or out.exists():
        raise AssertionError("CAPTURE_NEVER_OVERWRITE_SOURCE_OR_EXISTING_PREVIEW")
    policy=CAPTURE.read_bytes()
    author=json.loads(PREP.read_text("utf8"))
    if blob(policy)!=author["module_blob"] or author["official_base"]!="9feb2ec9f5ad8e96b6b727e9f77260b0a5f60991":
        raise AssertionError("CAPTURE_AUTHOR_SOURCE_OR_BASE_DRIFT")
    old=snapshot(srcdist)
    if len(old)!=PARENT_COUNT or MODULE in old or GAME not in old:
        raise AssertionError("CAPTURE_PREVIEW_NOT_OFFICIAL66_PARENT")
    if blob(old[GAME])!=OFFICIAL_GAME_BLOB:
        raise AssertionError("CAPTURE_GAME_SOURCE_DRIFT")
    expected={key:blob(value) for key,value in sorted(old.items())}
    lock=json.loads((srcdist/"SOURCE_LOCK.json").read_text("utf8"))
    features=json.loads((srcdist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    project=json.loads((srcdist/"default.project.json").read_text("utf8"))
    if lock.get("total_scripts")!=66 or lock.get("blobs")!=expected:
        raise AssertionError("CAPTURE_66_SOURCE_LOCK_DRIFT")
    if features.get("total_sources")!=66 or features.get("source_gitblobs")!=expected:
        raise AssertionError("CAPTURE_66_FEATURE_LOCK_DRIFT")
    if project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]!="src/server":
        raise AssertionError("CAPTURE_NOT_SAME_SERVER_MODULE_TREE")
    game=patch_game(old[GAME])
    if any(x in policy for x in (b"OnServerEvent:Connect(",b"DataStoreService",
                                   b"Instance.new(",b"TakeDamage(",b"MarketplaceService")):
        raise AssertionError("CAPTURE_MODULE_NOT_PURE_POLICY")
    assert "return Capture" in policy.decode("utf8")
    new=dict(old)
    new[GAME]=game
    new[MODULE]=policy
    assert len(new)==67 and all(new[p]==old[p] for p in old if p!=GAME)
    pins={key:blob(value) for key,value in sorted(new.items())}
    if "P0D_ENABLE_ADV_CAPTURE_V1" in project["tree"]["ServerStorage"]:
        raise AssertionError("CAPTURE_DUPLICATE_SWITCH")
    project["tree"]["ServerStorage"]["P0D_ENABLE_ADV_CAPTURE_V1"]={
        "$className":"BoolValue","$properties":{"Value":True}
    }
    lock["total_scripts"]=67
    lock["blobs"]=pins
    lock["rc_capture_preview"]={
        "id":"P0D-018","state":"PRIVATE_SCRATCH_NOT_RC",
        "parent_game_blob":OFFICIAL_GAME_BLOB,"current_game_blob":pins[GAME],
        "module_blob":author["module_blob"],"only_game_changed":True,
        "new_module":MODULE,"one_original_game_and_remote":True,
        "existing_guardian_net_preserved":True,
        "off_preserves_parent66":True,"studio_android_fun":"NOT_TESTED",
    }
    features["total_sources"]=67
    features["source_gitblobs"]=pins
    features["feature_flags"]["ADV_CAPTURE_RESCUE_PREVIEW_V1"]=True
    # All preflight and complete Game transformation before ANY scratch writes.
    shutil.copytree(srcdist,out)
    (out/"src"/GAME).write_bytes(game)
    (out/"src"/MODULE).write_bytes(policy)
    (out/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    (out/"RC_FEATURE_LOCK.json").write_text(json.dumps(features,ensure_ascii=False,indent=2)+"\n","utf8")
    (out/"default.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n","utf8")
    assert snapshot(out)==new
    print("P0D018_PRIVATE67_GAME_ONLY_AND_POLICY_SOURCE_EXACT_READY_FOR_ROJO")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--preview",required=True,type=Path)
    p.add_argument("--enabled",choices=["true","false"],required=True)
    a=p.parse_args()
    apply(a.dist,a.preview,a.enabled=="true")
