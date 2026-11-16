#!/usr/bin/env python3
"""Execute the REAL pure Luau melee policy in the Luau CLI, no mocked PASS."""
import argparse
from pathlib import Path

P = Path(__file__).resolve().parent / "EGGRUMBLE_NeutralMeleePolicy.luau"
CHECKS = r"""
local s={}
local v={}
assert(Policy.DAMAGE==4 and Policy.RANGE==4.25)
assert(Policy.MAX_RAYS_PER_TICK==24)
assert(Policy.ready(s,v,"soldier1","hero1",100,4.2,true,true,true))
Policy.commit(s,v,"soldier1","hero1",100)
assert(s.soldier1==100 and v.hero1==100)
assert(not Policy.ready(s,v,"soldier1","hero2",101,4,true,true,true))
assert(not Policy.ready(s,v,"soldier2","hero1",100.5,4,true,true,true))
assert(Policy.ready(s,v,"soldier2","hero2",101,4,true,true,true))
assert(not Policy.ready(s,v,"soldier2","hero2",101,4.251,true,true,true))
assert(not Policy.ready(s,v,"soldier2","hero2",101,4,false,true,true))
assert(not Policy.ready(s,v,"soldier2","hero2",101,4,true,false,true))
assert(not Policy.ready(s,v,"soldier2","hero2",101,4,true,true,false))
assert(not Policy.ready(s,v,"soldier2","hero2",101,-1,true,true,true))
assert(not Policy.ready(s,v,"soldier2","hero2",0/0,4,true,true,true))
assert(not Policy.ready(s,v,"soldier2","hero2",101,0/0,true,true,true))
assert(Policy.ready(s,v,"soldier1","hero1",101.5,4,true,true,true))
assert(s.soldier1==100 and v.hero1==100) -- no LOS/no commit leaves the lease unspent
Policy.commit(s,v,"soldier1","hero1",101.5)
assert(not Policy.ready(s,v,"soldier1","hero1",101.6,0,true,true,true))
assert(Policy.ready(s,v,"soldier3","hero1",102.31,4,true,true,true))
print("EGGRUMBLE_NEUTRAL_MELEE_PURE_POLICY_NATIVE_PASS")
"""
def main(out:Path):
    code=P.read_text(encoding="utf-8")
    if not code.endswith("return Policy\n"):
        raise SystemExit("RED: pure policy final return changed")
    out.write_text(code[:-len("return Policy\n")] + CHECKS, encoding="utf-8")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    main(args.out)
