--!strict
-- G7 S2+ source-only world event state machine. No Roblox API, gameplay buffs, remotes or chance-based rewards.
local D={}
D.CYCLE_SECONDS=95
D.WAIT_SECONDS=20
D.ANNOUNCE_SECONDS=5
D.ACTIVE_SECONDS=25
D.COOLDOWN_SECONDS=45
D.REALMS={"SPACE","HEAVEN","ABYSS"}
D.CARDS={
 SPACE={id="WF-13",label="星環の宇宙回廊",short="星の輪へ",cue="むらさきの輪",purpose="低重力の近道を選ぶ将来の戦術案"},
 HEAVEN={id="WF-14",label="雲上の光庭",short="雲の道へ",cue="白い鐘",purpose="天空城へ向かう将来の戦術案"},
 ABYSS={id="WF-15",label="灼熱の奈落洞",short="赤い門へ",cue="赤い門",purpose="地底からの近道を選ぶ将来の戦術案"}
}
local function integer(n)
 return type(n)=="number" and n==n and n>=0 and n<100000000 and n%1==0
end
function D.state(elapsed,seed)
 if type(elapsed)~="number" or elapsed~=elapsed or elapsed<0 or elapsed>100000000 then return nil end
 if not integer(seed) then return nil end
 local cycle=math.floor(elapsed/D.CYCLE_SECONDS)
 local within=elapsed-cycle*D.CYCLE_SECONDS
 local realm=D.REALMS[((cycle+seed)%#D.REALMS)+1]
 local phase
 local remaining
 if within<D.WAIT_SECONDS then
  phase="WAIT"
  remaining=D.WAIT_SECONDS-within
 elseif within<D.WAIT_SECONDS+D.ANNOUNCE_SECONDS then
  phase="ANNOUNCE"
  remaining=D.WAIT_SECONDS+D.ANNOUNCE_SECONDS-within
 elseif within<D.WAIT_SECONDS+D.ANNOUNCE_SECONDS+D.ACTIVE_SECONDS then
  phase="ACTIVE"
  remaining=D.WAIT_SECONDS+D.ANNOUNCE_SECONDS+D.ACTIVE_SECONDS-within
 else
  phase="COOLDOWN"
  remaining=D.CYCLE_SECONDS-within
 end
 return {phase=phase,realm=realm,field_id=D.CARDS[realm].id,
  remaining=remaining,cycle=cycle,source_only=true,world_access_is_free=true,
  server_gameplay_bonus=false,permanent_ground_route_open=true}
end
function D.isSymmetric(teamA,teamB)
 return (teamA=="RED" and teamB=="BLUE") or (teamA=="BLUE" and teamB=="RED")
end
function D.safeForCarrier(carrying)
 -- Viewing previews/using the regular permanent bridge is never blocked by egg carrying.
 return type(carrying)=="boolean"
end
return D
