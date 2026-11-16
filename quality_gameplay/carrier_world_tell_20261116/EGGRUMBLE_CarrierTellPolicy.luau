--!strict
-- Independent, pure server-truth policy. No Game, UI, attack, rewards or Remote calls.
local Policy = {}
Policy.MAX_CARRIED_EGGS = 3
Policy.MAX_WORLD_VIEW_DISTANCE = 70
Policy.POLL_SECONDS = 0.3

Policy.ARENA_HALO_STUDS = 10

-- The original V3 author places TEAM and BR battlefields 1240 studs apart,
-- each at X width 890. Check their REAL field part bounds rather than trusting
-- the player's present Character (which can be teleported to lobby/other mode).
-- This is purely a read-only display gate, never a physics/egg-gameplay rule.
function Policy.inArenaXZ(x:any, z:any, centerX:any, centerZ:any, sizeX:any, sizeZ:any):boolean
 if type(x) ~= "number" or type(z) ~= "number"
  or type(centerX) ~= "number" or type(centerZ) ~= "number"
  or type(sizeX) ~= "number" or type(sizeZ) ~= "number" then return false end
 if x ~= x or z ~= z or centerX ~= centerX or centerZ ~= centerZ
  or sizeX ~= sizeX or sizeZ ~= sizeZ then return false end
 if sizeX <= 0 or sizeZ <= 0 then return false end
 local halo = Policy.ARENA_HALO_STUDS
 return math.abs(x - centerX) <= sizeX / 2 + halo
  and math.abs(z - centerZ) <= sizeZ / 2 + halo
end

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
