--!strict
-- GQ828_BASIC_DODGE_REAL60_20261119 | pure Luau server rules ONLY.
-- Existing SevenRoleCombat remains the sole attack owner. This policy never
-- writes HP, creates any RemoteEvent, moves Instances or processes currency.
local M={}
M.FEATURE_ID="GQ828_BASIC_DODGE_REAL60_20261119"
M.SPECS={
 WARRIOR={basic={damage=12,reach=6,radius=7,shape="BLADE",cooldown=.46},
  dodge={distance=8,cooldown=3.6}},
 MAGE={basic={damage=9,reach=11,radius=5,shape="CRYSTAL",cooldown=.55},
  dodge={distance=7,cooldown=4.0}},
 NINJA={basic={damage=11,reach=6,radius=6,shape="SHADOW",cooldown=.40},
  dodge={distance=10,cooldown=3.0}},
 TRAPPER={basic={damage=10,reach=8,radius=6,shape="PSI",cooldown=.52},
  dodge={distance=8,cooldown=3.8}},
 BUILDER={basic={damage=9,reach=10,radius=5,shape="RAIL",cooldown=.53},
  dodge={distance=7,cooldown=3.9}},
 BEAST={basic={damage=13,reach=6,radius=7,shape="FANG",cooldown=.56},
  dodge={distance=8,cooldown=3.7}},
 ZOMBIE={basic={damage=10,reach=8,radius=6,shape="CURSE",cooldown=.53},
  dodge={distance=7,cooldown=4.1}},
}
local function finite(v:any):boolean
 return type(v)=="number" and v==v and v<math.huge and v>=0
end
function M.authorize(ledger:any,role:any,action:any,now:any,ctx:any):(boolean,string?,any?)
 if type(ledger)~="table" or type(role)~="string"
  or type(action)~="string" or not finite(now)
  or type(ctx)~="table" or ctx.serverVerified~=true
  or ctx.roleVerified~=true or ctx.ownsTool~=true
  or ctx.phase~="ACTIVE"
  or (ctx.mode~="TEAM" and ctx.mode~="BATTLE_ROYALE")
  or ctx.alive~=true or ctx.castleAlive~=true
  or ctx.downed==true or ctx.eliminated==true then
  return false,"SERVER_CONTEXT_REJECTED",nil
 end
 local row=M.SPECS[role]
 if not row then return false,"UNKNOWN_ROLE",nil end
 local spec=if action=="BASIC" then row.basic
  elseif action=="DODGE" then row.dodge else nil
 if not spec then return false,"UNKNOWN_ACTION",nil end
 -- Castle/egg routing: carrier may still defend with ordinary basic strikes,
 -- but may not shortcut the objective using a dodge displacement.
 if action=="DODGE" then
  if ctx.carryingEgg==true or ctx.seated==true
   or ctx.onGround~=true or ctx.realm~="LAND" then
   return false,"DODGE_UNSAFE_MOVEMENT",nil
  end
 end
 local epoch=ctx.matchEpoch
 if type(epoch)~="string" or #epoch==0 or #epoch>128 then
  return false,"BAD_MATCH_EPOCH",nil
 end
 local key=epoch..":"..role..":"..action
 local last=ledger[key]
 if type(last)=="number" and finite(last) and now-last<spec.cooldown then
  return false,"COOLDOWN",nil
 end
 return true,key,spec
end
-- Calls to `take` must be issued by one original Tool.Activated callback.
-- Atomic no-yield validation and charge; validated next to the real hit/move.
function M.take(ledger:any,role:any,action:any,now:any,ctx:any):(boolean,string?,any?)
 local ok,key,spec=M.authorize(ledger,role,action,now,ctx)
 if not ok or not key then return false,key,nil end
 ledger[key]=now
 return true,key,spec
end
function M.validate():number
 local count=0
 for role,row in pairs(M.SPECS) do
  assert(type(role)=="string" and #role>1)
  assert(row.basic.damage>=8 and row.basic.damage<=13)
  assert(row.basic.reach>=5 and row.basic.reach<=11)
  assert(row.basic.radius>=5 and row.basic.radius<=7)
  assert(row.basic.cooldown>=.39 and row.basic.cooldown<=.60)
  assert(row.dodge.cooldown>=3 and row.dodge.cooldown<=4.1)
  assert(row.dodge.distance>=7 and row.dodge.distance<=10)
  count+=1
 end
 assert(count==7,"RED_SEVEN_ROLE_COUNT")
 return count
end
return M
