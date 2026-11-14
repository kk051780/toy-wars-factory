#!/usr/bin/env python3
"""FB015 portable beast art: distance/phone LOD on REAL official RC80 Gorogan.

Safe and source-locked. Only existing client visual source changes: no extra
Lua/Remote/HUD/server authority, HP, egg, reward, collisions, or DataStore.
B #220 remains the only official RC writer.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path

TARGET="client/FB015CharacterArt.client.luau"
BASE_BLOB="2ff10db1a4171be9abdc276a43dd21b2401da2d8"
FEATURE="FB015_GOROGAN_MOBILE_LOD_V1"
BASE_RC="bd5b819b846705e18537a994ed97ffe71ddd4855"

def blob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()), p
    src=root/"src"
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}
def one(s:str,old:str,new:str)->str:
    assert s.count(old)==1,("EXACT_ART_ANCHOR_DRIFT",old[:65],s.count(old))
    return s.replace(old,new,1)

LOD_CONTROLLER='''-- FB015_GOROGAN_MOBILE_LOD_V1. One inexpensive distance check every .70s.
-- Client-only LocalTransparencyModifier: no server physics/network touches.
-- Strong near-field silhouette preserved, trim surface details at mid/far.
local lodAccumulator = 0
RunService.Heartbeat:Connect(function(dt: number)
    lodAccumulator += dt
    if lodAccumulator < .70 then return end
    lodAccumulator = 0
    local camera = Workspace.CurrentCamera
    if not camera then return end
    local near = if LOW_END_TOUCH then 52 else 82
    local far = if LOW_END_TOUCH then 118 else 182
    for model, item in pairs(lodSet) do
        local torso = model:FindFirstChild("Torso")
        if torso and torso:IsA("BasePart") and model.Parent then
            local distance = (torso.Position - camera.CFrame.Position).Magnitude
            local tier = if distance > far then 2
                elseif distance > near then 1 else 0
            if item.tier ~= tier then
                item.tier = tier
                for _, decoration in ipairs(item.parts) do
                    if decoration.Parent then
                        local name = decoration.Name
                        local silhouette = name == "ObsidianChestPlate"
                            or name:find("Pauldron") ~= nil
                            or name:find("CrownHorn") ~= nil
                            or name:find("BackSpike") ~= nil
                        local visible = tier == 0 or (tier == 1 and silhouette)
                        decoration.LocalTransparencyModifier = if visible then 0 else 1
                        decoration.CastShadow = not LOW_END_TOUCH and tier == 0
                    end
                end
                item.glow.Enabled = tier == 0
            end
        end
    end
end)

'''
def patch(raw:bytes)->bytes:
    assert blob(raw)==BASE_BLOB,("ORIGINAL_GOROGAN_GITBLOB_DRIFT",blob(raw))
    s=raw.decode("utf8")
    assert "if not RunService:IsStudio() then return end" in s
    assert FEATURE not in s
    s=one(s,'local TweenService = game:GetService("TweenService")\n',
          'local TweenService = game:GetService("TweenService")\n'
          'local UserInputService = game:GetService("UserInputService")\n')
    s=one(s,'local partCount = 0\n', '''local partCount = 0
-- Only a mobile heuristic; device/FPS still require independent real testing.
local LOW_END_TOUCH = UserInputService.TouchEnabled
    and not UserInputService.KeyboardEnabled
local decorByFolder: {[Instance]: {BasePart}} = {}
local lodSet: {[Model]: {parts: {BasePart}, glow: PointLight, tier: number}} = {}
''')
    s=one(s,'    if partCount >= MAX_DECOR_PARTS then return nil end\n',
          '''    -- Six microscopic cosmetic parts are omitted entirely on phones.
    -- Keep large shoulders/horns/spine for the threatening silhouette.
    if LOW_END_TOUCH and (name == "ShoulderSigil"
        or name == "HeartCarving" or name == "ForeheadMask"
        or name == "JawMask" or name:find("FlankArmor_") ~= nil) then
        return nil
    end
    if partCount >= MAX_DECOR_PARTS then return nil end
''')
    s=one(s,'    partCount += 1\n    p.Name = name\n',
          '''    partCount += 1
    local ownedParts = decorByFolder[folder]
    if ownedParts then table.insert(ownedParts, p) end
    p.Name = name
''')
    s=one(s,'    p.CastShadow = true\n',
          '    p.CastShadow = not LOW_END_TOUCH\n')
    s=one(s,'    art:SetAttribute("VisualOnly", true)\n',
          '''    art:SetAttribute("VisualOnly", true)
    decorByFolder[art] = {}
    art:SetAttribute("BeastLodPolicy", "FB015_GOROGAN_MOBILE_LOD_V1")
    art:SetAttribute("MobileDetailRadiusStuds", 52)
    art:SetAttribute("MobileSilhouetteRadiusStuds", 118)
''')
    s=one(s,'    glow.Brightness = .7\n', 
          '    glow.Brightness = if LOW_END_TOUCH then .45 else .7\n')
    s=one(s,'    pulse:Play()\n',
          '''    if not LOW_END_TOUCH then pulse:Play() end
''')
    s=one(s,'            burst:Emit(if value <= 0 then 22 else 8)\n',
          '''            -- No never-ending particles: short burst, smaller phone budget.
            burst:Emit(if LOW_END_TOUCH then (if value <= 0 then 6 else 3)
                else (if value <= 0 then 22 else 8))
''')
    s=one(s,'    local ownParts = partCount - partCountBefore\n',
          '''    local ownParts = partCount - partCountBefore
    local visualParts = decorByFolder[art]
    if visualParts then
        lodSet[model] = {parts = visualParts, glow = glow, tier = -1}
    end
''')
    s=one(s,'        seen[model] = nil\n',
          '''        seen[model] = nil
        lodSet[model] = nil
        decorByFolder[art] = nil
''')
    s=one(s,'for _,item in ipairs(Workspace:GetDescendants()) do\n',
          LOD_CONTROLLER+'for _,item in ipairs(Workspace:GetDescendants()) do\n')
    assert s.count("RunService.Heartbeat:Connect")==1
    assert s.count("LocalTransparencyModifier")==2
    assert s.count("partCount += 1")==1
    assert s.count("MAX_DECOR_PARTS = 64")==1
    assert s.count("MAX_BEASTS = 2")==1
    for forbidden in ("TakeDamage(", "FireServer(", "OnServerEvent:Connect(",
                       "CanCollide = true", "CanQuery = true",
                       'Instance.new("ScreenGui")',"GetDataStore("):
        assert forbidden not in s,("UNSAFE_ART_CHANGE",forbidden)
    return s.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_MUST_NOT_WRITE"
        print("GOROGAN_MOBILE_LOD_OFF_ZERO_WRITE");return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==80 and TARGET in before
    original={p:blob(b) for p,b in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==original
    assert original[TARGET]==BASE_BLOB
    for key in ("FB016_FOLIAGE_PASSAGE_20261114",
                "FB017_NO_PERSISTENT_BATTLE_GUIDES",
                "FB018_ACTION_BUTTON_TEXT_INIT",
                "FB019_RESPONSIVE_ATTACK_INPUT_SWING"):
        assert fl["feature_flags"].get(key) is True,("MISSING_PARENT_FLAG",key)
    assert FEATURE not in fl["feature_flags"]
    result=patch(before[TARGET])
    after={**before,TARGET:result}
    assert len(after)==80 and {p for p in before if before[p]!=after[p]}=={TARGET}
    updated={p:blob(b) for p,b in sorted(after.items())}
    receipt={
        "feature":FEATURE,"owner_feedback":"FB-015","baseline_official":BASE_RC,
        "stage":"PRIVATE_A_PREP_NOT_OFFICIAL","source_count":80,
        "changed_source":[TARGET],"other79_byte_exact":True,
        "old_git_blob":BASE_BLOB,"new_git_blob":updated[TARGET],
        "local_distance_sample_seconds":0.70,"mobile_detail_studs":52,
        "mobile_silhouette_studs":118,"mobile_particles_death":6,
        "pc_original_beauty_near_avatar":True,
        "game_authority_unchanged":True,"new_runtime_scripts":0,
        "android_fps":"NOT_TESTED","studio_art":"NOT_TESTED",
        "owner_accepted":False,"art_decision":"ART_NO_GO",
        "rollback":"remove isolated overlay and rebuild RC80 original client art",
    }
    sl["blobs"]=updated;fl["source_gitblobs"]=updated
    sl["fb015_beast_mobile_lod"]=receipt
    fl["fb015_beast_mobile_lod"]=receipt
    fl["feature_flags"][FEATURE]=True
    tmp=Path(tempfile.mkdtemp(prefix=".fb015_gorogan_lod_",dir=str(out.parent)))
    staged=tmp/"candidate"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/TARGET).write_bytes(result)
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    print("GOROGAN_MOBILE_LOD_80_SOURCE_ONE_ART_ONLY_79_BYTE_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
