#!/usr/bin/env python3
"""P0D #470 V3: fix physically reachable AI siege range; show 3 distinct hits.

Based on immutable previous V2 real 84-script place. Changes ONLY original
MapBuilder; all 83 other script bodies including Game/AI/egg/7jobs/warp stay exact.
Private Studio experiment, never writes official RC/main/merge/publication.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
import build_siege_bot_breach_private84 as original

PARENT="P0D_RC84_SIEGE_EGG_CARRIER_ESCAPE_CLOCK_SAFE_PRIVATE.rbxlx"
PARENT_SHA="89b47d4d919a04b4ea72304681749f2b8f01da768698bf5a1838b8bb5c331e7e"
PARENT_MAP_BLOB="65a42c009aa5200526845489a3799255bb8fc028"
PARENT_BOT_BLOB="e978f32072b7505014bea3ffa9e95e68503db9b8"
PARENT_GAME_BLOB="9b7fb4648b9b6c6b5efbc958ecdf275e46f6830d"
OFFICIAL="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
OUTPUT="P0D_RC84_SIEGE_STRIKE_VFX_AI_ARRIVAL_PRIVATE.rbxlx"
EXPECTED_PLACE_SHA="0f256dfd46cad4ff1f94d09730eb6bc1d285ed6fc29f4801cae6e59ea8f4e63a"
EXPECTED_MAP_BLOB="f8f6b4df84ff726518b31c3f3710aa369326fe47"
EXPECTED_PLACE_BYTES=822592

def once(s,a,b,name):
    if s.count(a)!=1 or b in s:
        raise ValueError("REAL_SIEGE_SOURCE_ANCHOR_DRIFT_"+name)
    return s.replace(a,b,1)

VISUALS='''    -- P0D_FB_SIEGE_HITS_V3: three true physical hit markers welded to gate.
    -- Each server-authoritative AI strike illuminates one section. No HUD
    -- overlay, marketplace assets, client Remote, or external SoundId.
    local hitBars={}
    for i=1,3 do
        local bar=Instance.new("Part")
        bar.Name=name.."_SIEGE_HIT_BAR_"..tostring(i)
        bar.Size=Vector3.new(.3,1.9,1.2)
        bar.Material=Enum.Material.Neon
        bar.Color=Color3.fromRGB(255,179,66)
        bar.Transparency=.84
        bar.Anchored=false
        bar.CanCollide=false;bar.CanTouch=false;bar.CanQuery=false
        bar.Massless=true;bar.CastShadow=false
        bar.CFrame=gate.CFrame*CFrame.new(-sign*1.22,0,(i-2)*3.35)
        bar.Parent=port
        local weld=Instance.new("WeldConstraint")
        weld.Part0=gate;weld.Part1=bar;weld.Parent=bar
        hitBars[i]=bar
    end
    local debris=game:GetService("Debris")
    local function setSiegeBars(damage,open)
        for i,bar in ipairs(hitBars) do
            if bar.Parent then
                bar.Transparency=if open then 1 elseif damage>=i then .06 else .84
            end
        end
    end
    local function siegeImpactVFX(damage,broken)
        -- One small 3D impact burst per true hit, capped 3 transient parts.
        -- The flash is anchored, non-collidable and never enters a damage query.
        local glow=if broken then Color3.fromRGB(255,238,137)
            else Color3.fromRGB(255,133,68)
        for k=1,3 do
            local p=Instance.new("Part")
            p.Name=name.."_SIEGE_IMPACT_"..tostring(damage)
            p.Size=Vector3.new(.24,.24,.48)
            p.Material=Enum.Material.Neon
            p.Color=glow
            p.Transparency=.12
            p.Anchored=true
            p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
            p.CastShadow=false
            local start=Vector3.new(x-sign*1.7,
                6+(k-2)*1.2, (damage-2)*3.35)
            p.CFrame=CFrame.new(start)
            p.Parent=port
            tween:Create(p,TweenInfo.new(.25,Enum.EasingStyle.Quad,
                Enum.EasingDirection.Out),{
                Position=start+Vector3.new(-sign*(1.4+k*.25),
                    k*.42, (k-2)*.9),Transparency=1}):Play()
            debris:AddItem(p,.30)
        end
    end
'''

def patch_map(src):
    # No change to console area/accessibility, existing 9s door lock, original
    # EGG score authority, or original player/npc validated gate requests.
    anchor='''    local tween=game:GetService("TweenService")
    local raised=CFrame.new(x,22,0)'''
    changed='''    local tween=game:GetService("TweenService")
'''+VISUALS+'''    local raised=CFrame.new(x,22,0)'''
    src=once(src,anchor,changed,"ADD_MOBILE_CAPPED_SERVER_VFX")
    src=once(src,
      '''        siegeDamage=0
        gate:SetAttribute("SiegeDamage",siegeDamage)
        gate:SetAttribute("GateRaised",opening)''',
      '''        siegeDamage=0
        gate:SetAttribute("SiegeDamage",siegeDamage)
        gate:SetAttribute("GateRaised",opening)
        setSiegeBars(0,opening)''',"RESET_PHYSICAL_HIT_BARS")
    src=once(src,
      '''        if math.abs(botOrigin.X-approachX)>4 then return false end''',
      '''        -- Bot.move() correctly stops within 4.5 studs of its goal.
        -- A <4 acceptance window could leave an arrived bot permanently
        -- unable to strike. The 5.2-stud window is still firmly on
        -- the authenticated outside/inside approach (7 studs off the gate).
        if math.abs(botOrigin.X-approachX)>5.2 then return false end''',
      "SERVER_BREACH_AI_MOVE_TO_TOLERANCE")
    src=once(src,
      '''        lastSiegeAt=now
        siegeDamage+=1
        gate:SetAttribute("SiegeDamage",siegeDamage)
        if siegeDamage>=3 then''',
      '''        lastSiegeAt=now
        siegeDamage+=1
        gate:SetAttribute("SiegeDamage",siegeDamage)
        setSiegeBars(siegeDamage,false)
        siegeImpactVFX(siegeDamage,siegeDamage>=3)
        if siegeDamage>=3 then''',"THREE_ACTUAL_HIT_VISUAL_IMPACTS")
    required=("workspace:GetServerTimeNow()",'"SiegeDamage"',
              "SiegeRequiredHits","setSiegeBars(siegeDamage,false)",
              "siegeImpactVFX(siegeDamage,siegeDamage>=3)",
              "math.abs(botOrigin.X-approachX)>5.2",
              "breachLock=now+10","task.delay(9",
              "local function npcBreach(attackerTeam,botOrigin,now,fromInside)",
              "fromInside then sign*7 else -sign*7",
              "workspace:GetAttributeChangedSignal",
              "GetPartBoundsInBox")
    for r in required:
        if r not in src:raise ValueError("SIEGE_CORE_FEATURE_LOST_"+r)
    if "local now=os.clock()" in src:raise ValueError("MIXED_GATE_CLOCK_RED")
    return src

def build(parent,out,extract=None):
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(
            n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_ZIP")
        raw=z.read(PARENT)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if original.sha(raw)!=PARENT_SHA or receipt.get("official_rc_head")!=OFFICIAL or receipt.get("official_rc_write") is not False:
        raise ValueError("WRONG_EXACT_RC84_PARENT")
    if lock["blobs"].get(original.MAP_PATH)!=PARENT_MAP_BLOB or lock["blobs"].get(original.BOT_PATH)!=PARENT_BOT_BLOB or lock["blobs"].get(original.GAME_PATH)!=PARENT_GAME_BLOB:
        raise ValueError("PARENT_GAME_MAP_AI_SOURCE_CHANGED")
    scripts=original.verify84(raw,lock,feature)
    before={n:v.text for n,v in scripts.items()}
    root,nodes=original.source_nodes(raw)
    nodes["MapBuilder"].text=patch_map(before["MapBuilder"])
    final=ET.tostring(root,encoding="utf-8")
    after=original.source_nodes(final)[1]
    if len(after)!=84 or any(after[n].text!=t for n,t in before.items() if n!="MapBuilder"):
        raise ValueError("UNRELATED_83_SOURCE_BODIES_MUTATED")
    newblob=original.blob(after["MapBuilder"].text)
    if EXPECTED_PLACE_SHA and (original.sha(final)!=EXPECTED_PLACE_SHA or
        len(final)!=EXPECTED_PLACE_BYTES or newblob!=EXPECTED_MAP_BLOB):
        raise ValueError("LOCKED_SIEGE_V3_SOURCE_SHA_DRIFT")
    lock["blobs"][original.MAP_PATH]=feature["source_gitblobs"][original.MAP_PATH]=newblob
    original.verify84(final,lock,feature)
    result={"schema":"P0D_SIEGE_V3_REAL_AI_ARRIVAL_AND_PHYSICAL_HIT_FX",
      "official_rc_head":OFFICIAL,"official_rc_write":False,
      "parent_place_sha256":PARENT_SHA,
      "place_sha256":original.sha(final),"place_bytes":len(final),
      "map_builder_blob":newblob,
      "script_count":84,"other_83_script_bodies_byte_exact":True,
      "solo_AI_original_source_exact":True,
      "game_egg_score_winner_exact":True,"seven_weapons_and_trapper_exact":True,
      "server_ai_4_5_to_5_2_window_fixed":True,
      "physical_three_hit_siege_indicators":True,
      "impact_sparks_per_hit":3,"particle_or_external_asset_dependency":False,
      "server_synced_gate_clock":True,"private_default_off":True,
      "source_dual_lock_exact":True,"native":"NOT_RUN","rojo":"NOT_RUN",
      "studio":"NOT_RUN","android":"NOT_RUN","owner":False,"product":"NO_GO"}
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT,final)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    if extract:
        extract.mkdir(parents=True,exist_ok=True)
        for n,node in after.items():
            (extract/(n+".luau")).write_text(node.text,encoding="utf-8")
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--extract",type=Path)
    args=ap.parse_args()
    print(json.dumps(build(args.parent,args.out,args.extract),ensure_ascii=False,indent=2))
