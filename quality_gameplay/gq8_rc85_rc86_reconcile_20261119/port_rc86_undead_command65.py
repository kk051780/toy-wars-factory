#!/usr/bin/env python3
"""Port only original RC86 UndeadSquad 3/48s/ATTACK-GUARD-FOLLOW semantics
into the ONE original V3 SevenRoleCombat. No new source/Game/Remote/Damage owner.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
FEATURE="GQ8_RC86_UNDEAD_SQUAD_COMMAND_RECONCILE_20261119"
ROUTE="ServerScriptService/EGGRUMBLE_SevenRoleCombat"
def demand(b,reason):
    if not b:raise ValueError("RED_RC86_UNDEAD_"+reason)
def once(s,a,b,key):
    demand(s.count(a)==1,"ANCHOR_"+key+"_"+str(s.count(a)))
    return s.replace(a,b,1)
def patch(s):
    demand(FEATURE not in s,"DUPLICATE")
    demand("GQ8_RC85_DOJO_RECONCILE_20261119" in s and "GQ8_RC86_STAGE_PVE_M1_REACH" in s,"PRESERVE_PRIOR")
    demand(s.count("local ZombieCommander=(function()")==1,"ONE_COMBAT_OWNER")
    s=once(s,'local LIMIT = 3\nlocal LIFETIME = 14\n',
       '-- '+FEATURE+': old RC86 three units, 48s and server-only ATTACK/GUARD/FOLLOW\nlocal LIMIT = 3\nlocal LIFETIME = 48\n',"TTL48")
    s=once(s,'local VALID = { FOLLOW = true, GUARD = true, FOCUS = true }',
       'local VALID = { FOLLOW = true, GUARD = true, FOCUS = true, ATTACK = true }',"VALID")
    s=once(s,'        order = "FOLLOW",\n','        order = "ATTACK",\n',"INITIAL_ATTACK")
    s=once(s,'    local bestDistance = ACQUIRE_RANGE\n    for _, candidate in ipairs(snapshot.targets or {}) do',
       '    local bestDistance = ACQUIRE_RANGE\n    -- FOLLOW is non-aggressive; all decisions remain with server policy.\n    if state.order == "FOLLOW" then return nil, bestDistance end\n    for _, candidate in ipairs(snapshot.targets or {}) do',"FOLLOW")
    s=once(s,'        if eligible(candidate, state.matchToken)\n            and (state.order ~= "GUARD"',
       '        if eligible(candidate, state.matchToken)\n            and (state.order ~= "ATTACK" or candidate.kind == "NEUTRAL")\n            and (state.order ~= "GUARD"',"ATTACK_TARGET_FENCE")
    s=once(s,'        if active[player] and active[player].stop == stop then active[player] = nil end',
       '        if active[player] and active[player].stop == stop then\n            active[player] = nil\n            if player.Parent then player:SetAttribute("EGGRUMBLE_UndeadCommand", nil) end\n        end',"STOP_CLEANUP")
    s=once(s,'    active[player] = { stop = stop, policy = policy }',
       '    active[player] = { stop = stop, policy = policy, character = character }\n    player:SetAttribute("EGGRUMBLE_UndeadCommand", "ATTACK")',"BEGIN")
    s=once(s,'    return Policy.issue(state.policy, order, focusId)\nend\n\nfunction Runtime.stop',
       '''    if not Policy.issue(state.policy, order, focusId) then return false end
    player:SetAttribute("EGGRUMBLE_UndeadCommand", order)
    return true
end

-- Skill C has already passed server slot/match validation in original Combat.
-- Reuse current real 3 units, never spawn another duplicate unit authority.
function Runtime.retask(player:Player, token:string):boolean
    local state = active[player]
    if not state or not state.policy.active or state.policy.count ~= Policy.MAX_UNITS
        or state.policy.matchToken ~= token or state.character ~= player.Character
        or os.clock() >= state.policy.startedAt + Policy.TTL_SECONDS then return false end
    local previous = state.policy.order
    local nextOrder = if previous == "ATTACK" then "GUARD"
        elseif previous == "GUARD" then "FOLLOW" else "ATTACK"
    return Runtime.order(player, nextOrder, nil)
end

function Runtime.stop''',"RETASK_METHOD")
    s=once(s,'   local matchToken=tostring(session)\n   -- Weak per-instance keys',
       '   local matchToken=tostring(session)\n   if ZombieCommander.retask(p,matchToken) then\n    blast()\n   else\n   -- Weak per-instance keys',"SKILL_C_BEGIN")
    s=once(s,'''   ZombieCommander.begin(p,{
    matchToken=matchToken,ownerId=tostring(p.UserId),world=session.world,
    snapshot=commanderSnapshot,hit=commanderHit
   })
  end
 end
end''','''   ZombieCommander.begin(p,{
    matchToken=matchToken,ownerId=tostring(p.UserId),world=session.world,
    snapshot=commanderSnapshot,hit=commanderHit
   })
   end -- only spawn when no live three-unit squad exists
  end
 end
end''',"SKILL_C_END")
    demand(s.count(FEATURE)==1 and s.count("ZombieCommander.begin(p,{")==1
           and s.count("function Runtime.retask(")==1,"ONE_AUTHORITY")
    demand("local SQUAD_COOLDOWN = 0.4" in s and "RespectCanCollide=true" in s,"V3_HIT_WALL_FENCE")
    return s
def main(project_path,receipt_path):
    root=project_path.parent
    project=json.loads(project_path.read_text())
    receipt=json.loads(receipt_path.read_text())
    rows={r["route"]:r for r in receipt["sources"]}
    demand(len(rows)==65 and ROUTE in rows,"EXACT_65")
    demand(receipt.get("rc85_dojo_lobby_training") and receipt.get("stage_weapon_reach_balance")
           and receipt.get("pickup_prompt_alias"),"PARENTS")
    demand("rc86_three_undead_command" not in receipt,"ALREADY_ADOPTED")
    demand(ROUTE in receipt["patched_existing_routes"],"EXISTING_OWNER")
    def get(row):
        node=project["tree"]
        for part in row["route"].split("/"):node=node[part]
        data=(root/node["$path"]).read_bytes()
        demand(len(data)==row["bytes"] and hashlib.sha256(data).hexdigest()==row["sha256"],
               "SOURCE_SHA_"+row["route"])
        return root/node["$path"],data
    for row in rows.values():get(row)
    path,before=get(rows[ROUTE])
    after=patch(before.decode("utf-8")).encode("utf-8")
    path.write_bytes(after)
    rows[ROUTE]["sha256"]=hashlib.sha256(after).hexdigest()
    rows[ROUTE]["bytes"]=len(after)
    for row in rows.values():get(row)
    receipt["rc86_three_undead_command"]={
      "feature_id":FEATURE,"original_rc86_artifact_id":14161823401,
      "modified_existing_routes":[ROUTE],"other_sources_unchanged":64,
      "new_game_remote_store_or_damage_owner":0,"new_script_count":0,
      "count":3,"duration_seconds":48,"legacy_commands":["ATTACK","GUARD","FOLLOW"],
      "v3_focus_preserved":True,"attack_neutral_only":True,
      "same_original_v3_hit_authority":True,"studio":"NOT_TESTED",
      "android":"NOT_TESTED","fun":"NOT_TESTED",
      "rollback":"Drop only this Combat overlay; retain Dojo, six weapons, exploration and OFF63"}
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ8_RC86_UNDEAD3_48S_ATTACK_GUARD_FOLLOW_EXISTING_COMBAT_SOURCE_PASS")
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--project",type=Path,required=True)
    a.add_argument("--receipt",type=Path,required=True)
    q=a.parse_args();main(q.project,q.receipt)
