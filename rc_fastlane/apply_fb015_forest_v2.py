#!/usr/bin/env python3
"""FB015 forest biomes & stone landmarks, source-exact private RC80 overlay.

Only modifies existing Studio-only FantasyWorldArt decorative script after the
certified FB019 RC80 build; no gameplay, physics, HUD, client attack or server
authority code changes. B #220 remains the sole official RC writer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

TARGET="server/FantasyWorldArt.server.luau"
BASE_BLOB="dc741ec6d0506cfebf82631cf3583dd4037fbea9"
FEATURE="FB015_FOREST_BIOMES_MONUMENTS_V2"
TREE_ANCHOR="    end\nend\nlocal leftMargin=math.min(85,ground.Size.X*.33)"
RUIN_ANCHOR="-- Color grading is global but only in the author's Studio preview."
META_OLD='folder:SetAttribute("ArtPass","FB015_WORLD_PALETTE_FOLIAGE_ONLY")'

TREE_ADDITION='''    end
    -- Biome-dependent sculpted blossom highlights, kept within existing
    -- decorative-only tree crowns. LeafMass prefix retains FB016 camera fade.
    local petal = if side < 0 then Color3.fromRGB(166,201,185)
        else Color3.fromRGB(199,164,190)
    for j=1,2 do
        local pos=if j==1 then Vector3.new(-1.6,6.15,-.84)
            else Vector3.new(1.37,6.46,1.1)
        local petalPart=deco("LeafMass_BiomeBlossom_"..index.."_"..side.."_"..j,
            center+pos*scale,Vector3.new(2.1,1.2,1.9)*scale,
            petal,Enum.Material.Grass,Enum.PartType.Ball)
        if petalPart then petalPart.Transparency=.09 end
    end
end
local leftMargin=math.min(85,ground.Size.X*.33)'''

RUIN_ADDITION='''-- FB015_FOREST_BIOMES_MONUMENTS_V2: four readable, small, ruined forest gates.
-- The existing routes/eggs/castle/world are NOT modified. These are far
-- from z=-55 sea, z=0 main road and objective x≈±145. No collision/query.
-- 18 x 2 crowns + 4 x 6 gate parts => base166 + 60 = 226 under 255 cap.
for side=-1,1,2 do
    for column=1,2 do
        local x=if column==1 then -57 else 57
        local z=side*(sideZ+11)
        local center=Vector3.new(x,BASE_Y,z)
        local prefix="AncientForestGate_"..side.."_"..column
        local pillar=if side<0 then Color3.fromRGB(125,149,157)
            else Color3.fromRGB(147,133,147)
        local crystal=if side<0 then Color3.fromRGB(143,220,203)
            else Color3.fromRGB(230,180,218)
        for _,dir in ipairs({-1,1}) do
            deco(prefix.."_PILLAR_"..dir,
                center+Vector3.new(dir*4,4.25,0),
                Vector3.new(1.9,8.5,2.3),pillar,
                Enum.Material.Slate)
            local foot=deco(prefix.."_FOOT_"..dir,
                center+Vector3.new(dir*4,.42,0),
                Vector3.new(3.5,.84,3.6),stone[column],
                Enum.Material.Rock,Enum.PartType.Ball)
            if foot then foot.Orientation=Vector3.new(0,column*22,0) end
        end
        deco(prefix.."_BROKEN_LINTEL",
            center+Vector3.new(0,8.9,0),
            Vector3.new(10.6,1.55,2.6),pillar,Enum.Material.Slate)
        local gem=deco(prefix.."_CRYSTAL_KEYSTONE",
            center+Vector3.new(0,10.2,0),
            Vector3.new(2.35,3.0,1.75),crystal,Enum.Material.Glass,
            Enum.PartType.Ball)
        if gem then gem.Transparency=.13 end
    end
end

'''
def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),p
    src=root/"src"
    return {p.relative_to(src).as_posix():p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def once(raw:str,old:str,new:str)->str:
    assert raw.count(old)==1,("ART_WORLD_SOURCE_DRIFT",old[:60],raw.count(old))
    return raw.replace(old,new,1)

def patch(raw:bytes)->bytes:
    assert blob(raw)==BASE_BLOB,("WORLD_ART_AUTHOR_GIT_BLOB_DRIFT",blob(raw))
    source=raw.decode("utf8")
    assert FEATURE not in source, "PREEXISTING_FOREST_V2_FEATURE"
    source=once(source,'if root:FindFirstChild("P0D_FB015_WORLD_ART_V1") then return end',
        '''local oldForest = root:FindFirstChild("P0D_FB015_WORLD_ART_V1")
if oldForest and oldForest:GetAttribute("ArtPass")=="FB015_FOREST_BIOMES_MONUMENTS_V2" then return end''')
    source=once(source,'local folder = Instance.new("Folder")',
        '''if oldForest then oldForest:Destroy() end
local folder = Instance.new("Folder")''')
    assert 'if not RunService:IsStudio() then return end' in source
    assert 'p.CanCollide=false' in source and 'p.CanQuery=false' in source
    assert 'MAX_PARTS=255' in source
    assert 'for i=1,9 do' in source and 'for i=1,12 do' in source
    source=once(source,TREE_ANCHOR,TREE_ADDITION)
    source=once(source,RUIN_ANCHOR,RUIN_ADDITION+
        'assert(count==226,"FB015_FOREST_RUNTIME_PART_COUNT_DRIFT")\n'+RUIN_ANCHOR)
    source=once(source,META_OLD,'folder:SetAttribute("ArtPass","FB015_FOREST_BIOMES_MONUMENTS_V2")')
    source=once(source,'folder:SetAttribute("OfficialOwnerAccepted",false)',
        '''folder:SetAttribute("ForestBiomeBlossomParts",36)
folder:SetAttribute("ForestGateCount",4)
folder:SetAttribute("ForestArtPartBudgetExpectedMax",226)
folder:SetAttribute("OfficialOwnerAccepted",false)''')
    assert source.count("AncientForestGate_")==1
    assert source.count("LeafMass_BiomeBlossom_")==1
    assert source.count("p.CanQuery=false")==1
    assert source.count("MAX_PARTS=255")==1
    for banned in ('FireServer(', 'OnServerEvent:Connect(', 'TakeDamage(',
                   'GetDataStore(', 'MarketplaceService',
                   'Instance.new("ScreenGui")', 'Instance.new("BillboardGui")',
                   'CanCollide=true', 'CanQuery=true'):
        assert banned not in source,("FORBIDDEN_WORLD_ART",banned)
    return source.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"NO_DISABLED_OUT"
        print("FB015_FOREST_V2_DISABLED_ZERO_WRITE_PASS")
        return False
    base=base.resolve()
    out=out.parent.resolve(strict=True)/out.name
    assert out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base), "OUTPUT_INSIDE_INPUT"
    before=read(base)
    assert len(before)==80 and TARGET in before
    assert blob(before[TARGET])==BASE_BLOB
    origPins={p:blob(data) for p,data in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==origPins, "PARENT_SOURCE_LOCK_DRIFT"
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"] is True
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"] is True
    assert fl["feature_flags"]["FB018_ACTION_BUTTON_TEXT_INIT"] is True
    assert fl["feature_flags"]["FB019_RESPONSIVE_ATTACK_INPUT_SWING"] is True
    assert fl["feature_flags"].get("FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2") is True, "MISSING_CONFIRMED_HIT_V2"
    v2=fl.get("fb019_hit_visibility",{})
    assert v2.get("id")=="FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2", "V2_RECEIPT_UNTRUSTED"
    assert v2.get("source_blobs_after",{}).get("server/Game.server.luau")==origPins.get("server/Game.server.luau"), "V2_PARENT_GAME_DRIFT"
    assert FEATURE not in fl["feature_flags"]
    world=patch(before[TARGET])
    after=dict(before)
    after[TARGET]=world
    assert len(after)==80
    assert {p for p in before if before[p]!=after[p]}=={TARGET}
    newPins={p:blob(data) for p,data in sorted(after.items())}
    receipt={
        "feature":FEATURE,
        "owner_feedback":"FB-015",
        "base_official_sha":"bd5b819b846705e18537a994ed97ffe71ddd4855",
        "stage":"PRIVATE_A_PREP_ONLY",
        "source_count":80,
        "modified":[TARGET],
        "other79_byte_identical":True,
        "base_world_git_blob":BASE_BLOB,
        "new_world_git_blob":newPins[TARGET],
        "forest_biome_blossom_accents":36,
        "forest_monument_gates":4,
        "world_parts_estimated_max":226,
        "all_decorations_noncollide_nonquery":True,
        "server_game_hud_attack_egg_hp_store_unchanged":True,
        "studio_real_view":"NOT_TESTED",
        "android_fps":"NOT_TESTED",
        "owner_art":"ART_NO_GO",
        "official_rc_adopted":False,
        "rollback":"omit forest-v2 overlay to return author FantasyWorldArt original",
    }
    sl["blobs"]=newPins
    fl["source_gitblobs"]=newPins
    sl["fb015_forest_v2"]=receipt
    fl["fb015_forest_v2"]=receipt
    fl["feature_flags"][FEATURE]=True
    tmp=Path(tempfile.mkdtemp(prefix=".fb015forest_",dir=str(out.parent)))
    staged=tmp/"out"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/TARGET).write_bytes(world)
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    print("FB015_FOREST_V2_OFFICIAL_FB019_PARENT80_OTHER79_BYTE_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
