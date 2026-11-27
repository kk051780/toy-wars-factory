--!strict
-- This is INTAKE, not another item implementation: compose the existing
-- EGGRUMBLE_FieldItemPickups author-owned module into both real V3 modes.
-- 3 route rows x 3 positions = 9 consumables, Latin-square class placement.
-- Each corridor and each lateral side sees HEAL/DASH/SHIELD once.
local RaidItems={}
local FIXED={
 {x=-140,z=300,kind="HEAL"},
 {x=0,z=300,kind="DASH"},
 {x=140,z=300,kind="SHIELD"},
 {x=140,z=470,kind="HEAL"},
 {x=-140,z=470,kind="DASH"},
 {x=0,z=470,kind="SHIELD"},
 {x=0,z=640,kind="HEAL"},
 {x=140,z=640,kind="DASH"},
 {x=-140,z=640,kind="SHIELD"},
}
function RaidItems.offsets():{any}
 -- Return independent values, so shared author data can never be modified
 -- by a consumer or a different concurrent mode.
 local out={}
 for _,v in ipairs(FIXED) do
  table.insert(out,{x=v.x,z=v.z,kind=v.kind})
 end
 return out
end
function RaidItems.validate():boolean
 assert(#FIXED==9,"9 item sites required")
 local rows:{[number]:{[string]:boolean}}={}
 local columns:{[number]:{[string]:boolean}}={}
 local used={}
 for i,v in ipairs(FIXED) do
  local expected=({"HEAL","DASH","SHIELD"})[(i-1)%3+1]
  assert(v.kind==expected,"external item author cycles types in HEAL/DASH/SHIELD order")
  assert(v.x>=-145 and v.x<=145 and (v.x==-140 or v.x==0 or v.x==140),"lateral site out of contested zone")
  assert(v.z==300 or v.z==470 or v.z==640,"site must lie along one of 3 routes")
  local id=tostring(v.x)..":"..tostring(v.z)
  assert(not used[id],"overlapping pickup")
  used[id]=true
  rows[v.z]=rows[v.z] or {}
  columns[v.x]=columns[v.x] or {}
  assert(not rows[v.z][v.kind],"unfair duplicate type in same route")
  assert(not columns[v.x][v.kind],"unfair duplicate type on same flank")
  rows[v.z][v.kind]=true
  columns[v.x][v.kind]=true
 end
 for _,group in pairs({rows,columns}) do
  for _,types in pairs(group) do
   assert(types.HEAL and types.DASH and types.SHIELD,"every lane/flank must offer three equal choices")
  end
 end
 return true
end
function RaidItems.start(session:any,origin:Vector3,authorItems:any):number
 assert(session and session.rules and session.rules.phase=="ACTIVE","cannot place items outside running game")
 assert(session.itemIntakeStarted~=true,"item intake must be exactly once per match")
 assert(session.mode=="TEAM" or session.mode=="BATTLE_ROYALE","unsupported mode")
 RaidItems.validate()
 local xCenter=if session.mode=="TEAM" then -620 else 620
 local points={}
 for _,site in ipairs(FIXED) do
  -- At top of existing walkable route; pickups remain within the 890x1050 floor.
  table.insert(points,origin+Vector3.new(xCenter+site.x,1.8,site.z))
 end
 -- Mark first, to prevent reentrant startup spawning a second item set.
 session.itemIntakeStarted=true
 local ok,err=pcall(function() authorItems.start(session,points) end)
 if not ok then
  -- Optional gameplay slice: remove any partial pickups before allowing a retry.
  local partial=session.world and session.world:FindFirstChild("EGGRUMBLE_FieldItems")
  if partial then partial:Destroy() end
  session.itemIntakeStarted=false
  error(err)
 end
 return #points
end
return RaidItems
