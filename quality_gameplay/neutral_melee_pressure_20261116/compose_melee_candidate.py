#!/usr/bin/env python3
"""Source-selective V3 Swarm neutral melee overlay; never edit an author source."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "handoffs" / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
HERE = Path(__file__).resolve().parent
SOURCE_BLOB = "fea147ac51411e626b410d172aad5cd72615bd45"

def git_blob(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()

def once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"RED_SOURCE_DRIFT {label}: expected one anchor, got {text.count(old)}")
    return text.replace(old, new, 1)

def patch(original: str) -> str:
    source = original
    a = 'local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))\n'
    source = once(source, a, a + 'local Melee=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralMeleePolicy"))\n', "require")
    a = ' local lastBotHit:{[string]:number}={}\n'
    source = once(source, a, a + ' local lastMeleeSwing:{[Model]:number}=setmetatable({}, {__mode="k"}) :: any\n local lastVictimHit:{[Humanoid]:number}=setmetatable({}, {__mode="k"}) :: any\n', "state")
    a = ' -- Area skills have a visible area, not the ability to hit through solid castle walls.\n'
    add = """ local function liveMeleeVictims():{any}
  local victims={}
  for _,p in ipairs(Players:GetPlayers()) do
   local castle=session.rules.castles[tostring(p.UserId)]
   local ch=p.Character
   local root=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
   local hum=ch and ch:FindFirstChildOfClass("Humanoid")
   if p.Parent and p:GetAttribute("EGGRUMBLE_QueuedMode")==session.mode\n    and castle and castle.alive and root and hum and hum.Health>0 then
    table.insert(victims,{root=root,humanoid=hum})
   end
  end
  for id,actor in pairs(session.botActors or {}) do
   local castle=session.rules.castles[id]
   local root=actor and actor.PrimaryPart
   local hum=actor and actor:FindFirstChildOfClass("Humanoid")
   if castle and castle.alive and actor.Parent and root and hum and hum.Health>0 then
    table.insert(victims,{root=root,humanoid=hum})
   end
  end
  return victims
 end
 local function meleeLineClear(mob:Model,target:BasePart):boolean
  local root=mob.PrimaryPart
  if not root or not target.Parent then return false end
  local from=root.Position+Vector3.new(0,1,0)
  local delta=(target.Position+Vector3.new(0,1,0))-from
  if delta.Magnitude<=.01 then return true end
  local params=RaycastParams.new()
  params.FilterType=Enum.RaycastFilterType.Exclude
  params.FilterDescendantsInstances={mob,target.Parent}
  params.RespectCanCollide=true
  return workspace:Raycast(from,delta,params)==nil
 end
"""
    source = once(source, a, add + a, "victim_and_los")
    a = '''   local candidates=aliveTargets()
   if #candidates>0 then
    for m,h in pairs(live) do
'''
    b = '''   local candidates=aliveTargets()
   local victims=liveMeleeVictims()
   local meleeRays=0
   local meleeNow=os.clock()
   if #candidates>0 then
    for m,h in pairs(live) do
'''
    source = once(source, a, b, "movement_context")
    a = '''       if chosen then
        local next=at+chosen
        m:PivotTo(CFrame.lookAt(next,next+near.Unit))
       end
      end
     end
'''
    b = '''       if chosen then
        local next=at+chosen
        m:PivotTo(CFrame.lookAt(next,next+near.Unit))
       end
      end
      -- Same existing Swarm tick/neutral owner; capped melee is NOT a second AI loop.
      if meleeRays<Melee.MAX_RAYS_PER_TICK and session.rules.phase=="ACTIVE" then
       local mobRoot=m.PrimaryPart
       if mobRoot then
        -- Select the nearest READY candidate, not merely the nearest body.
        -- A victim on cooldown or behind a solid wall must not starve others.
        local eligible={}
        for index,victim in ipairs(victims) do
         local dist=(mobRoot.Position-victim.root.Position).Magnitude
         if Melee.ready(lastMeleeSwing,lastVictimHit,m,victim.humanoid,
          meleeNow,dist,true,h.Health>0,victim.humanoid.Health>0) then
          table.insert(eligible,{victim=victim,distance=dist,slot=index})
         end
        end
        table.sort(eligible,function(a,b)
         if a.distance==b.distance then return a.slot<b.slot end
         return a.distance<b.distance
        end)
        for _,candidate in ipairs(eligible) do
         if meleeRays>=Melee.MAX_RAYS_PER_TICK then break end
         meleeRays+=1
         if meleeLineClear(m,candidate.victim.root) then
          Melee.commit(lastMeleeSwing,lastVictimHit,m,candidate.victim.humanoid,meleeNow)
          -- Roblox Humanoid:TakeDamage respects ForceField.
          candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)
          break -- One real hit per soldier swing.
         end
        end
       end
      end
     end
'''
    source = once(source, a, b, "existing_movement_tick")
    source = once(source, "   live[m]=nil\n", "   live[m]=nil\n   lastMeleeSwing[m]=nil\n", "neutral_ko_memory_cleanup")
    if source.count('candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)') != 1:
        raise ValueError("RED authority: expected one real melee damage call")
    return source

def make_project(out: Path) -> None:
    project = json.loads((GAME / "EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))
    def rebase(node: dict) -> None:
        for key, value in node.items():
            if key == "$path":
                raise ValueError("unreachable")
            if isinstance(value, dict):
                if "$path" in value:
                    value["$path"] = os.path.relpath(GAME / value["$path"], out)
                else:
                    rebase(value)
    rebase(project["tree"])
    svc = project["tree"]["ServerScriptService"]
    svc["EGGRUMBLE_SwarmCombat"]["$path"] = "EGGRUMBLE_SwarmCombat.luau"
    svc["EGGRUMBLE_NeutralMeleePolicy"] = {"$path": "EGGRUMBLE_NeutralMeleePolicy.luau"}
    project["name"] = "EGGRUMBLE_GQ_NEUTRAL_MELEE_PRIVATE_NO_RC"
    (out / "EGGRUMBLE_GQ_NEUTRAL_MELEE.project.json").write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main(out: Path) -> None:
    raw = (GAME / "EGGRUMBLE_SwarmCombat.luau").read_bytes()
    if git_blob(raw) != SOURCE_BLOB:
        raise ValueError(f"RED_SOURCE_LOCK mismatch expected {SOURCE_BLOB}; actual {git_blob(raw)}")
    out.mkdir(parents=True, exist_ok=True)
    patched = patch(raw.decode("utf-8"))
    (out / "EGGRUMBLE_SwarmCombat.luau").write_text(patched, encoding="utf-8")
    pure = (HERE / "EGGRUMBLE_NeutralMeleePolicy.luau").read_text(encoding="utf-8")
    (out / "EGGRUMBLE_NeutralMeleePolicy.luau").write_text(pure, encoding="utf-8")
    make_project(out)
    receipt = {"official_RC_integrated": False, "source_parent": SOURCE_BLOB,
               "patched_swarm_sha256": hashlib.sha256(patched.encode()).hexdigest(),
               "policy_sha256": hashlib.sha256(pure.encode()).hexdigest(),
               "scripts": 22, "game_authorities": 0, "studio_tested": False}
    (out / "SOURCE_LOCK.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("SOURCE_EXACT_PRIVATE_GQ_MELEE", json.dumps(receipt))
if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    main(args.out)
