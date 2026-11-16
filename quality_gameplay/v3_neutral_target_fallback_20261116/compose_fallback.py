#!/usr/bin/env python3
"""Source-locked single-Swarm fallback for #533's existing melee attack selection.

Takes an already composed original-author Swarm script, patches exactly one
selection block and writes a separate candidate. Never writes source in place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

OLD = '''      if meleeRays<Melee.MAX_RAYS_PER_TICK and session.rules.phase=="ACTIVE" then
       local mobRoot=m.PrimaryPart
       local nearest=nil
       local range=Melee.RANGE
       if mobRoot then
        for _,victim in ipairs(victims) do
         local dist=(mobRoot.Position-victim.root.Position).Magnitude
         if dist<=range then nearest=victim;range=dist end
        end
        if nearest and Melee.ready(lastMeleeSwing,lastVictimHit,m,nearest.humanoid,
         meleeNow,range,true,h.Health>0,nearest.humanoid.Health>0) then
         meleeRays+=1
         if meleeLineClear(m,nearest.root) then
          Melee.commit(lastMeleeSwing,lastVictimHit,m,nearest.humanoid,meleeNow)
          -- Roblox Humanoid:TakeDamage respects ForceField; no custom score/egg mutation.
          nearest.humanoid:TakeDamage(Melee.DAMAGE)
         end
        end
       end
      end
'''
NEW = '''      if meleeRays<Melee.MAX_RAYS_PER_TICK and session.rules.phase=="ACTIVE" then
       local mobRoot=m.PrimaryPart
       if mobRoot then
        local inRange={}
        for _,victim in ipairs(victims) do
         local dist=(mobRoot.Position-victim.root.Position).Magnitude
         if dist<=Melee.RANGE then
          table.insert(inRange,{target=victim,distance=dist})
         end
        end
        table.sort(inRange,function(a:any,b:any):boolean return a.distance<b.distance end)
        -- A cooling or walled nearest victim must not suppress a valid next target.
        -- Count every actual ray attempt against ONE existing shared per-tick cap.
        for _,candidate in ipairs(inRange) do
         if meleeRays>=Melee.MAX_RAYS_PER_TICK then break end
         local victim=candidate.target
         if Melee.ready(lastMeleeSwing,lastVictimHit,m,victim.humanoid,
          meleeNow,candidate.distance,true,h.Health>0,victim.humanoid.Health>0) then
          meleeRays+=1
          if meleeLineClear(m,victim.root) then
           Melee.commit(lastMeleeSwing,lastVictimHit,m,victim.humanoid,meleeNow)
           -- Same sole Swarm damage authority; no second loop/score/egg mutation.
           victim.humanoid:TakeDamage(Melee.DAMAGE)
           break
          end
         end
        end
       end
      end
'''

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def apply(source: str) -> str:
    if source.count(OLD) != 1:
        raise ValueError(f"RED_SOURCE_DRIFT: original #533 nearest-only block count={source.count(OLD)}")
    if source.count("local Melee=require(") != 1:
        raise ValueError("RED_AUTHORITY_DRIFT: must have exactly one existing #533 melee policy")
    if source.count("lastMeleeSwing[m]=nil") != 1:
        raise ValueError("RED_COOLDOWN_LIFECYCLE_DRIFT: #533 weak-key/KO cleanup absent")
    fixed = source.replace(OLD, NEW, 1)
    if fixed.count("victim.humanoid:TakeDamage(Melee.DAMAGE)") != 1:
        raise ValueError("RED_DOUBLE_DAMAGE_AUTHORITY")
    if fixed.count("Melee.commit(") != 1:
        raise ValueError("RED_DOUBLE_MELEE_COMMIT")
    if fixed.count("meleeRays+=1") != 1:
        raise ValueError("RED_RAY_BUDGET_DRIFT")
    return fixed

def emit(source_path: Path, expected_sha256: str, out: Path) -> dict:
    source_path = source_path.resolve(strict=True)
    out = out.resolve()
    if out == source_path or out.exists():
        raise ValueError("RED_NO_INPLACE_OR_OVERWRITE")
    raw = source_path.read_bytes()
    if sha256(raw) != expected_sha256:
        raise ValueError("RED_INPUT_SHA256_MISMATCH: source changed, recapture expected hash")
    candidate = apply(raw.decode("utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    data = candidate.encode("utf-8")
    out.write_bytes(data)
    receipt = {
        "feature": "GQ_V3_NEUTRAL_MELEE_ELIGIBLE_TARGET_FALLBACK_20261116",
        "original_author_pr": 533,
        "original_source_sha256": sha256(raw),
        "candidate_source_sha256": sha256(data),
        "swarm_authority_count": 1,
        "damage_calls": 1,
        "ray_cap_per_tick": 24,
        "changed_runtime_script_count": 1,
        "private_candidate_only": True,
        "formal_rc_adopted": False,
        "studio_android_tested": False,
    }
    out.with_name(out.name + ".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="Pinned generated #533 or #530 composite Swarm")
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(emit(args.source, args.expected_sha256, args.out), indent=2))
