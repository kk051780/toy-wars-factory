#!/usr/bin/env python3
"""FB-019 P0: direct local swing feedback for valid ATTACK input, server attack unchanged.
Exact RC80+FB018 input; replaces only HUD.client.luau. No new remote/game authority.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
HUD="client/HUD.client.luau"
PIN="0bc1af1af5ff4c30cb51106b3fad5c662a403393"
FEATURE="FB019_RESPONSIVE_ATTACK_INPUT_SWING"
ANCHOR="end\n-- Single existing HUD sequence counter; no second Remote or client score logic.\n"
BUTTON='attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)'
KEY='if input.KeyCode == Enum.KeyCode.F then action("ATTACK", nil)'
SNAP='    attack.Visible = s.phase == "ACTIVE"'
# Fully local transient effect: no damage, no fake hit/KO and no persistent GUI.
GESTURE="""-- FB-019 OWNER P0: visible SWING even when no enemy is within server hit reach.
-- Does not claim damage. The original Game alone handles ATTACK, sequence, HP, horde.
local attackLocalLastAt = -math.huge
local attackDebris = game:GetService("Debris")
local function showLocalSwing()
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    local hum = character and character:FindFirstChildOfClass("Humanoid")
    if not root or not root:IsA("BasePart") or not hum or hum.Health<=0 then return end
    local basis = root.CFrame
    for i=1,2 do
        local flash = Instance.new("Part")
        flash.Name = "FB019_ATTACK_SWING_LOCAL_"..i
        flash.Anchored=true
        flash.CanCollide=false
        flash.CanTouch=false
        flash.CanQuery=false
        flash.CastShadow=false
        flash.Material=Enum.Material.Neon
        flash.Color=if i==1 then Color3.fromRGB(255,227,157) else Color3.fromRGB(150,220,255)
        flash.Size=Vector3.new(3.1,.15,.10)
        flash.Transparency=.12
        local side=if i==1 then -1 else 1
        flash.CFrame=basis*CFrame.new(side*.27,.75,-2.8)
            *CFrame.Angles(0,0,math.rad(side*32))
        flash.Parent=workspace
        local goal=basis*CFrame.new(side*.36,1.0,-4.2)
            *CFrame.Angles(0,0,math.rad(side*69))
        TweenService:Create(flash,TweenInfo.new(.18,Enum.EasingStyle.Quad,
            Enum.EasingDirection.Out),{
            CFrame=goal,
            Transparency=1,
            Size=Vector3.new(4.0,.06,.08),
        }):Play()
        attackDebris:AddItem(flash,.24)
    end
end
local function pressAttack()
    -- One accepted server phase, same source of truth used by other HUD controls.
    local snapshot=relayLatest
    if type(snapshot)~="table" or snapshot.phase~="ACTIVE" then return end
    local character=player.Character
    local hum=character and character:FindFirstChildOfClass("Humanoid")
    if not hum or hum.Health<=0 then return end
    local now=os.clock()
    if now-attackLocalLastAt<.85 then return end
    attackLocalLastAt=now
    action("ATTACK",nil) -- SAME existing Remote and monotonic seq; no second authority.
    showLocalSwing() -- input acknowledgement, NOT a confirmed hit.
end
"""
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def read(dist:Path)->dict[str,bytes]:
    assert dist.is_dir() and not dist.is_symlink()
    for path in dist.rglob("*"):
        assert not path.is_symlink() and path.resolve().is_relative_to(dist.resolve()),path
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes() for p in sorted(root.rglob("*.luau"))}
def replace_once(s:str,old:str,new:str)->str:
    assert s.count(old)==1,(old[:45],s.count(old))
    return s.replace(old,new,1)
def patch(raw:bytes)->bytes:
    assert blob(raw)==PIN,("HUD_PIN_DRIFT",blob(raw))
    s=raw.decode("utf8")
    s=replace_once(s,ANCHOR,"end\n"+GESTURE+"-- Single existing HUD sequence counter; no second Remote or client score logic.\n")
    s=replace_once(s,BUTTON,"attack.Activated:Connect(pressAttack)")
    s=replace_once(s,KEY,"if input.KeyCode == Enum.KeyCode.F then pressAttack()")
    s=replace_once(s,SNAP,SNAP+"\n    attack.Active = s.phase == \"ACTIVE\"")
    assert s.count('action("ATTACK",nil)')==1
    assert s.count("attack.Activated:Connect(pressAttack)")==1
    assert "attack.MouseButton1Click:Connect(" not in s
    assert s.count("if input.KeyCode == Enum.KeyCode.F then pressAttack()")==1
    assert "showLocalSwing()" in s and "attackDebris:AddItem(flash,.24)" in s
    return s.encode("utf8")
def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists()
        print("FB019_OFF_ZERO_WRITE_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert out.parent.is_dir() and not out.exists() and not out.is_relative_to(base)
    originals=read(base)
    assert len(originals)==80 and HUD in originals
    before={p:blob(v) for p,v in sorted(originals.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==before
    assert fl["feature_flags"]["FB018_ACTION_BUTTON_TEXT_INIT"] is True
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"] is True
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"] is True
    assert FEATURE not in fl["feature_flags"]
    patched=patch(originals[HUD])
    assert not any(x in patched for x in (b"TakeDamage(",b"UpdateAsync(",b"Instance.new(\"RemoteEvent\")"))
    after={**originals,HUD:patched}
    assert len(after)==80 and {p for p in originals if originals[p]!=after[p]}=={HUD}
    pins={p:blob(v) for p,v in sorted(after.items())}
    receipt={
        "id":FEATURE,"user_feedback":"FB-019","source_count":80,
        "modified":HUD,"other79_byte_exact":True,
        "server_Game_Remote_HP_egg_horde_unchanged":True,
        "touch_and_PC":"GuiButton.Activated plus existing F-key both use pressAttack",
        "cooldown_sec":0.85,"visual_only_local_miss_swing_sec":0.24,
        "real_hit":"Original Game and Horde only",
        "new_remote":False,"new_gui":False,
        "studio_engine":"NOT_TESTED","owner_fun":"FUN_NO_GO",
        "rollback":"omit FB019 overlay to obtain exact a47abf05 RC80",
    }
    sl["blobs"]=pins;sl["fb019_attack_feedback"]=receipt
    fl["source_gitblobs"]=pins;fl["feature_flags"][FEATURE]=True
    fl["fb019_attack_feedback"]=receipt
    scratch=Path(tempfile.mkdtemp(prefix=".fb019_",dir=str(out.parent)))
    staging=scratch/"dist"
    try:
        shutil.copytree(base,staging,symlinks=False)
        (staging/"src"/HUD).write_bytes(patched)
        (staging/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staging/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staging)==after and read(base)==originals
        os.replace(staging,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("FB019_REAL_RC80_ATTACK_GESTURE_HUD_PATCH_79_UNCHANGED_PASS")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
