local count=oldCount+extraCount
local floor=s.world:FindFirstChild('TacticalBattlefield')
local horde=s.world:FindFirstChild('NeutralHorde')
local models={}
for _=1,700 do
 rootPart.CFrame=CFrame.new(floor.Position+Vector3.new(180,floor.Size.Y*.5+3,80))
 advanceTo(now+.2);table.clear(models)
 for _,m in horde:GetChildren() do
  local h=m:FindFirstChildOfClass('Humanoid')
  if h and h.Health>0 and m.PrimaryPart then table.insert(models,m) end
 end
 if #models>=count then break end
end
assert(#models>=count and s.rules.phase=='ACTIVE')
local wall
if blocked then
 wall=Instance.new('Part');wall.Name='BudgetTestObstacle';wall.CanCollide=true;wall.Anchored=true
 wall.Size=Vector3.new(4,8,4);wall.CFrame=CFrame.new(origin+aim*10+Vector3.new(0,4,0));wall.Parent=workspace
end
local function cast(includeExtras)
 local before,ids={},{}
 for i,m in models do
  local f=if i<=oldCount then 14.1 elseif i<=count and includeExtras then 5.95 else 75
  local y=if i<=oldCount then 5+i*.0125 else -.40-(i-oldCount)*.02
  place(m,f,0,y)
  if i<=count then
   local ident=m:GetAttribute('EGGRUMBLE_NeutralInstanceId');assert(ident and not ids[ident]);ids[ident]=true
   before[i]=m:FindFirstChildOfClass('Humanoid').Health
  end
 end
 rootPart.CFrame=CFrame.new(origin,origin+aim*math.cos(math.rad(30))+Vector3.new(0,.5,0))
 local q0=#queryTrace;fire(true)
 local oldRays,oldHits={},{};local addedRays,addedHits=0,0;local nextClass=false;local legacyFirst=true
 for j=q0+1,#queryTrace do
  local q=queryTrace[j];local at=q.origin;local dx=q.delta.X*aim.X+q.delta.Z*aim.Z
  if (at-(origin+Vector3.new(0,1,0))).Magnitude<.00001 then
   if math.abs(dx-14.1)<.00001 then
    local ix=math.round((q.delta.Y-5)/.0125);assert(ix>=1 and ix<=oldCount)
    assert(q.hit==wall);oldRays[#oldRays+1]=models[ix]:GetAttribute('EGGRUMBLE_NeutralInstanceId')
    if nextClass then legacyFirst=false end
   elseif math.abs(dx-5.95)<.00001 then
    assert(q.hit==nil);addedRays+=1;nextClass=true
   end
  end
 end
 for i=1,count do
  local delta=before[i]-models[i]:FindFirstChildOfClass('Humanoid').Health
  assert(delta==0 or delta==9)
  if delta==9 then
   if i<=oldCount then table.insert(oldHits,models[i]:GetAttribute('EGGRUMBLE_NeutralInstanceId')) else addedHits+=1 end
  end
 end
 table.sort(oldHits)
 return {oldRays=oldRays,addedRays=addedRays,oldHits=oldHits,addedHits=addedHits,legacyFirst=legacyFirst}
end
local empty=cast(false);rest(.552);local loaded=cast(true)
assert(#empty.oldRays==math.min(oldCount,if blocked then 48 else 24) and empty.addedRays==0)
assert(#empty.oldHits==(if blocked then 0 else math.min(24,oldCount)))
local sameRay=table.concat(empty.oldRays,',')==table.concat(loaded.oldRays,',')
local sameHit=table.concat(empty.oldHits,',')==table.concat(loaded.oldHits,',')
if variant~='V2' then
 local expected=if variant=='V3' then math.min(extraCount,24-#empty.oldHits,48-#empty.oldRays) else 0
 assert(sameRay and sameHit and loaded.legacyFirst,'legacy ID choice or ray order changed after adding approach targets')
 assert(loaded.addedRays==expected and loaded.addedHits==expected,'unused budget incorrect')
else
 assert(loaded.addedHits==extraCount and not loaded.legacyFirst,'control lost the expected repro')
end
print('TIE',oldCount,extraCount,blocked,#loaded.oldHits,loaded.addedHits,#loaded.oldRays,loaded.addedRays,sameRay,sameHit,loaded.legacyFirst)
