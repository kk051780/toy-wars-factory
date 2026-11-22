-- Native engine boundaries for the bounded full Host + Guardian + Swarm path.
-- No game policy, membership, HP gate, spawn policy or winner function is stubbed here.
-- The original prefix created its floor/avatar before the engine default-property
-- wrapper was installed. Fill the missing BasePart CanQuery default for those
-- fixture objects too; no gameplay object/property is rewritten here.
for _,existing in ipairs(workspace:GetDescendants())do
 if existing:IsA('BasePart')and rawget(existing._props,'CanQuery')==nil then
  existing._props.CanQuery=true
 end
end
local fullSourceRanges={}
local function sourceLabel(line)
 for name,range in pairs(fullSourceRanges) do
  if line>=range.first and line<=range.last then return name end
 end
 return 'fixture'
end

local oldVectorNew=Vector3.new
Vector3.new=function(x,y,z)return oldVectorNew(x or 0,y or 0,z or 0)end
vectorMeta.__unm=function(v)return Vector3.new(-v.X,-v.Y,-v.Z)end
CFrame.lookAt=function(at,towards)return CFrame.new(at,towards)end
local TweenInfo={new=function(seconds,style,direction)return {Time=seconds,Style=style,Direction=direction}end}
local TweenService={Create=function(_self,object,_info,properties)
 -- Cosmetic tween properties are committed immediately; no rendering proof.
 return {Play=function()for key,value in pairs(properties)do object[key]=value end end}
end}
local beforeCombinedService=game.GetService
game.GetService=function(self,name)
 if name=='TweenService' then return TweenService end
 return beforeCombinedService(self,name)
end
local beforeCombinedInstance=Instance.new
Instance.new=function(class)
 local object=beforeCombinedInstance(class)
 object._props.HealthChanged=signal()
 return object
end
humanoid._props.HealthChanged=signal();secondHumanoid._props.HealthChanged=signal()
local healthWrites={}
local oldCombinedWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 local before=self._props[key]
 oldCombinedWrite(self,key,value)
 if key=='Health' and before~=value and self:IsA('Humanoid') then
  local _source,line=debug.info(2,'sl')
  table.insert(healthWrites,{humanoid=self,before=before,after=value,at=now,line=line})
  if self._props.HealthChanged then self._props.HealthChanged:Fire(value)end
 end
end
function methods:GetPivot()
 local root=self.PrimaryPart or self:FindFirstChild('HumanoidRootPart')
 assert(root,'fixture GetPivot requires actual model root')
 return root.CFrame
end
function methods:PivotTo(frame)
 local root=self.PrimaryPart or self:FindFirstChild('HumanoidRootPart')
 assert(root,'fixture PivotTo requires actual model root')
 local delta=frame.Position-root.Position
 for _,part in ipairs(self:GetDescendants())do
  if part:IsA('BasePart')then part.Position=part.Position+delta end
 end
 root.CFrame=frame
end
local oldCombinedDestroy=methods.Destroy
function methods:Destroy()
 oldCombinedDestroy(self)
 for _,value in pairs(self._props)do
  if type(value)=='table' and type(rawget(value,'DisconnectAll'))=='function' then value:DisconnectAll()end
 end
end
Debris.AddItem=function(_self,object,seconds)
 task.delay(seconds,function()if object.Parent then object:Destroy()end end)
end
dependencies.EGGRUMBLE_ImpactFeedback.ko=function()end -- unrelated cosmetic feedback

-- Axis-aligned current-Part queries only. Cosmetic CFrame rotations inherited
-- from the original Host fixture are approximate; no terrain/rigid-body claim.
local function queryExcluded(part,params)
 for _,object in ipairs(params.FilterDescendantsInstances or {})do
  if part==object or part:IsDescendantOf(object)then return true end
 end
 return false
end
local function queryEligible(part,params)
 if not part:IsA('BasePart') or queryExcluded(part,params)then return false end
 return if params.RespectCanCollide then part.CanCollide==true else part.CanQuery~=false
end
local rayQueries=0;local overlapQueries=0;local queryTrace={}
workspace.Raycast=function(_self,origin,delta,params)
 rayQueries+=1
 local callerLine=debug.info(2,'l')
 local best=nil;local nearest=math.huge;local normal=nil
 for _,part in ipairs(workspace:GetDescendants())do
  if queryEligible(part,params)then
   local lo=part.Position-part.Size*.5;local hi=part.Position+part.Size*.5
   local entry=0;local exit=1;local hitNormal=Vector3.new();local accepted=true
   for _,axis in ipairs({'X','Y','Z'})do
    local start=origin[axis];local direction=delta[axis]
    if math.abs(direction)<1e-10 then
     if start<lo[axis] or start>hi[axis]then accepted=false;break end
    else
     local a=(lo[axis]-start)/direction;local b=(hi[axis]-start)/direction
     local sign=-1
     if a>b then a,b=b,a;sign=1 end
     if a>entry then
      entry=a
      hitNormal=if axis=='X' then Vector3.new(sign,0,0)
       elseif axis=='Y' then Vector3.new(0,sign,0)else Vector3.new(0,0,sign)
     end
     exit=math.min(exit,b)
     if entry>exit then accepted=false;break end
    end
   end
   if accepted and entry>=0 and entry<=1 and entry<nearest then
    nearest=entry;best=part;normal=hitNormal
   end
  end
 end
 table.insert(queryTrace,{line=callerLine,source=sourceLabel(callerLine),origin=origin,delta=delta,hit=best,respectCanCollide=params.RespectCanCollide,at=now})
 if not best then return nil end
 return {Instance=best,Position=origin+delta*nearest,Distance=delta.Magnitude*nearest,Normal=normal}
