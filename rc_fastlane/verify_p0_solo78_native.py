#!/usr/bin/env python3
"""Execute REAL final Game's solo mode assignment in native Luau; no Studio engine."""
from __future__ import annotations
import argparse,re
from pathlib import Path
def verify(dist:Path,out:Path)->None:
    s=(dist/"src/server/Game.server.luau").read_text("utf8")
    h=(dist/"src/client/HUD.client.luau").read_text("utf8")
    old='EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE'
    assert old not in s and s.count('EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio()')==1
    assert s.count('remote.OnServerEvent:Connect(')==1
    assert 'pcall(SoloTeamBots.start,map,' in s
    assert 'and not EXPERIMENTAL_FIVE_EGG_MODE then' in s
    m=re.search(r'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio\(\)\s+and #Players:GetPlayers\(\)>1 and chosenMode==ModeVote.SCORE',s)
    assert m,"ACTUAL_GAME_SOLO_MODE_SELECTOR_NOT_FOUND"
    assert 'soloFiveEggUnavailable = RunService:IsStudio()' in s
    assert 'soloFiveEggUnavailable' in h and '味方2・敵3' in h
    assignment=m.group(0)
    luau=r'''-- Real mode-selection source extracted from the actual 78-file Game.
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={studio=true}
function RunService:IsStudio() return self.studio end
local ModeVote={SCORE="SCORE",CLASSIC="CLASSIC"}
local chosenMode=ModeVote.SCORE
local EXPERIMENTAL_FIVE_EGG_MODE=false
local function selectMode(n,studio,mode)
  Players.online={}
  for _=1,n do table.insert(Players.online,{}) end
  RunService.studio=studio
  chosenMode=mode
'''+assignment+r'''
  return EXPERIMENTAL_FIVE_EGG_MODE
end
assert(not selectMode(0,true,ModeVote.SCORE),"EMPTY_LOBBY_CANNOT_ENABLE_H2")
assert(not selectMode(1,true,ModeVote.SCORE),"ONE_HUMAN_SCORE_VOTE_MUST_BE_CLASSIC")
assert(not selectMode(1,true,ModeVote.CLASSIC),"ONE_HUMAN_CLASSIC")
assert(selectMode(2,true,ModeVote.SCORE),"TWO_HUMAN_SCORE_VOTE_PRESERVED")
assert(not selectMode(2,true,ModeVote.CLASSIC),"TWO_HUMAN_CLASSIC_PRESERVED")
assert(selectMode(3,true,ModeVote.SCORE),"MULTIPLAYER_SCORE_VOTE_PRESERVED")
assert(not selectMode(1,false,ModeVote.SCORE),"NON_STUDIO_NO_H2")
assert(not selectMode(2,false,ModeVote.SCORE),"NON_STUDIO_TWO_HUMANS_NO_STUDIO_H2")
assert(not selectMode(3,false,ModeVote.CLASSIC),"CLASSIC_FALSE_EVERYWHERE")
print("P0_PRIVATE78_REAL_GAME_SOLO_CLASSIC_MODE_9_NATIVE_CASES_PASS")
'''
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(luau,"utf8")
    print("P0_PRIVATE78_ACTUAL_GAME_SOLO_MODE_SOURCE_EXACT_PASS",len(assignment))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.out)
