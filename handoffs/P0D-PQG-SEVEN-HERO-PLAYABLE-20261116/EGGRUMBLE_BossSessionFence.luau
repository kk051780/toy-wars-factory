--!strict
-- Pure match-membership fence for the ORIGINAL StoneGiant, shared by actual
-- V3 TEAM / BR sessions. This is NOT a new boss, enemy AI or match controller.
local Fence={}
function Fence.active(mode:string,session:any,sessions:any):boolean
 return (mode=="TEAM" or mode=="BATTLE_ROYALE")
  and sessions[mode]==session and session.rules~=nil
  and session.rules.phase=="ACTIVE" and session.rules.winner==nil
end
function Fence.mayEngage(mode:string,session:any,sessions:any,joined:any,
 userId:number,eliminated:boolean):boolean
 if eliminated or not Fence.active(mode,session,sessions) then return false end
 if joined[userId]~=mode then return false end
 local owner=session.rules.castles[tostring(userId)]
 return owner~=nil and owner.alive==true
end
return Fence
