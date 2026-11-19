#!/usr/bin/env python3
"""RC86 FB030 parity repair: StageLoot has damage AND reach, for PvE M1 only.

Old Game applied the buff inside applyAttack to Horde M1. Current #865
original V3 neutralAndBotHit instead applied it to every Player skill/PvP.
Use the one existing FieldItemPickups/SevenRoleCombat authority; never
duplicate Game, Store, damage, Hero, Swarm, Remote or pickup world entities.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ITEM="ServerScriptService/EGGRUMBLE_FieldItemPickups"
COMBAT="ServerScriptService/EGGRUMBLE_SevenRoleCombat"
FEATURE="GQ8_RC86_FB030_PVE_M1_REACH_AND_BALANCE_RECONCILIATION_20261119"
SPEC={
'SUN_BLADE={label="炎の大剣",damage=1.35,color=':'SUN_BLADE={label="炎の大剣",damage=1.35,reach=0,color=',
'WIND_SPEAR={label="疾風の槍",damage=1.08,color=':'WIND_SPEAR={label="疾風の槍",damage=1.08,reach=3.5,color=',
'THUNDER_BOW={label="雷光の弩",damage=1.22,color=':'THUNDER_BOW={label="雷光の弩",damage=1.22,reach=1.7,color=',
}
ITEM_LEASE_OLD='''     kind=kind,damage=def.damage}'''
ITEM_LEASE_NEW='''     kind=kind,damage=def.damage,reach=def.reach}'''
ITEM_API_OLD=''' return lease.damage
end'''
ITEM_API_NEW=''' return lease.damage
end
-- The same original server-owned lease guards reach; no client attribute grants power.
function Items.weaponReachBonus(player:Player,session:any):number
 local lease=weaponBuffs[player]
 if not lease or lease.session~=session or lease.character~=player.Character
  or not lease.character or not lease.character.Parent
  or not session or not session.world or not session.world.Parent
  or not session.rules or session.rules.phase~="ACTIVE"
  or not canUse(player,session) or carryingEnemyEggs(player,session) then return 0 end
 local hum=lease.character:FindFirstChildOfClass("Humanoid")
 if not hum or hum.Health<=0 or os.clock()>=lease.expires then return 0 end
 return lease.reach or 0
end'''
COMBAT_SIG_OLD='''local function neutralAndBotHit(session:any,p:Player,root:BasePart,char:Model,at:Vector3,range:number,damage:number,c:Color3,shape:string):number'''
COMBAT_SIG_NEW='''local function neutralAndBotHit(session:any,p:Player,root:BasePart,char:Model,at:Vector3,range:number,damage:number,c:Color3,shape:string,stageBasic:boolean?):number'''
COMBAT_BUFF_OLD=''' -- RC86 temporary field weapons use this SAME existing Combat damage authority.
 -- No client-supplied multipliers, no extra HP/KO writer, no summoned minion buffs.
 if root.Parent==p.Character then
  damage*=FieldItemPickups.weaponDamageMultiplier(p,session)
 end'''
COMBAT_BUFF_NEW=''' -- GQ8_RC86_STAGE_PVE_M1_REACH: true old RC86 FB030 semantic parity.
 -- Only the verified basic attack receives a temporary NEUTRAL bonus.
 -- Do not amplify skills, PvP players, castle/bot/guardian HP or zombie summons.
 local neutralDamage=damage
 local neutralAt=at
 if stageBasic==true and root.Parent==p.Character then
  neutralDamage=damage*FieldItemPickups.weaponDamageMultiplier(p,session)
  local stageReach=FieldItemPickups.weaponReachBonus(p,session)
  if stageReach>0 and stageReach<=3.5 then
   local look=root.CFrame.LookVector
   local flat=Vector3.new(look.X,0,look.Z)
   if flat.Magnitude>.01 then
    local step=flat.Unit*stageReach
    local ray=RaycastParams.new()
    ray.FilterType=Enum.RaycastFilterType.Exclude
    ray.FilterDescendantsInstances={char}
    ray.RespectCanCollide=true
    -- RC86 FB030 original wall/gate fix: reject projected hit through solids.
    if workspace:Raycast(root.Position+Vector3.new(0,1.2,0),step,ray)==nil then
     neutralAt=at+step
    end
   end
  end
 end'''
SWARM_OLD=''' if session.swarm then count+=session.swarm.damageFromPlayer(p,at,range,damage,shape) end'''
SWARM_NEW=''' if session.swarm then count+=session.swarm.damageFromPlayer(p,neutralAt,range,neutralDamage,shape) end'''
M1_OLD='''local hits=neutralAndBotHit(session,p,root,char,center,
  spec.radius,spec.damage,JOBS[role].color,spec.shape)'''
M1_NEW='''local hits=neutralAndBotHit(session,p,root,char,center,
  spec.radius,spec.damage,JOBS[role].color,spec.shape,true)'''

def one(src:str,old:str,new:str,label:str)->str:
    if src.count(old)!=1 or new in src:
        raise ValueError("RED_STAGE_REACH_"+label+"_SOURCE_DRIFT")
    return src.replace(old,new,1)

def item_patch(src:str)->str:
    if "GQ8_RC86_STAGE_WEAPONS_TO_REAL65_20261119" not in src:
        raise ValueError("RED_STAGE_REACH_OLD_STAGE_MISSING")
    original=src
    for a,b in SPEC.items():
        src=one(src,a,b,"SPEC")
    src=one(src,ITEM_LEASE_OLD,ITEM_LEASE_NEW,"LEASE")
    src=one(src,ITEM_API_OLD,ITEM_API_NEW,"API")
    assert "function Items.weaponReachBonus(player:Player,session:any):number" in src
    for a,b in list(SPEC.items())+[(ITEM_LEASE_OLD,ITEM_LEASE_NEW),(ITEM_API_OLD,ITEM_API_NEW)]:
        src=src  # all differences verified by one-source-only hash gate in apply()
    if src==original:raise ValueError("RED_STAGE_REACH_NOT_APPLIED")
    return src

def combat_patch(src:str)->str:
    if "RC86_FB029_WIND_SINGLE_COMBAT_PORT" not in src:
        raise ValueError("RED_STAGE_REACH_LOST_WIND")
    original=src
    for a,b,name in [
        (COMBAT_SIG_OLD,COMBAT_SIG_NEW,"SIGNATURE"),
        (COMBAT_BUFF_OLD,COMBAT_BUFF_NEW,"BUFF"),
        (SWARM_OLD,SWARM_NEW,"SWARM"),
        (M1_OLD,M1_NEW,"M1_ONLY")]:
        src=one(src,a,b,name)
    if src.replace(M1_NEW,M1_OLD,1).replace(SWARM_NEW,SWARM_OLD,1).replace(
       COMBAT_BUFF_NEW,COMBAT_BUFF_OLD,1).replace(COMBAT_SIG_NEW,COMBAT_SIG_OLD,1)!=original:
        raise ValueError("RED_STAGE_REACH_UNRELATED_COMBAT_MUTATION")
    for token in (":TakeDamage(","RemoteEvent","ProcessReceipt","DataStoreService"):
        if src.count(token)!=original.count(token):
            raise ValueError("RED_STAGE_REACH_SECOND_AUTHORITY")
    return src

def self_test():
    fixture_item="\n".join(("GQ8_RC86_STAGE_WEAPONS_TO_REAL65_20261119",*SPEC.keys(),
                            ITEM_LEASE_OLD,ITEM_API_OLD))
    one_result=item_patch(fixture_item)
    assert "reach=3.5" in one_result and "reach=1.7" in one_result
    assert "weaponReachBonus" in one_result
    fixture_combat="\n".join(("RC86_FB029_WIND_SINGLE_COMBAT_PORT",COMBAT_SIG_OLD,
                              COMBAT_BUFF_OLD,SWARM_OLD,M1_OLD))
    out=combat_patch(fixture_combat)
    assert "stageBasic==true" in out and "neutralAt=at+step" in out
    assert "workspace:Raycast(" in out and "neutralDamage" in out
    for fn,text in ((item_patch,one_result),(combat_patch,out),
                    (combat_patch,fixture_combat.replace(SWARM_OLD,SWARM_OLD+"\n"+SWARM_OLD))):
        try:fn(text)
        except ValueError:pass
        else:raise AssertionError("RED_STAGE_REACH_MUTATION_ACCEPTED")
    print("GQ8_RC86_FB030_BASIC_ONLY_WALL_SAFE_REACH_NEGATIVE_TESTS_PASS")

def apply(project_path:Path,receipt_path:Path)->None:
    proj=json.loads(project_path.read_text(encoding="utf8"))
    rec=json.loads(receipt_path.read_text(encoding="utf8"))
    rows={r["route"]:r for r in rec["sources"]}
    if proj.get("name")!="EGGRUMBLE_REAL65_PRIVATE_STUDIO" or len(rows)!=65 or len(rec["sources"])!=65:
        raise ValueError("RED_STAGE_REACH_CURRENT_65_ROUTING")
    if not rec.get("pickup_prompt_alias") or not rec.get("rc85_rc86_stage_weapon_delta") or not rec.get("legacy_rc86_wind"):
        raise ValueError("RED_STAGE_REACH_PRIOR_CUMULATIVE_GATES")
    if "stage_weapon_reach_balance" in rec:
        raise ValueError("RED_STAGE_REACH_DOUBLE_PORT")
    names={}
    for route,row in rows.items():
        node=proj["tree"]
        for seg in route.split("/"):node=node[seg]
        path=project_path.parent/node["$path"]
        if not path.is_file():
            raise ValueError("RED_STAGE_REACH_MISSING_PATH_"+route)
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=row["sha256"] or len(data)!=row["bytes"]:
            raise ValueError("RED_STAGE_REACH_PARENT_HASH_"+route)
        names[route]=(path,data)
    for route,fn in ((ITEM,item_patch),(COMBAT,combat_patch)):
        p,data=names[route]
        updated=fn(data.decode("utf8")).encode("utf8")
        p.write_bytes(updated)
        rows[route]["sha256"]=hashlib.sha256(updated).hexdigest()
        rows[route]["bytes"]=len(updated)
    if sum(d!=p.read_bytes() for p,d in names.values())!=2:
        raise ValueError("RED_STAGE_REACH_NONLOSS_SCRIPT_COUNT")
    # Both routes were already owned/modified by original #865. No added author.
    if ITEM not in rec["patched_existing_routes"] or COMBAT not in rec["patched_existing_routes"]:
        raise ValueError("RED_STAGE_REACH_EXISTING_OWNERS_MISSING")
    rec["stage_weapon_reach_balance"]={
        "feature_id":FEATURE,"script_count":65,"unchanged_source_count":63,
        "changed_existing":[ITEM,COMBAT],"added_new_scripts":0,
        "original_rc86_source_gitblob":"450ba944550c3bc44ce04dc9b91da943090598d9",
        "pve_basic_only":True,"skill_mult":False,"pvp_mult":False,"castle_mult":False,
        "original_damage":[1.35,1.08,1.22],"original_reach":[0,3.5,1.7],
        "wall_ray_respect_can_collide":True,"original_item_owner":True,
        "studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NO_GO",
        "rollback":"Remove two narrow overlays; retain all earlier REAL65 wind, 15 pickup aliases, exact OFF63"}
    receipt_path.write_text(json.dumps(rec,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    for route,row in rows.items():
        p=names[route][0];d=p.read_bytes()
        if len(d)!=row["bytes"] or hashlib.sha256(d).hexdigest()!=row["sha256"]:
            raise ValueError("RED_STAGE_REACH_FINAL_65_SOURCE_LOCK_"+route)
    print("GQ8_RC86_STAGE_REACH_PVE_M1_ONLY_65_SOURCE_NONLOSS_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--project",type=Path)
    parser.add_argument("--receipt",type=Path)
    arg=parser.parse_args()
    if arg.self_test:self_test()
    else:
        if not arg.project or not arg.receipt:parser.error("--project and --receipt required")
        apply(arg.project,arg.receipt)
