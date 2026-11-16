#!/usr/bin/env python3
"""Run original #484 AI action LOS real source with parented-live-part fixtures.

Original test fixture predates the new targetPart.Parent guard. Rather than
overwriting the owner's test or BotActors, adapt the TEST FIXTURE in memory only,
add destroyed world-target case and prove its negative mutation is rejected.
Native Luau VM only, not Studio physics.
"""
import argparse
import importlib.util
from pathlib import Path

def load_test(path: Path):
    spec=importlib.util.spec_from_file_location("owner_action_los_test",path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--luau",required=True,type=Path)
    ap.add_argument("--quality",required=True,type=Path)
    args=ap.parse_args()
    quality=args.quality.resolve(strict=True)
    source=(quality/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_BotActors.luau")
    original_test=(quality/"quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/test_action_los_native.py")
    spec=load_test(original_test)
    guard=spec.extracted(source.read_text(encoding="utf-8"))
    gate='if not targetPart or not targetPart.Parent then return false end'
    assert gate in guard,"ghost-target guard missing: reconcile with game author"
    before='local targetPart={Name="EggVault"}'
    after='local targetPart={Name="EggVault",Parent={}}'
    assert spec.HEADER.count(before)==1,"owner fixture changed"
    spec.HEADER=spec.HEADER.replace(before,after)
    ray_test='if math.abs(pos.Y-goal.Y)<=4 and (goal-(pos+Vector3.new(0,.4,0))).Magnitude>.01 then'
    assert spec.FOOTER.count(ray_test)==1,"owner fixture raycase drift"
    spec.FOOTER=spec.FOOTER.replace(ray_test,
        'if interactable~=nil and math.abs(pos.Y-goal.Y)<=4 and (goal-(pos+Vector3.new(0,.4,0))).Magnitude>.01 then')
    extra=r"""
-- A real but destroyed target does not create phantom egg/castle action.
local gone={Name="EggVault",Parent=nil}
actor.position=Vector3.new(0,1,0)
nextHit=nil
assert(clearActionPath(actor,actors,Vector3.new(3,1,0),gone)==false,
       "destroyed target must fail closed, even if LOS ray is clear")
print("GQ_GHOST_TARGET_NEGATIVE_NATIVE_PASS")
"""
    spec.FOOTER+=extra
    actual=spec.run(args.luau,guard)
    assert actual.returncode==0,(actual.stdout,actual.stderr)
    assert "GQ_ACTION_LOS_NATIVE_PASS cases=9" in actual.stdout
    assert "GQ_GHOST_TARGET_NEGATIVE_NATIVE_PASS" in actual.stdout
    mutation=guard.replace(gate,"")
    assert mutation!=guard
    bad=spec.run(args.luau,mutation)
    assert bad.returncode!=0,"mutation removed live-target check but still passed"
    print("GQ_ORIGINAL_AI_LOS_LIVE_TARGET_NATIVE_PASS")
    print("GQ_GHOST_TARGET_GUARD_MUTATION_REJECTED")
if __name__=="__main__":
    main()
