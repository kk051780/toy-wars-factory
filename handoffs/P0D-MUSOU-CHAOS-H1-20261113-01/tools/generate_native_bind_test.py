#!/usr/bin/env python3
"""Generate native Luau checks from the exact isolated original rules source."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"inputs/MusouBindRules.luau").read_text("utf-8")
assert src.count("return Rules")==1
test=r'''
local R=(function()
__MODULE__
end)()
local function patch(src,key,value)
    local t={}
    for k,v in pairs(src) do t[k]=v end
    t[key]=value
    return t
end
local net={
 phase="ACTIVE",role="GUARDIAN",team="RED",alive=true,
 egg=false,bound=false,now=100,last=0,
}
local target={
 enemy=true,alive=true,bound=false,immune=false,invulnerable=false,
 distance=7,facing=.8,visible=true
}
local rescue={
 phase="ACTIVE",teammate=true,alive=true,targetBound=true,
 visible=true,distance=6
}
local checks={
 {"net_allow",R.canNet(net),true},
 {"net_lobby",R.canNet(patch(net,"phase","LOBBY")),false},
 {"net_raider",R.canNet(patch(net,"role","RAIDER")),false},
 {"net_carry",R.canNet(patch(net,"egg",true)),false},
 {"net_bound",R.canNet(patch(net,"bound",true)),false},
 {"net_cooldown",R.canNet(patch(net,"last",95)),false},
 {"net_none",R.canNet(patch(net,"team","NONE")),false},
 {"net_dead",R.canNet(patch(net,"alive",false)),false},
 {"target_allow",R.canTarget(target),true},
 {"target_ally",R.canTarget(patch(target,"enemy",false)),false},
 {"target_immune",R.canTarget(patch(target,"immune",true)),false},
 {"target_respawn",R.canTarget(patch(target,"invulnerable",true)),false},
 {"target_occluded",R.canTarget(patch(target,"visible",false)),false},
 {"target_behind",R.canTarget(patch(target,"facing",-.4)),false},
 {"target_far",R.canTarget(patch(target,"distance",15)),false},
 {"break_allow",R.canBreak({kind="NET",startedAt=10},10.5),true},
 {"break_too_soon",R.canBreak({kind="NET",startedAt=10},10.2),false},
 {"rescue_allow",R.canRescue(rescue),true},
 {"rescue_far",R.canRescue(patch(rescue,"distance",9)),false},
 {"rescue_enemy",R.canRescue(patch(rescue,"teammate",false)),false},
}
assert(#checks == 20)
for _,x in ipairs(checks) do
    assert(x[2]==x[3], "MUSOU_BIND_FAIL_"..tostring(x[1]))
end
print("MUSOU_BIND_NATIVE_20_ASSERTIONS_PASS")
'''
test=test.replace("__MODULE__",src)
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",required=True)
    opts=ap.parse_args()
    out=Path(opts.write)
    out.write_text(test,encoding="utf-8")
    print("MUSOU_BIND_NATIVE_TEST_SOURCE_GENERATED",out)
