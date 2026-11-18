#!/usr/bin/env python3
"""Real original 44 -> 46 (#830) -> 47 verified seven-role reactive COUNTERS.

Uses original 44 exact previous first-hit composer without altering prior
source rights; adds ONLY one Counter module and a tightly scoped PvP return
in the SAME original SevenRoleCombat HP owner. No second Swarm or Score.
"""
import argparse,copy,hashlib,json,os
from pathlib import Path
from compose_real46 import compose as compose46, flatten,HOST,SITES,exact_blob

ROOT=Path(__file__).resolve().parent
COUNTER=ROOT/"EGGRUMBLE_InvulCounterNeutral.luau"
NEW=("ServerScriptService","EGGRUMBLE_InvulCounterNeutral")
HERO=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
PVP_ORIGINAL='enemyHum:TakeDamage(InvulRuntime.filterDamage(enemyHum,damage*duel*mark,"PLAYER",p.UserId))'
PVP_REPLACEMENT='''local originalAttackDamage=InvulRuntime.filterDamage(enemyHum,damage*duel*mark,"PLAYER",p.UserId)
    enemyHum:TakeDamage(originalAttackDamage)
    if originalAttackDamage==0 then
     -- This return strike executes IN the existing original SevenRoleCombat HP
     -- writer (not in new InvulRuntime or Swarm). One Policy claim per awakening.
     local counter=InvulRuntime.claimPvPCounter(session,enemyPlayer,p)
     if counter then
      local defenderAvatar=enemyPlayer.Character
      local attackerAvatar=p.Character
      local warningEnd=os.clock()+counter.tellSeconds
      task.delay(counter.tellSeconds,function()
       if session.rules.phase~="ACTIVE" or not owner or not state
        or not state.alive or not owner.alive then return end
       if enemyPlayer.Character~=defenderAvatar or p.Character~=attackerAvatar
        or not p.Parent or not enemyPlayer.Parent then return end
       local atRoot=attackerAvatar and attackerAvatar:FindFirstChild("HumanoidRootPart")
       local defRoot=defenderAvatar and defenderAvatar:FindFirstChild("HumanoidRootPart")
       local atHum=attackerAvatar and attackerAvatar:FindFirstChildOfClass("Humanoid")
       local defHum=defenderAvatar and defenderAvatar:FindFirstChildOfClass("Humanoid")
       if not atRoot or not defRoot or not atHum or not defHum
        or atHum.Health<=0 or defHum.Health<=0
        or os.clock()<warningEnd or (atRoot.Position-defRoot.Position).Magnitude>16 then return end
       local aCastle=session.rules.castles[tostring(p.UserId)]
       local dCastle=session.rules.castles[tostring(enemyPlayer.UserId)]
       if not aCastle or not dCastle or not aCastle.alive or not dCastle.alive
        or (session.mode=="TEAM" and aCastle.team==dCastle.team) then return end
       -- A real enemy can escape by leaving counter range or line-of-sight
       -- during the warning. No fake client-supplied dodge response.
       if not lineClear(defRoot.Position+Vector3.new(0,1.5,0),
        atRoot.Position+Vector3.new(0,1,0),defenderAvatar,attackerAvatar) then return end
       local maxPortion=counter.maxPvpMaxHealthFraction
       if type(maxPortion)~="number" or maxPortion<=0 or maxPortion>.4 then return end
       local amount=math.min(atHum.Health,atHum.MaxHealth*maxPortion)
       if counter.effect=="TELEGRAPHED_FINISHER" then
        local fraction=if counter.role=="WARRIOR" then .25 else .20
        if atHum.Health/atHum.MaxHealth>fraction then
         -- Healed out of execute threshold during telegraph: only bounded
         -- nonlethal strike, never a hidden full-health execution.
         amount=math.min(amount,math.max(0,atHum.Health-1))
        end
       else
        amount=math.min(amount,math.max(0,atHum.Health-1))
       end
       if amount>0 then
        local realDamage=InvulRuntime.filterDamage(atHum,amount,"PLAYER",enemyPlayer.UserId)
        if realDamage>0 then
         atHum:TakeDamage(realDamage) -- SAME original Combat HP authority
         ImpactFeedback.hit(attackerAvatar,counter.role)
        end
       end
      end)
     end
    end'''
