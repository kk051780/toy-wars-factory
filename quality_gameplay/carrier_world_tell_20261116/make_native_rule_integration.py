#!/usr/bin/env python3
"""Run source-exact #482 CastleMatchRules + this PR's WorldTell in one native Luau VM.

Use the original real egg issuance, theft, deposit, elimination, and castle
attack logic. All Roblox Instancing is mocked; NOT a Studio/Android claim.
"""
import argparse
from pathlib import Path
from make_native_world_harness import PRELUDE
from compose import AUTHOR

HERE = Path(__file__).resolve().parent

CASES = r'''
local function captionOn(root)
 local _,gui=liveOn(root)
 if not gui then return nil end
 for _,child in ipairs(__instances) do
  if child.__class=="TextLabel" and child.Parent==gui then return child.Text end
 end
 return nil
end

-- Do not fake heldEggs here: read the #482 author's REAL match rules instead.
local roster=RealRules.makeRoster("TEAM",{"301","302"},16)
eq("actual original TEAM 16-seat roster",#roster,16)
local state=RealRules.new("TEAM",roster,24)
RealRules.start(state)
eq("real original match ACTIVE",state.phase,"ACTIVE")
local bots={}
local roots={}
for _,entry in ipairs(roster) do
 local actor,rt,hum=makeAvatar("real_team_"..entry.id)
 roots[entry.id]=rt
 if entry.isAI then bots[entry.id]=actor
 else __players[tonumber(entry.id)]={Character=actor} end
end
local sess={mode="TEAM",world=makeWorld("TEAM"),rules=state,roster=roster,botActors=bots}
eq("real match starts read-only tell",NativeTell.start(sess),true)
step()
eq("original all castles initially empty",countLiveAll(),0)
local initial=RealRules.auditEggConservation(state)
eq("original 16-castle egg conservation starts valid",initial.valid,true)
eq("original 24 physically sourced field egg count",state.fieldEggs,24)
eq("real FIELD_1 first pickup",RealRules.takeFieldEgg(state,"301","FIELD_1"),1)
step()
eq("one actual server-carrier label",countLiveAll(),1)
eq("correct actual RealRules egg caption 1",captionOn(roots["301"]),"🥚×1")
local reuseOk=pcall(function() RealRules.takeFieldEgg(state,"301","FIELD_1") end)
eq("author duplicate egg ID cannot create phantom badge",reuseOk,false)
eq("one egg after replay rejection",state.castles["301"].heldEggs,1)
eq("real enemy vault steal into carrier",RealRules.takeEggs(state,"301",1,"302"),2)
step()
eq("actual server egg caption 2",captionOn(roots["301"]),"🥚×2")
eq("real FIELD_2 pickup",RealRules.takeFieldEgg(state,"301","FIELD_2"),3)
step()
eq("actual server egg caption 3",captionOn(roots["301"]),"🥚×3")
local overCapOk=pcall(function() RealRules.takeEggs(state,"301",1,"302") end)
eq("author carrying max 3 unchanged",overCapOk,false)
eq("real deposit returns eggs to castle",RealRules.depositEggs(state,"301",3),3)
step()
eq("deposited carrier badge cleared",liveOn(roots["301"]),0)
eq("original TEAM deposit counter exact",state.teamDeposits.RED,3)
eq("real rules conservation remains valid",RealRules.auditEggConservation(state).valid,true)

-- Neutral bot/human ownership handoff remains from original BotActors. The
-- carrier badge only observes server Rules; it never creates a new item/AI.
eq("actual AI steals from opposed castle",RealRules.takeEggs(state,"AI_1",1,"302"),1)
step()
eq("actual AI's server-truth label",captionOn(roots["AI_1"]),"🥚×1")
local dropped,dropIds=RealRules.onCarrierEliminated(state,"AI_1")
eq("real AI carrier drops 1",dropped,1)
eq("unique real carrier drop token",#dropIds,1)
step()
eq("AI drop clears display",liveOn(roots["AI_1"]),0)
eq("real AI drop conserves inventory",RealRules.auditEggConservation(state).valid,true)
eq("real human pickup after AI drop",RealRules.takeFieldEgg(state,"301",dropIds[1]),1)
step()
eq("reissued real dropped egg visible",captionOn(roots["301"]),"🥚×1")
local droppedHuman,humanTokens=RealRules.onCarrierEliminated(state,"301")
eq("human carrier dropped real egg",droppedHuman,1)
step()
eq("human death egg marker removed",liveOn(roots["301"]),0)
eq("real human drop conserves inventory",RealRules.auditEggConservation(state).valid,true)

-- Real castle loss must suppress the marker and release the egg through
-- the original Rules, not through any new carrier counting authority.
eq("human reclaims 1 real egg",RealRules.takeFieldEgg(state,"301",humanTokens[1]),1)
step()
eq("human marker back before castle falls",liveOn(roots["301"]),1)
for i=1,4 do
 RealRules.damageCastle(state,"301","302",250)
end
eq("actual authored castle fallen",state.castles["301"].alive,false)
step()
eq("castle fallen label removed despite live Avatar",liveOn(roots["301"]),0)
eq("author original castle destruction still conserved eggs",RealRules.auditEggConservation(state).valid,true)
eq("TEAM still ACTIVE with additional red and blue bots",state.phase,"ACTIVE")

-- Native TEAM and BR together. This tests live server Rules independently
-- without touching original role/FX/item/neutral/lobby scripts.
eq("real TEAM AI picks another field egg",RealRules.takeFieldEgg(state,"AI_1","FIELD_4"),1)
step()
eq("TEAM AI still visible",captionOn(roots["AI_1"]),"🥚×1")
local brRoster=RealRules.makeRoster("BATTLE_ROYALE",{"401"},16)
local brRules=RealRules.new("BATTLE_ROYALE",brRoster,24)
RealRules.start(brRules)
local brBots={}
local brRoots={}
for _,entry in ipairs(brRoster) do
 local actor,rt,hum=makeAvatar("real_br_"..entry.id)
 rt.Position=Vector3.new(620,5,465)
 brRoots[entry.id]=rt
 if entry.isAI then brBots[entry.id]=actor
 else __players[tonumber(entry.id)]={Character=actor} end
end
local br={mode="BATTLE_ROYALE",world=makeWorld("BATTLE_ROYALE"),
 roster=brRoster,botActors=brBots,rules=brRules}
eq("real BR starts while TEAM active",NativeTell.start(br),true)
eq("BR real first egg pickup",RealRules.takeFieldEgg(brRules,"401","FIELD_1"),1)
step()
eq("BR human real egg marker",captionOn(brRoots["401"]),"🥚×1")
eq("TEAM AI coexists with BR real Rules",captionOn(roots["AI_1"]),"🥚×1")
eq("real two-mode egg conservation TEAM",RealRules.auditEggConservation(state).valid,true)
eq("real two-mode egg conservation BR",RealRules.auditEggConservation(brRules).valid,true)
sess.world.Parent=nil
step()
eq("original TEAM world end removes only TEAM badges",liveOn(roots["AI_1"]),0)
eq("original BR world still has badge",liveOn(brRoots["401"]),1)
brRoots["401"].Position=Vector3.new(-620,5,465)
step()
eq("actual BR egg blocked after TEAM teleport",liveOn(brRoots["401"]),0)
brRoots["401"].Position=Vector3.new(620,5,465)
step()
eq("BR egg restored in own arena",captionOn(brRoots["401"]),"🥚×1")
RealRules.depositEggs(brRules,"401",1)
step()
eq("real BR egg deposited -> badge hidden",liveOn(brRoots["401"]),0)
eq("real BR eggs conserved",RealRules.auditEggConservation(brRules).valid,true)

-- True V3 rule engine continues to issue eggs, but optional tell can be
-- disabled/re-enabled safely by server control without new token authority.
br.carrierWorldTellEnabled=false
step()
eq("real BR kill switch finishes only cosmetic worker",br._carrierWorldTellStarted,nil)
eq("real BR kill switch keeps all markers hidden",countLiveAll(),0)
eq("real BR second field egg minted by original rules",RealRules.takeFieldEgg(brRules,"401","FIELD_2"),1)
step()
eq("real egg cannot bypass disabled carrier tell",liveOn(brRoots["401"]),0)
eq("disabled UI does not corrupt egg conservation",RealRules.auditEggConservation(brRules).valid,true)
eq("BR refuses to restart during OFF",NativeTell.start(br),false)
br.carrierWorldTellEnabled=true
eq("real BR explicit ON restarts once",NativeTell.start(br),true)
step()
eq("real egg shows after turning optional display ON",captionOn(brRoots["401"]),"🥚×1")
br.carrierWorldTellEnabled=false
step()
eq("OFF removes real-rule carrier badge again",liveOn(brRoots["401"]),0)
eq("OFF does not consume real-rule carried egg",brRules.castles["401"].heldEggs,1)
eq("OFF keeps total real eggs valid",RealRules.auditEggConservation(brRules).valid,true)
br.world.Parent=nil
step()
eq("real two mode teardown complete",countLiveAll(),0)
eq("native actual original real-rules loops cleaned",#__threads,0)
print("NATIVE_ORIGINAL_RULES_TO_WORLD_TELL_INTEGRATION_PASS checks="..tostring(checks))
'''

def make(out: Path):
    policy=(HERE/"EGGRUMBLE_CarrierTellPolicy.luau").read_text(encoding="utf-8")
    tell=(HERE/"EGGRUMBLE_CarrierWorldTell.luau").read_text(encoding="utf-8")
    rules=(AUTHOR/"EGGRUMBLE_CastleMatchRules.luau").read_text(encoding="utf-8")
    for src,marker in ((policy,"\nreturn Policy\n"),(tell,"\nreturn Tell\n"),(rules,"\nreturn M\n")):
        assert src.count(marker)==1, "RED: upstream canonical module changed"
    full=(policy.replace("\nreturn Policy\n","\nlocal NativePolicy=Policy\n",1)
          +"\n"+PRELUDE
          +"\n"+rules.replace("\nreturn M\n","\nlocal RealRules=M\n",1)
          +"\n"+tell.replace("\nreturn Tell\n","\nlocal NativeTell=Tell\n",1)
          +"\n"+CASES)
    out.write_text(full,encoding="utf-8")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    make(args.out)
