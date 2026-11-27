local function gather(want)
 local models={}
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local horde=s.world:FindFirstChild("NeutralHorde")
 for _=1,900 do
  rootPart.CFrame=CFrame.new(floor.Position+Vector3.new(180,floor.Size.Y*.5+3,80))
  advanceTo(now+.2)
  assert(s.rules.phase=="ACTIVE","round ended before obtaining real NPCs")
  table.clear(models)
  for _,m in horde:GetChildren() do
   local h=m:FindFirstChildOfClass("Humanoid")
   if h and h.Health>0 and m.PrimaryPart then table.insert(models,m) end
  end
  if #models>=want then return models end
 end
 error("insufficient NPCs "..#models)
end

local models=gather(population)
local seen={}
local before={}
for i=1,population do
 local id=models[i]:GetAttribute("EGGRUMBLE_NeutralInstanceId")
 assert(id and not seen[id])
 seen[id]=true
 local nominal=i<=originalCount
 local f=if nominal then 14.1+i*.002 else 5.89+i*.002
 place(models[i],f,((i%5)-2)*.12,if nominal then 5.5 else -.4)
 before[i]=models[i]:FindFirstChildOfClass("Humanoid").Health
end
rootPart.CFrame=CFrame.new(origin,origin+aim*math.cos(math.rad(30))+Vector3.new(0,.5,0))
local wall
if obstructed then
 wall=Instance.new("Part")
 wall.Name="NominalOnlyCollider"
 wall.Anchored=true
 wall.CanCollide=true
 wall.Size=Vector3.new(4,8,4)
 wall.CFrame=CFrame.new(origin+aim*10+Vector3.new(0,4,0))
 wall.Parent=workspace
end
local start=#queryTrace
fire(true)
local legacyHits,approachHits=0,0
for i=1,population do
 local delta=before[i]-models[i]:FindFirstChildOfClass("Humanoid").Health
 assert(delta==0 or delta==9,"unexpected amount "..delta)
 if delta>0 then
  if i<=originalCount then legacyHits+=1 else approachHits+=1 end
 end
end
local legacyRays,approachRays=0,0
local ordered=true
for i=start+1,#queryTrace do
 local q=queryTrace[i]
 local d=q.delta
 local horizontal=d.X*aim.X+d.Z*aim.Z
 if (q.origin-(origin+Vector3.new(0,1,0))).Magnitude<1e-5 then
  if math.abs(d.Y-5.5)<1e-5 and horizontal>=14.09 and horizontal<14.23 then
   legacyRays+=1
   if approachRays>0 then ordered=false end
   if obstructed then assert(q.hit==wall) end
  elseif math.abs(d.Y+.4)<1e-5 and horizontal>5.88 and horizontal<6.05 then
   approachRays+=1
   assert(q.hit==nil,"approach unexpectedly blocked")
  end
 end
end
assert(legacyRays+approachRays>0 and legacyRays+approachRays<=48)
local expectedOriginal=if obstructed then 0 else math.min(originalCount,24)
local expectedNew=if patched then math.min(population-originalCount,24-expectedOriginal,48-originalCount) else 0
local expectedOldRays=if obstructed then math.min(originalCount,48) else expectedOriginal
if preserves then
 assert(ordered and legacyHits==expectedOriginal and approachHits==expectedNew,"target priority/cap")
 assert(legacyRays==expectedOldRays and approachRays==expectedNew,"ray priority/cap")
elseif obstructed then
 assert(legacyRays==48-(population-originalCount) and approachRays==population-originalCount)
 assert(approachHits==population-originalCount and legacyHits==0 and not ordered)
else
 assert(legacyHits==24-(population-originalCount) and approachHits==population-originalCount and not ordered)
end
print("PRIORITY",population,originalCount,obstructed,legacyHits,approachHits,legacyRays,approachRays,ordered)
