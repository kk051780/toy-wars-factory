--!strict
-- Independent, pure server-truth policy. No Game, UI, attack, rewards or Remote calls.
local Policy = {}
Policy.MAX_CARRIED_EGGS = 3
Policy.MAX_WORLD_VIEW_DISTANCE = 70
Policy.POLL_SECONDS = 0.3

function Policy.shouldShow(phase:string?, winner:any, castle:any, avatarAlive:boolean):boolean
 if phase ~= "ACTIVE" or winner ~= nil or avatarAlive ~= true then return false end
 if type(castle) ~= "table" or castle.alive ~= true then return false end
 local eggs = castle.heldEggs
 return type(eggs) == "number" and eggs == eggs and eggs%1 == 0
  and eggs >= 1 and eggs <= Policy.MAX_CARRIED_EGGS
end

function Policy.caption(eggs:number):string
 assert(type(eggs) == "number" and eggs%1 == 0 and eggs >= 1 and eggs <= 3, "invalid carried eggs")
 return "🥚×"..tostring(eggs)
end
return Policy
