#!/usr/bin/env python3
"""Real current official31 -> ON32 HP-regen gameplay adapter; OFF31 is byte exact.

Does not mutate checked-out author code or the canonical branch.
Single-authority Host embeds the only HP write. Original other 30 scripts unchanged.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from quality_gameplay.gq8_lss_real31_20261117.rehydrate_real31 import flat_project

HERE=Path(__file__).resolve().parent
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
MOD=("ServerScriptService","EGGRUMBLE_PassiveRegenPolicy")
MOD_SOURCE=HERE/"PassiveRegenPolicy.luau"

REQUIRE_ANCHOR='local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
BIND_ANCHOR='if humanoid and humanoid:IsA("Humanoid") then'
REQUIRE_INSERT='local PassiveRegen=require(script.Parent:WaitForChild("EGGRUMBLE_PassiveRegenPolicy"))'
HOOK=r'''
      -- GQ8 BATTLE_HP_REGEN: one Host owns all HP changes; no new Remote/Game.
      if sessions[mode]==session and joined[player.UserId]==mode
          and player.Character==character and session.rules.phase=="ACTIVE" then
       session.regenBound=session.regenBound or {}
       if not session.regenBound[character] then
        session.regenBound[character]=true
        local owner=session.rules.castles[tostring(player.UserId)]
        local role=chosenRole[player.UserId] or "WARRIOR"
        local cap=PassiveRegen.maxHPForRole(role)
        if owner and owner.alive and cap then
         humanoid.MaxHealth=cap
         humanoid.Health=cap
         local token=mode..":"..tostring(session)
         local policyState=PassiveRegen.new(token,os.clock(),humanoid.Health,humanoid.MaxHealth)
         local observedHP=humanoid.Health
         local hpWatcher=humanoid.HealthChanged:Connect(function(hp)
          if hp < observedHP-0.000001 then
           policyState.lastDamageAt=os.clock()
          end
          observedHP=hp
         end)
         table.insert(session.lifeConnections,hpWatcher)
         local heartbeat:RBXScriptConnection?=nil
         heartbeat=RunService.Heartbeat:Connect(function()
          if sessions[mode]~=session or joined[player.UserId]~=mode
              or player.Character~=character or humanoid.Parent==nil then
           if heartbeat then heartbeat:Disconnect() end
           hpWatcher:Disconnect()
           return
          end
          local owned=session.rules.castles[tostring(player.UserId)]
          local amount=PassiveRegen.step(policyState,{
           sessionId=token,now=os.clock(),health=humanoid.Health,maxHP=humanoid.MaxHealth,
           inMatch=(session.rules.phase=="ACTIVE" and owned~=nil and owned.alive==true),
           downed=(humanoid.Health<=0 or character:GetAttribute("EGGRUMBLE_Downed")==true),
           hasDot=(character:GetAttribute("EGGRUMBLE_DoT")==true),
          })
          if amount>0 then humanoid.Health=math.min(humanoid.MaxHealth,humanoid.Health+amount) end
         end)
         table.insert(session.lifeConnections,heartbeat)
        end
       end
      end
'''
def _flat(model, project):
    values=flat_project(model)
    paths={}
    for route,item in values.items():
        if not isinstance(item.get("$path"),str):
            raise ValueError("RED_MISSING_SOURCE_PATH")
        paths[route]=(project.parent/item["$path"]).resolve(strict=True)
    return paths

def compose(current31:Path,out:Path,off=False):
    current31=current31.resolve(strict=True);out=out.resolve()
    if out.exists() or current31==out:
        raise ValueError("RED_OVERWRITE_OR_SAME_FILE")
    model=json.loads(current31.read_text(encoding="utf-8"))
    originals=_flat(model,current31)
    if len(originals)!=31 or HOST not in originals or SWARM not in originals or MOD in originals:
        raise ValueError("RED_NOT_CURRENT_SINGLE_HOST31")
    if len({r[-1] for r in originals})!=31:
        raise ValueError("RED_DUPLICATE_SCRIPT_NAME")
    candidate=copy.deepcopy(model)
    candidate["name"]="GQ8_BATTLE_REGEN_OFF31" if off else "GQ8_BATTLE_REGEN_LIVE32"
    out.parent.mkdir(parents=True,exist_ok=True)
    for route,item in flat_project(candidate).items():
        item["$path"]=os.path.relpath(originals[route],out.parent).replace(os.sep,"/")
    if not off:
        host=originals[HOST].read_text(encoding="utf-8")
        if ("BATTLE_HP_REGEN" in host or host.count(REQUIRE_ANCHOR)!=1
            or host.count(BIND_ANCHOR)!=1 or "local RunService=game:GetService" not in host):
            raise ValueError("RED_HOST_ADAPTER_ANCHOR_OR_DOUBLE_AUTHORITY")
        host=host.replace(REQUIRE_ANCHOR,REQUIRE_ANCHOR+"\n"+REQUIRE_INSERT,1)
        host=host.replace(BIND_ANCHOR,BIND_ANCHOR+"\n"+HOOK,1)
        new_host=out.parent/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
        if new_host.exists():
            raise ValueError("RED_REPLACE_GENERATED_HOST")
        new_host.write_text(host,encoding="utf-8",newline="\n")
        candidate["tree"]["ServerScriptService"][HOST[-1]]["$path"]=new_host.name
        candidate["tree"]["ServerScriptService"][MOD[-1]]={
            "$path":os.path.relpath(MOD_SOURCE,out.parent).replace(os.sep,"/")
        }
    out.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    selected=_flat(candidate,out)
    expected=31 if off else 32
    if len(selected)!=expected:
        raise ValueError("RED_WRONG_SCRIPT_COUNT")
    for route,src in originals.items():
        if route==HOST and not off:
            if selected[route].read_bytes()==src.read_bytes():
                raise ValueError("RED_REGEN_NOT_WIRED")
        elif selected[route].read_bytes()!=src.read_bytes():
            raise ValueError("RED_CHANGED_ORIGINAL_SOURCE_"+"/".join(route))
    if not off and selected[MOD].read_bytes()!=MOD_SOURCE.read_bytes():
        raise ValueError("RED_POLICY_BLOB_NOT_EXACT")
    receipt={"feature":"BATTLE_HP_REGEN_20261118","off":off,"count":expected,
             "host_only_changed":not off,"new_module_exact":not off,
             "old30_byte_exact":True,"inverse_original31":off,
             "old_host_sha256":hashlib.sha256(originals[HOST].read_bytes()).hexdigest(),
             "official_rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED"}
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("GQ8_REGEN_OFF31_EXACT" if off else "GQ8_REGEN_HOST_HP_OWNER_ON32",expected)
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--current31",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--off",action="store_true")
    a=p.parse_args()
    compose(a.current31,a.out,a.off)