def make(real44,policy,out):
 out=Path(out).resolve()
 if out.exists() or out.parent.exists():raise ValueError("RED_REFUSE_EXISTING_PARENT")
 out.parent.mkdir(parents=True)
 real46=out.parent/"source46"/"ON46.project.json"
 compose46(Path(real44),Path(policy),real46)
 original46,old=flatten(real46)
 if len(old)!=46 or NEW in old or HERO not in old:
  raise ValueError("RED_NOT_UNMODIFIED_ORIGINAL46")
 hero=old[HERO].read_text(encoding="utf-8")
 if hero.count(PVP_ORIGINAL)!=1 or "claimPvPCounter(" in hero:
  raise ValueError("RED_UNEXPECTED_ORIGINAL_HERO_HIT")
 if "InvulRuntime.filterDamage" not in hero or hero.count("InvulRuntime.filterDamage")<2:
  raise ValueError("RED_ORIGINAL13_PREHIT_GATES_MISSING")
 # Do not create a second game damage loop, only the same original hero
 # already authorized PvP hit branch can execute delayed single return.
 amended=hero.replace(PVP_ORIGINAL,PVP_REPLACEMENT,1)
 if amended.count("atHum:TakeDamage(realDamage)")!=1:
  raise ValueError("RED_NOT_SINGLE_COMBAT_PVP_RETURN")
 counter_src=COUNTER.read_bytes()
 if not counter_src.startswith(b"--!strict") or b"session.swarm.damageFromPlayer" not in counter_src:
  raise ValueError("RED_COUNTER_MUST_DELEGATE_SWARM")
 pvp_target=out.parent/"source47"/"ServerScriptService"/"EGGRUMBLE_SevenRoleCombat.luau"
 pvp_target.parent.mkdir(parents=True,exist_ok=True)
 pvp_target.write_text(amended,encoding="utf-8")
 counter_target=out.parent/"source47"/"ServerScriptService"/"EGGRUMBLE_InvulCounterNeutral.luau"
 counter_target.write_bytes(counter_src)
 model=copy.deepcopy(original46)
 node=model["tree"]["ServerScriptService"]
 node[HERO[-1]]["$path"]=os.path.relpath(pvp_target,out.parent).replace(os.sep,"/")
 node[NEW[-1]]={"$path":os.path.relpath(counter_target,out.parent).replace(os.sep,"/")}
 model["name"]="EGGRUMBLE_REAL47_SEVEN_ROLE_AWAKEN_COUNTER_SINGLE_COMBAT_AND_SWARM"
 out.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,new=flatten(out)
 if len(new)!=47 or set(new)!=set(old)|{NEW}:raise ValueError("RED_WRONG47_ROUTES")
 for route,f in old.items():
  if route!=HERO and new[route].read_bytes()!=f.read_bytes():
   raise ValueError("RED_MODIFIED_OTHER_SOURCES_"+"/".join(route))
 if new[HERO].read_text().replace(PVP_REPLACEMENT,PVP_ORIGINAL,1)!=hero:
  raise ValueError("RED_CANNOT_REMOVE_SINGLE_COMBAT_PVP_INSERT")
 if new[NEW].read_bytes()!=COUNTER.read_bytes():
  raise ValueError("RED_COUNTER_OWNER_DRIFT")
 receipt={
  "feature_id":"GQ822_SEVEN_ROLE_AWAKENED_COUNTER_REAL47",
  "official_rc_written":False,"publish":False,
  "original44":44,"previous46":46,"counter47":47,
  "modified_existing_relative_to_original46":["/".join(HERO)],
  "original_other46_byte_exact":45,"added_counter_script":"/".join(NEW),
  "new_parallel_damage_owners":0,
  "new_single_original_combat_return_damage_sites":1,
  "all_existing_13_pre_damage_sites_intact":True,
  "neutral_hits_delegated_to_existing_swarm":True,
  "warrior_ninja_single_pvp_attacker_only":True,
  "mate_barrier_is_half_damage_not_full_invul":True,
  "real_engine_Studio":False,"android":False,
  "source_parent_830":"f7d4a736fefe1b680ba8f0f1b39a53606531cd47",
  "original_v2_policy_blob":exact_blob(new[("ServerScriptService","EGGRUMBLE_InvulnerabilityPolicy")].read_bytes()),
  "off46":"Re-select unmodified Real46 generated by #830 composer",
  "off44":"Re-select original immutable 44 parent",
 }
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("GQ822_ORIGINAL_REAL46_PLUS_SINGLE_COMBAT_COUNTER_REAL47_SOURCE_EXACT")
 return out
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--original44",required=True,type=Path)
 a.add_argument("--policy",required=True,type=Path)
 a.add_argument("--out",required=True,type=Path)
 args=a.parse_args()
 make(args.original44,args.policy,args.out)
