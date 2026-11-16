#!/usr/bin/env python3
"""Exercise the original #482 authoritative ImpactFeedback.attacker and #504
LocalScript together in one real Luau VM, through actual SetAttribute signals.

Only services are mocked: NO duplicate hit implementation and NO claimed Studio playtest.
"""
import argparse
from pathlib import Path

from make_native_hit_audio_harness import PRELUDE

AUDIO = Path(__file__).resolve().parents[1] / "EGGRUMBLE_RealHitAudio.client.luau"
TESTS = r'''
local checks=0
local function check(x,reason)
 checks+=1
 assert(x,reason)
end
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local distinct={}
player.UserId=52
player.Parent=soundService
function player:SetAttribute(name,value)
 attributes[name]=value
 local sig=signals[name]
 if sig then sig:Fire() end
end
local n=#plays
check(Feedback.attacker(player,"WARRIOR","A",0)==false,"server miss rejected")
check(#plays==n,"no audio from missed attack")
for i,role in ipairs(roles) do
 fakeTime=1+i*.35
 local ok=Feedback.attacker(player,role,"A",i==3 and 9 or 1)
 check(ok,"server must issue confirmed hit")
 check(attributes.EGGRUMBLE_ImpactRole==role,"role authoritative and read correctly")
 check(attributes.EGGRUMBLE_ImpactSequence==i,"single sequence per accepted hit")
 check(#plays==i,"client reacts exactly once to real server sequence")
 distinct[plays[i].id]=true
 if i==3 then check(attributes.EGGRUMBLE_ImpactWeight==3,"server clamps multi-target hit weight") end
end
local unique=0
for _ in pairs(distinct) do unique+=1 end
check(unique==7,"seven unique confirmed-hit audio profiles")
local before=#plays
fakeTime=5
check(Feedback.attacker(player,"MAGE","A",1)==true,"first hit accepted")
check(Feedback.attacker(player,"MAGE","A",1)==false,"server cooldown suppresses duplicate")
check(#plays==before+1,"only one client pulse during cooldown")
player:SetAttribute("EGGRUMBLE_SFXMuted",true)
local silence=true
for _,v in ipairs(objects) do
 if v.ClassName=="Sound" and v.playing then silence=false end
end
check(silence,"mute stops existing authoritative hit")
fakeTime=5.4
check(Feedback.attacker(player,"NINJA","B",2)==true,"server hit still valid while client muted")
check(#plays==before+1,"client never overrides local mute")
player:SetAttribute("EGGRUMBLE_SFXMuted",false)
player.Parent=nil
fakeTime=5.8
check(Feedback.attacker(player,"BUILDER","C",2)==false,"server rejects removed attacker")
check(#plays==before+1,"removed attacker causes no sound")
player.Parent=soundService
fakeTime=6.2
check(Feedback.attacker(player,"ZOMBIE","C",1)==true,"server can resume")
check(#plays==before+2,"client resumes on new confirmed hit only")
player.AncestryChanged:Fire(player,nil)
print("GQ_SERVER_TO_CLIENT_REAL_HIT_PIPELINE_NATIVE_PASS",checks,"checks")
'''
def make(source: str) -> str:
    begin = source.index("function Feedback.attacker(")
    end = source.index("\nreturn Feedback",begin)
    actual = source[begin:end]
    for token in ('if actualHits<=0', 'ImpactSequence', 'SetAttribute(', 'ATTACKER_FEEDBACK_CD'):
        if token == 'ATTACKER_FEEDBACK_CD':
            assert token in actual
        else:
            assert token in actual, token
    audio = AUDIO.read_text(encoding="utf-8")
    return (PRELUDE + """
local Feedback={}
local ATTACKER_FEEDBACK_CD=.16
local nextAttacker={}
""" + actual + """
do
""" + audio + """
end
""" + TESTS)
if __name__ == "__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--author-impact", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    a=cli.parse_args()
    a.out.write_text(make(a.author_impact.read_text(encoding="utf-8")),encoding="utf-8")
