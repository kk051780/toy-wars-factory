--!strict
-- GAME QUALITY isolated source candidate: guards delayed status damage, no world writes.
-- This is a pure Luau policy; the authoritative server computes identity evidence.
local M={}
function M.canTick(currentRules:any,originalRules:any,targetId:any,
 targetCastle:any,sameTarget:any,humanoidAlive:any):boolean
 if currentRules~=originalRules or type(originalRules)~="table" then return false end
 if originalRules.phase~="ACTIVE" or originalRules.winner~=nil then return false end
 if type(targetId)~="string" or type(originalRules.castles)~="table" then return false end
 if type(targetCastle)~="table" or originalRules.castles[targetId]~=targetCastle then return false end
 return targetCastle.alive==true and sameTarget==true and humanoidAlive==true
end
return M
