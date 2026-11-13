--!strict
-- G8 private Studio showroom: pure valid-source graph. No Roblox services or game authority.
local R={}
R.MAX_DISTANCE_SQUARED=196
R.COOLDOWN=1.6
R.NODES={
 PORT={x=0,y=0,z=0},
 SEA={x=0,y=-28,z=150},
 SKY={x=0,y=48,z=300}
}
R.ALLOWED={
 PORT={SEA=true},
 SEA={PORT=true,SKY=true},
 SKY={PORT=true,SEA=true}
}
local function finite(v: any): boolean
 return type(v)=="number" and v==v and math.abs(v)<1000000000
end
function R.validate(from: any,dest: any,distSquared: any,lastUsed: any,now: any,health: any):(boolean,string)
 if type(from)~="string" or type(dest)~="string" then return false,"BAD_NODE" end
 if not R.NODES[from] or not R.NODES[dest] or not R.ALLOWED[from][dest] then return false,"NO_ROUTE" end
 if not finite(distSquared) or distSquared<0 or distSquared>R.MAX_DISTANCE_SQUARED then return false,"TOO_FAR" end
 if not finite(now) or now<0 or not finite(lastUsed) or lastUsed>now then return false,"INVALID_CLOCK" end
 if now-lastUsed<R.COOLDOWN then return false,"COOLDOWN" end
 if not finite(health) or health<=0 then return false,"NOT_ALIVE" end
 return true,"OK"
end
function R.destination(dest: any): {x:number,y:number,z:number}?
 if type(dest)~="string" then return nil end
 local n=R.NODES[dest]
 if not n then return nil end
 return {x=n.x,y=n.y+5,z=n.z}
end
function R.symmetricAccess(team: any):boolean
 return team=="RED" or team=="BLUE" or team=="NONE"
end
return R
