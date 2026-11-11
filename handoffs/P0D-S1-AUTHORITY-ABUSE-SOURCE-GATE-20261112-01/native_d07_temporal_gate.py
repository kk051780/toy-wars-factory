#!/usr/bin/env python3
"""D07 temporal / reentrancy audit on four exact original native Luau modules.

Uses baseline's SHA-pinned four-module harness and minimal FAKE Roblox services.
Does not claim Roblox Studio physics, two-client, or final RC safety.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import native_d07_chain_gate as baseline

FIXTURE_END = "-- No test can forge the canonical activation"
TESTS = r'''
-- All four original D07 modules are genuine. This fixture provides only
-- engine-owned services and collects modeled Humanoid TakeDamage outcomes.
local samples=64
for seed=1,samples do
 local rid="temporal_"..tostring(seed)
 local f=newFixture({id=rid})
 local started, why=f.combined:start(f.activation)
 eq(started,true,"temporal_canonical_start")
 local total=0
 for attack=1,3 do
  local at=2+4*(attack-1)
  f:setNow(at-0.001)
  local quiet,err=f.combined:heartbeat()
  eq(quiet,nil,"before_windup_no_attack")
  f:setNow(at)
  local warning,werr=f.combined:heartbeat()
  eq(warning and warning.kind,"STOMP_WARNING","warning_only")
  eq(warning.attackId,attack,"warnings_ordered")
  eq(f.hum.Health,100-8*(attack-1),"warning_cannot_hit")
  eq(f.window:attests(rid,"boss_event",attack),false,"no_receipt_during_warning")
  f:setNow(at+1.999)
  local waitCmd,waitWhy=f.combined:heartbeat()
  eq(waitCmd,nil,"no_early_resolve")
  eq(f.hum.Health,100-8*(attack-1),"no_early_damage")
  f:setNow(at+2)
  local resolved,whyResolved=f.combined:heartbeat()
  eq(resolved and resolved.kind,"STOMP_RESOLVE","actual_core_resolve")
  eq(resolved.attackId,attack,"resolved_attack_order")
  total+=1
  eq(f.hum.Health,100-8*total,"one_hit_per_stomp")
  eq(f:damageCalls(),total,"one_take_damage_call_per_stomp")
  eq(f.window:attests(rid,"boss_event",attack),false,"close_receipt_after_stomp")
  local replay,replayReason=f.gate:applyServerDamage("P1",8,attack,rid,"boss_event")
  eq(replay,false,"cannot_reuse_old_attestation")
  eq(replayReason,"UNTRUSTED_ATTACK","replay_rejected_reason")
 end
 f:setNow(12.5)
 local noAttack,err=f.combined:heartbeat()
 eq(noAttack,nil,"no_fourth_stomp")
 eq(f.hum.Health,76,"three_stomp_HP_total")
 f:setNow(13)
 local ended,whyEnd=f.combined:heartbeat()
 eq(ended and ended.kind,"END","ttl_end")
 eq(f:driverStops(),1,"rig_cleanup_once")
 eq(f.hum.Health,76,"no_hit_after_expiry")
 eq(f.window:attests(rid,"boss_event",3),false,"expiry_window_closed")
end

-- Exercise a real duplicate attack while TAKE DAMAGE callback re-enters
-- the authentic Gate. Without a consumed receipt BEFORE TakeDamage, this
-- would apply twice or recurse, so the explicit code must deny DUPLICATE.
for k=1,24 do
 local rid="reentrant_"..tostring(k)
 local f=newFixture({id=rid})
 local origTake=f.hum.TakeDamage
 local retries=0
 function f.hum:TakeDamage(n)
   retries+=1
   if retries>2 then error("REENTRANT_DAMAGE_LOOP") end
   local allowed,why=f.gate:applyServerDamage("P1",8,1,rid,"boss_event")
   eq(allowed,false,"reentrant_duplicate_denied")
   eq(why,"DUPLICATE_DAMAGE","reentrant_duplicate_reason")
   origTake(self,n)
 end
 eq(f.combined:start(f.activation),true,"reentrant_start")
 f:setNow(2)
 local warning=f.combined:heartbeat()
 eq(warning and warning.kind,"STOMP_WARNING","reentrant_warning")
 f:setNow(4)
 local hit,why=f.combined:heartbeat()
 eq(hit and hit.kind,"STOMP_RESOLVE","reentrant_authentic_stomp")
 eq(f.hum.Health,92,"reentrant_exactly_once_hp")
 eq(f:damageCalls(),1,"reentrant_exactly_once_callback")
 eq(retries,1,"reentrant_callback_count")
 eq(f.window:attests(rid,"boss_event",1),false,"reentrant_window_closed")
end

-- Reentrant heartbeat triggered by visual delivery during STOMP WARNING
-- cannot advance AI a second time / cannot mint duplicate warning.
for k=1,24 do
 local rid="inflight_"..tostring(k)
 local f=newFixture({id=rid})
 eq(f.combined:start(f.activation),true,"inflight_start")
 local oldBroadcast=f.combined.deps.broadcastVisual
 local reentries=0
 f.combined.deps.broadcastVisual=function(msg)
  oldBroadcast(msg)
  if msg.kind=="STOMP" then
   reentries+=1
   local cmd,reason=f.combined:heartbeat()
   eq(cmd,nil,"no_reentrant_new_cmd")
   eq(reason,"REENTRANT_HEARTBEAT","reentrant_heartbeat_denied")
  end
 end
 f:setNow(2)
 local warning,why=f.combined:heartbeat()
 eq(warning and warning.kind,"STOMP_WARNING","inflight_warning")
 eq(reentries,1,"single_warning_callback")
 f:setNow(4)
 local stomp,why=f.combined:heartbeat()
 eq(stomp and stomp.kind,"STOMP_RESOLVE","inflight_subsequent_resolve")
 eq(f.hum.Health,92,"inflight_one_hit")
end
if checks<3500 then error("TEMPORAL_INSUFFICIENT_CHECKS "..tostring(checks),0) end
print("P0D_NATIVE_D07_TEMPORAL_PASS assertions="..tostring(checks))
'''
MUTATIONS = [
    # each mutation runs the exact full authentic source except one modified anchor
    ("reentrant_double_hit", "GoroganDamageBoundary.luau",
     "self.receipts[key]=true;self.total+=1",
     "self.total+=1", 1),
    ("wrong_reentrant_reason", "GoroganCombinedRuntime.luau",
     'if self.busy then return nil,"REENTRANT_HEARTBEAT" end',
     'if false then return nil,"REENTRANT_HEARTBEAT" end', 1),
    ("early_first_stomp", "GoroganServerAICore.luau",
     "and input.now >= a.nextAttackAt", "and true", 1),
    ("skip_windup", "GoroganServerAICore.luau",
     "if input.now < a.windupEnds then return nil,nil end",
     "if false then return nil,nil end", 1),
]

def run_native(luau: str, path: Path, sources: dict[str, str]) -> tuple[int, str]:
    old = baseline.LUAU_TEST
    marker = old.find(FIXTURE_END)
    if marker == -1:
        raise RuntimeError("UNEXPECTED_BASELINE_FIXTURE_LAYOUT")
    program = baseline.build(sources)
    if program.count(old) != 1:
        raise RuntimeError("ORIGINAL_TEST_BLOCK_NOT_UNIQUE")
    program = program.replace(old, old[:marker] + TESTS, 1)
    path.write_text(program, encoding="utf-8")
    p = subprocess.run(
        [luau, str(path)], capture_output=True, text=True, check=False, timeout=25
    )
    return p.returncode, p.stdout + p.stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--luau", required=True)
    args = parser.parse_args()
    authentic = baseline.verified_source(args.repo)
    with TemporaryDirectory(prefix="p0d_d07_temporal_") as temp:
        path = Path(temp) / "original_d07_temporal.luau"
        result, output = run_native(args.luau, path, authentic)
        m = re.search(r"P0D_NATIVE_D07_TEMPORAL_PASS assertions=(\d+)", output)
        if result != 0 or m is None or int(m.group(1)) < 3500:
            raise RuntimeError("GENUINE_FOUR_MODULE_TEMPORAL_FAILURE " + output[-1000:])
        print("4/4 SHA_LOCKED_ORIGINAL_SOURCE " + m.group(0))
        for name, source, old, new, count in MUTATIONS:
            original_text = authentic[source]
            if original_text.count(old) != count:
                raise RuntimeError("SOURCE_MUTATION_NOT_UNIQUE " + name)
            mutated = dict(authentic)
            mutated[source] = original_text.replace(old, new, 1)
            status, details = run_native(args.luau, path, mutated)
            if status == 0 or ("ASSERT_" not in details
                                and "TEMPORAL_INSUFFICIENT" not in details):
                raise RuntimeError("MUTATION_UNDETECTED " + name + " " + details[-550:])
            print("MUTATION_REJECTED " + name)
        print("P0D_NATIVE_D07_TEMPORAL_NEGATIVE_CONTROLS=" + str(len(MUTATIONS)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, UnicodeError, OSError, subprocess.TimeoutExpired) as exc:
        print("P0D_NATIVE_D07_TEMPORAL_BLOCKED " + str(exc), file=sys.stderr)
        sys.exit(1)