end
workspace.GetPartBoundsInBox=function(_self,frame,size,params)
 overlapQueries+=1
 local found={};local center=frame.Position;local half=size*.5
 for _,part in ipairs(workspace:GetDescendants())do
  if queryEligible(part,params)then
   local distance=part.Position-center;local extent=part.Size*.5+half
   if math.abs(distance.X)<extent.X and math.abs(distance.Y)<extent.Y and math.abs(distance.Z)<extent.Z then
    table.insert(found,part)
   end
  end
 end
 return found
end

local moduleRequires={}
local beforeCombinedRequire=require
require=function(name)
 local result=beforeCombinedRequire(name)
 table.insert(moduleRequires,{caller=loadingModule,name=name,value=result})
 return result
end

-- Only observe the original engine registration boundary. Every function is
-- forwarded unchanged; the ordinary fixture scheduler still runs its body.
local currentSwarmRegistration=nil
local swarmTasks={}
local previousSpawn=task.spawn
task.spawn=function(fn,...)
 local thread=if type(fn)=='thread' then fn else coroutine.create(fn)
 if currentSwarmRegistration and type(fn)=='function'then
  local line=debug.info(fn,'l')
  if sourceLabel(line)=='SwarmCombat'then
   table.insert(swarmTasks,{session=currentSwarmRegistration,thread=thread,line=line,at=now})
  end
 end
 previousSpawn(thread,...)
 return thread
end
local publishedWrites={}
local beforeCombinedAttribute=methods.SetAttribute
function methods:SetAttribute(name,value)
 if (self==player or self==second)and
  (name=='EGGRUMBLE_NeutralKOs'or name=='EGGRUMBLE_Combo'or name=='EGGRUMBLE_BestCombo'
   or name:match('^EGGRUMBLE_Musou'))then
  local _source,line=debug.info(2,'sl')
  table.insert(publishedWrites,{player=self,name=name,value=value,at=now,line=line})
 end
 return beforeCombinedAttribute(self,name,value)
end

local guardianAttachments={};local guardianCalls={};local guardianShutdowns={}
local guardianDamageFilters={}
local swarmAttachments={}
local function installApiObservers()
 local invulModule=dependencies.EGGRUMBLE_InvulRuntime
 local originalFilter=invulModule.filterDamage
 invulModule.filterDamage=function(victim,damage,kind,attacker)
  local filtered=originalFilter(victim,damage,kind,attacker)
  if attacker=='GUARDIAN_ATTACK'then
   table.insert(guardianDamageFilters,{victim=victim,damage=damage,kind=kind,attacker=attacker,
    filtered=filtered,at=now})
  end
  return filtered
 end
 local guardianModule=dependencies.EGGRUMBLE_CastleGuardianRuntime
 local originalAttach=guardianModule.attach
 guardianModule.attach=function(session,roles)
  local controller=originalAttach(session,roles)
  table.insert(capturedSessions,session)
  table.insert(guardianAttachments,{session=session,controller=controller,module=guardianModule})
  local originalHit=controller.damageFromPlayer
  controller.damageFromPlayer=function(p,at,radius,damage,shape,attackRoot,attackCharacter)
   local result=originalHit(p,at,radius,damage,shape,attackRoot,attackCharacter)
   table.insert(guardianCalls,{session=session,controller=controller,player=p,root=attackRoot,
    character=attackCharacter,shape=shape,result=result,at=now})
   return result
  end
  local originalShutdown=controller.shutdown
  controller.shutdown=function(...)
   table.insert(guardianShutdowns,{session=session,at=now})
   return originalShutdown(...)
  end
  return controller
 end
 local swarmModule=dependencies.EGGRUMBLE_SwarmCombat
 local originalStart=swarmModule.start
 swarmModule.start=function(session)
  local previous=currentSwarmRegistration;currentSwarmRegistration=session
  local api=originalStart(session)
  currentSwarmRegistration=previous
  table.insert(swarmAttachments,{session=session,api=api,module=swarmModule})
  return api
 end
end
