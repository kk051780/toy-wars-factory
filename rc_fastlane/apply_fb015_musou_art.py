#!/usr/bin/env python3
"""FB-015/008: reversible single-Horde source ART-MINION overhaul.

Patches the REAL MusouHorde Game-owned mob model, rather than spawning a second
NPC simulation.  All hits, HP, KO, respawn and target authority remain original.
Only one of the assembled 66 Luau source bytes changes. OFF = zero writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ID = "FB015_ART_MINION_SILHOUETTE_V1"
HORDE = "server/MusouHorde.luau"
ORIGINAL_HORDE_BLOB = "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def sub(src: str, old: str, new: str) -> str:
    assert src.count(old) == 1, ("H1_SOURCE_ANCHOR_DRIFT", old[:110], src.count(old))
    return src.replace(old, new, 1)

ART_MAKE = '''
    -- FB-015: actual independent silhouettes, not a recolored stock block mob.
    -- Three small enemy designs + one boss, all animated by existing single Horde tick.
    local artStyle=if elite then "SIEGE_CHAMPION"
        elseif id%3==1 then "SHIELD_WARDEN"
        elseif id%3==2 then "TWINBLADE_SCOUT"
        else "HORNED_LANCER"
    model:SetAttribute("P0D_ArtStyle",artStyle)
    model:SetAttribute("P0D_VisualOnly",true)
    local charcoal=Color3.fromRGB(42,52,67)
    local slate=Color3.fromRGB(85,110,132)
    local brass=Color3.fromRGB(217,180,111)
    local bone=Color3.fromRGB(220,213,186)
    local deepGreen=Color3.fromRGB(58,107,86)
    local crimson=Color3.fromRGB(157,62,75)
    local function wear(tag: string,dimensions: Vector3,at: Vector3,
        tint: Color3,material: Enum.Material,wedge: boolean?,yaw: number?,
        roll: number?): BasePart
        local part=if wedge then Instance.new("WedgePart") else Instance.new("Part")
        part.Name="ART_"..tag
        part.Size=dimensions
        part.Anchored=true
        part.CanCollide=false
        part.CanTouch=false
        part.CanQuery=false -- NEVER extend authoritative melee/raycast geometry
        part.CastShadow=true
        part.Material=material
        part.Color=tint
        part.CFrame=CFrame.new(at)*CFrame.Angles(0,math.rad(yaw or 0),
            math.rad(roll or 0))
        part.Parent=model
        return part
    end
    local half=if elite then 2.5 else 1.65
    local headY=if elite then 4.7 else 3.75
    local shoulderX=if elite then 2.28 else 1.52
    local bootX=if elite then 1.12 else .71
    local armorColor=if elite then charcoal
        elseif artStyle=="SHIELD_WARDEN" then slate
        elseif artStyle=="TWINBLADE_SCOUT" then deepGreen else crimson
    local chest=wear("LAYERED_CUIRASS",if elite then Vector3.new(4.1,3.6,.38)
        else Vector3.new(2.7,2.65,.28),Vector3.new(0,0,-(if elite then 1.72 else 1.13)),
        armorColor,Enum.Material.Metal,false)
    wear("CHEST_RIDGE",Vector3.new(if elite then 2.3 else 1.55,.22,.36),
        Vector3.new(0,.85,-(if elite then 1.96 else 1.33)),
        brass,Enum.Material.Metal,false)
    wear("GORGET",Vector3.new(if elite then 3 else 2.1,.65,1.95),
        Vector3.new(0,1.8,0),charcoal,Enum.Material.Metal,false)
    for _,sg in ipairs({-1,1}) do
        wear("SHOULDER_PLATE_"..sg,Vector3.new(if elite then 1.65 else 1.1,.7,1.7),
            Vector3.new(sg*shoulderX,1.2,0),slate,Enum.Material.Metal,true,0,sg*19)
        wear("GAUNTLET_"..sg,Vector3.new(.67,1.15,.82),
            Vector3.new(sg*(if elite then 2.75 else 1.78),-.55,-.22),
            charcoal,Enum.Material.Metal,true,0,sg*14)
    end
    wear("HELM_CROWN",Vector3.new(if elite then 3.0 else 2.2,.52,
            if elite then 2.5 else 1.9),Vector3.new(0,headY,0),
        armorColor,Enum.Material.Metal,false)
    wear("HELM_BROW",Vector3.new(if elite then 2.45 else 1.65,.38,.45),
        Vector3.new(0,headY-.47,-(if elite then 1.55 else 1.1)),
        brass,Enum.Material.Metal,false)
    wear("WAIST_BELT",Vector3.new(if elite then 4.15 else 2.85,.32,
        if elite then 3.2 else 2.14),Vector3.new(0,-.78,0),
        charcoal,Enum.Material.Metal,false)
    wear("BELT_SEAL",Vector3.new(.63,.54,.28),
        Vector3.new(0,-.75,-(if elite then 1.8 else 1.21)),
        brass,Enum.Material.Metal,false)
    local artLegs: {BasePart} = {}
    for _,sg in ipairs({-1,1}) do
        local foot=wear("ARMOR_BOOT_"..sg,Vector3.new(
            if elite then 1.2 else .8,if elite then 1.1 else .79,
            if elite then 1.8 else 1.15),
            Vector3.new(sg*bootX,-half+.45,-.4),
            armorColor,Enum.Material.Metal,true)
        table.insert(artLegs,foot)
    end
    if artStyle=="SHIELD_WARDEN" then
        -- Big shield silhouette; the visual shield confers NO extra block or HP.
        local shield=wear("TOWER_SHIELD",Vector3.new(.55,2.75,2.38),
            Vector3.new(-2.16,.18,-.75),slate,Enum.Material.Metal)
        shield.Shape=Enum.PartType.Ball
        wear("SHIELD_BOSS",Vector3.new(.32,.9,.85),
            Vector3.new(-2.51,.18,-.78),brass,Enum.Material.Metal)
        wear("LONG_BANNER",Vector3.new(.27,2.0,1.55),
            Vector3.new(0,-.18,1.18),deepGreen,Enum.Material.Fabric,true)
    elseif artStyle=="TWINBLADE_SCOUT" then
        for _,sg in ipairs({-1,1}) do
            wear("CURVED_DUAL_BLADE_"..sg,Vector3.new(.24,2.6,.9),
                Vector3.new(sg*2.14,-.75,-1.3),bone,Enum.Material.Metal,true,sg*22,sg*18)
            wear("BLADE_HILT_"..sg,Vector3.new(.33,.8,.5),
                Vector3.new(sg*2.0,-.95,-.74),brass,Enum.Material.Wood,false)
        end
        wear("SCOUT_HOOD",Vector3.new(1.65,1.3,2.2),
            Vector3.new(0,headY+.48,.48),deepGreen,Enum.Material.Fabric,true)
        wear("SCOUT_CAPE",Vector3.new(.26,2.5,2.45),
            Vector3.new(0,-.08,1.13),slate,Enum.Material.Fabric,true)
    elseif artStyle=="HORNED_LANCER" then
        for _,sg in ipairs({-1,1}) do
            wear("ANTLER_"..sg,Vector3.new(.42,1.7,.7),
                Vector3.new(sg*1.02,headY+.85,.17),
                bone,Enum.Material.Slate,true,0,sg*32)
        end
        wear("LANCE_POLE",Vector3.new(.24,5.6,.24),
            Vector3.new(2.3,.36,-.1),charcoal,Enum.Material.Wood)
        wear("LANCE_TIP",Vector3.new(.85,1.72,.7),
            Vector3.new(2.3,3.62,-.1),bone,Enum.Material.Metal,true,0,180)
        wear("LANCER_CLOAK",Vector3.new(.27,2.2,2.15),
            Vector3.new(0,-.15,1.12),crimson,Enum.Material.Fabric,true)
    else
        -- Boss: giant tiered pauldrons, four horn points, broad pole axe and cape.
        for _,sg in ipairs({-1,1}) do
            wear("BOSS_HORN_"..sg,Vector3.new(.85,2.8,.85),
                Vector3.new(sg*1.25,5.95,0),bone,Enum.Material.Slate,true,0,sg*22)
            wear("BOSS_BACK_SPIKE_"..sg,Vector3.new(1,2.3,1.5),
                Vector3.new(sg*1.55,1.7,1.45),brass,Enum.Material.Metal,true,0,sg*27)
        end
        wear("BOSS_AXE_HANDLE",Vector3.new(.43,7,.43),
            Vector3.new(3.45,.8,-.35),charcoal,Enum.Material.Wood)
        wear("BOSS_AXE_EDGE",Vector3.new(1.4,3.5,2.7),
            Vector3.new(3.48,4.2,-.35),bone,Enum.Material.Metal,true,0,110)
        wear("BOSS_DOUBLE_CAPE",Vector3.new(.29,4.5,4.5),
            Vector3.new(0,-.23,1.84),crimson,Enum.Material.Fabric,true)
        wear("BOSS_MEDALLION",Vector3.new(1.1,1.18,.36),
            Vector3.new(0,.1,-1.96),brass,Enum.Material.Metal)
    end
    local function burst(tint: Color3): ParticleEmitter
        local fx=Instance.new("ParticleEmitter")
        fx.Name="ART_HIT_CONFIRM_ONLY"
        fx.Enabled=true
        fx.Rate=0 -- zero idle particles
        fx.Texture="rbxasset://textures/particles/sparkles_main.dds"
        fx.LightEmission=.68
        fx.Color=ColorSequence.new(tint)
        fx.Lifetime=NumberRange.new(.15,.32)
        fx.Speed=NumberRange.new(4,10)
        fx.SpreadAngle=Vector2.new(160,160)
        fx.Drag=8
        fx.Size=NumberSequence.new(.28)
        fx.Parent=body
        return fx
    end
    local hitBurst=burst(Color3.fromRGB(253,228,150))
    local koBurst=burst(Color3.fromRGB(243,119,87))
    -- Original body/HP/target and one Game tick remain sole combat authority.
'''
def patch_horde(text: str) -> str:
    assert "FB015_ART_MINION_SILHOUETTE_V1" not in text, "DOUBLE_ART_PATCH"
    assert blob(text.encode("utf8")) == ORIGINAL_HORDE_BLOB, "AUTHORED_HORDE_BLOB_DRIFT"
    assert text.count('local function makeBody(')==1
    text = sub(text,
        '    model.Parent=folder\n    model:PivotTo(CFrame.new(p))\n    return model,body,text,zone,arms,eyes,popup,popupText',
        ART_MAKE + '''    model.Parent=folder
    model:PivotTo(CFrame.new(p))
    return model,body,text,zone,arms,eyes,popup,popupText,artLegs,hitBurst,koBurst''')
    text = sub(text,
        'local model,body,cue,zone,arms,eyes,popup,popupText=makeBody(self.folder,i,elite,base)',
        'local model,body,cue,zone,arms,eyes,popup,popupText,artLegs,hitBurst,koBurst=makeBody(self.folder,i,elite,base)')
    text = sub(text,
        'popup=popup,popupText=popupText,popupUntil=0,hidden=false,id=i,',
        'popup=popup,popupText=popupText,artLegs=artLegs,hitBurst=hitBurst,koBurst=koBurst,\n            popupUntil=0,hidden=false,id=i,')
    text = sub(text,
        '    gui.AlwaysOnTop=true\n    gui.Size=UDim2.fromOffset(110,43)',
        '    gui.AlwaysOnTop=false\n    gui.MaxDistance=26\n    gui.Size=UDim2.fromOffset(82,26)')
    text = sub(text,
        '    popup.AlwaysOnTop=true\n    popup.Enabled=false',
        '    popup.AlwaysOnTop=true\n    popup.MaxDistance=40\n    popup.Enabled=false')
    text = sub(text, '                    m.popup.Enabled=true\n                    m.popupUntil=now+.72',
        '                    m.popup.Enabled=true\n                    m.hitBurst:Emit(if m.elite then 8 else 5)\n                    m.popupUntil=now+.72')
    text = sub(text, '''                    if m.hp<=0 then
                        defeated+=1''',
        '''                    if m.hp<=0 then
                        m.koBurst:Emit(if m.elite then 23 else 14)
                        defeated+=1''')
    text = sub(text, '''            local sway=math.sin(now*4+m.id)
            m.arms[1].Orientation''',
        '''            local sway=math.sin(now*4+m.id)
            local moving=(m.pos-(m.artPreviousPosition or m.pos)).Magnitude>.06
            m.artPreviousPosition=m.pos
            for index,boot in ipairs(m.artLegs) do
                local side=if index==1 then -1 else 1
                local bx=side*(if m.elite then 1.12 else .71)
                local lift=if moving then math.max(0,math.sin(now*7+m.id+index*math.pi))*.26 else 0
                boot.CFrame=m.body.CFrame*CFrame.new(bx,-(if m.elite then 2.5 else 1.65)+.45+lift,-.4)
            end
            m.arms[1].Orientation''')
    text = sub(text, 'local Horde = {}', 'local Horde = {}\n-- FB015_ART_MINION_SILHOUETTE_V1 / FB-008 + FB-015')
    assert text.count("Horde:hit(")==1
    assert text.count("Horde:tick(")==1
    assert text.count('function Horde:reset(')==1
    assert 'm.hitBurst:Emit(' in text and 'm.koBurst:Emit(' in text
    assert 'OnServerEvent:Connect(' not in text
    return text

def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("P0D_FB015_ART_MINION_OFF_ZERO_WRITES")
        return False
    before=sources(dist)
    assert len(before)==66, ("REQUIRE_CANONICAL66",len(before))
    assert HORDE in before
    existing={path:blob(raw) for path,raw in sorted(before.items())}
    lp=dist/"SOURCE_LOCK.json"
    fp=dist/"RC_FEATURE_LOCK.json"
    lock=json.loads(lp.read_text("utf8"))
    feature=json.loads(fp.read_text("utf8"))
    assert lock["total_scripts"]==66 and lock["blobs"]==existing,"SOURCE_LOCK_DRIFT"
    assert feature["total_sources"]==66 and feature["source_gitblobs"]==existing,"FEATURE_LOCK_DRIFT"
    assert ID not in feature["feature_flags"],"DOUBLE_ART_APPLY"
    game=before["server/Game.server.luau"]
    assert game.count(b'remote.OnServerEvent:Connect(')==1, "GAME_NOT_SINGLE_AUTHORITY"
    changed=patch_horde(before[HORDE].decode("utf8")).encode("utf8")
    after=dict(before)
    after[HORDE]=changed
    assert {k for k in before if before[k]!=after[k]}=={HORDE}
    newPins={path:blob(raw) for path,raw in sorted(after.items())}
    lock["blobs"]=newPins
    lock["fb015_minion_visual"]={
        "feature_id":ID,"feedback":["FB-008","FB-015"],
        "changed_source_only":HORDE,
        "unchanged_other_sources":65,
        "game_and_remote_same_source":True,
        "all_npc_hp_damage_ko_original":True,
        "owner_visual_fun":"ART_NO_GO_NOT_TESTED",
        "studio_mobile_performance":"NOT_TESTED",
        "rollback":"omit ART_MINION post-assembly patch; exact 66 originals"
    }
    feature["source_gitblobs"]=newPins
    feature["feature_flags"][ID]=True
    (dist/"src"/HORDE).write_bytes(changed)
    lp.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    fp.write_text(json.dumps(feature,ensure_ascii=False,indent=2)+"\n","utf8")
    assert sources(dist)==after
    print("FB015_ART_MINION_66_ONE_HORDE_MODIFIED_65_UNTOUCHED")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    args=p.parse_args()
    apply(args.dist,args.enabled=="true")
