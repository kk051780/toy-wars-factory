-- Native-only API fixtures. This is not Roblox physics/network/Studio evidence.
local now = 100
local os = { clock = function() return now end }
local signalCount = 0
local function signal()
 local callbacks = {}
 return {
  Connect=function(self, fn)
   signalCount += 1
   local entry={fn=fn,connected=true};table.insert(callbacks,entry)
   return {Disconnect=function() entry.connected=false end}
  end,
  Fire=function(self,...)
   for _,entry in ipairs(table.clone(callbacks)) do
    if entry.connected then entry.fn(...) end
   end
  end,
  DisconnectAll=function(self)
   for _,entry in ipairs(callbacks) do entry.connected=false end
  end,
 }
end
local vectorMethods = {}
local vectorMeta = {}
local Vector3 = {}
function Vector3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vectorMeta) end
vectorMeta.__index=function(v,key)
 if key=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 if key=="Unit" then local m=v.Magnitude;return Vector3.new(v.X/m,v.Y/m,v.Z/m) end
 return vectorMethods[key]
end
vectorMeta.__add=function(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
vectorMeta.__sub=function(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
vectorMeta.__mul=function(a,b)
 if type(a)=="number" then return Vector3.new(a*b.X,a*b.Y,a*b.Z) end
 return Vector3.new(a.X*b,a.Y*b,a.Z*b)
end
vectorMeta.__div=function(a,b) return Vector3.new(a.X/b,a.Y/b,a.Z/b) end
function vectorMethods:Dot(other) return self.X*other.X+self.Y*other.Y+self.Z*other.Z end
local CFrame={}
function CFrame.new(a,b,c)
 local p=if type(a)=="number" then Vector3.new(a,b,c) else (a or Vector3.new(0,0,0))
 local look=if type(b)=="table" then (b-p).Unit else Vector3.new(0,0,-1)
 return {Position=p,LookVector=look,RightVector=Vector3.new(-look.Z,0,look.X)}
end
local Color3={fromRGB=function(r,g,b) return {R=r/255,G=g/255,B=b/255} end}
local Enum=setmetatable({}, {__index=function(t,k)
 local value=setmetatable({}, {__index=function(s,v) rawset(s,v,k.."."..v);return rawget(s,v) end})
 rawset(t,k,value);return value
end})
local RaycastParams={new=function() return {} end}
local OverlapParams={new=function() return {} end}
local methods={}
local Instance={}
local allowedNil={Parent=true,Character=true,PrimaryPart=true,SeatPart=true,Part0=true,Part1=true,ToolTip=true}
local instanceMeta={}
instanceMeta.__index=function(self,key)
 if methods[key] then return methods[key] end
 local value=self._props[key]
 if value~=nil or allowedNil[key] then return value end
 for _,child in ipairs(self._children) do if child.Name==key then return child end end
 error("Invalid member "..tostring(key).." of "..self.ClassName.." "..self.Name)
end
instanceMeta.__newindex=function(self,key,value)
 if key=="Parent" then
  local old=self._props.Parent
  if old then
   for i,c in ipairs(old._children) do if c==self then table.remove(old._children,i);break end end
  end
  self._props.Parent=value
  if value then table.insert(value._children,self) end
 else
  self._props[key]=value
  if key=="CFrame" then self._props.Position=value.Position end
 end
end
function Instance.new(class)
 return setmetatable({_props={ClassName=class,Name=class,Activated=signal(),Destroying=signal(),
  CanCollide=false,Anchored=false,Health=100,MaxHealth=100,FloorMaterial=Enum.Material.Concrete,
  Position=Vector3.new(0,0,0),CFrame=CFrame.new(0,0,0),Size=Vector3.new(1,1,1)},_children={},_attributes={}},instanceMeta)
end
function methods:IsA(class)
 return self.ClassName==class or class=="Instance"
  or class=="BasePart" and (self.ClassName=="Part" or self.ClassName=="WedgePart")
end
function methods:GetChildren() return table.clone(self._children) end
function methods:FindFirstChild(name)
 for _,child in ipairs(self._children) do if child.Name==name then return child end end
 return nil
end
function methods:FindFirstChildOfClass(class)
 for _,child in ipairs(self._children) do if child:IsA(class) then return child end end
 return nil
end
function methods:WaitForChild(name) return self:FindFirstChild(name) end
function methods:GetAttribute(name) return self._attributes[name] end
function methods:SetAttribute(name,value) self._attributes[name]=value end
function methods:IsDescendantOf(parent)
 local p=self.Parent
 while p do if p==parent then return true end;p=p.Parent end
 return false
end
function methods:PivotTo(frame)
 local root=self:FindFirstChild("HumanoidRootPart")
 assert(root,"fixture model root missing")
 root.CFrame=frame
end
function methods:Destroy()
 self.Destroying:Fire()
 self.Activated:DisconnectAll()
 for _,child in ipairs(self:GetChildren()) do child:Destroy() end
 self.Parent=nil
end
local geometry={rayCalls=0,boundsCalls=0,wallDistance=nil,noGround=false,groundHeight=0,overlap=false,groundCollidable=true}
local workspace=Instance.new("Workspace")
local ground=Instance.new("Part");ground.Name="FixtureFloor";ground.CanCollide=true;ground.Parent=workspace
workspace.Raycast=function(self,origin,direction,params)
 geometry.rayCalls+=1
 assert(params.RespectCanCollide==true and #params.FilterDescendantsInstances==1,"collision query context")
 if direction.Y<0 then
  if geometry.noGround then return nil end
  ground.CanCollide=geometry.groundCollidable
  return {Instance=ground,Position=Vector3.new(origin.X,geometry.groundHeight,origin.Z),Distance=origin.Y-geometry.groundHeight}
 end
 if geometry.wallDistance then return {Instance=ground,Distance=geometry.wallDistance,Position=origin+direction.Unit*geometry.wallDistance} end
 return nil
end
workspace.GetPartBoundsInBox=function(self,frame,size,params)
 geometry.boundsCalls+=1
 assert(params.RespectCanCollide==true and #params.FilterDescendantsInstances==1,"overlap query context")
 return if geometry.overlap then {ground} else {}
end
local currentPlayers={}
local RunService={IsStudio=function() return true end,IsServer=function() return true end,Heartbeat=signal()}
local Players={GetPlayers=function() return currentPlayers end}
local Debris={AddItem=function() end}
local game={GetService=function(self,name)
 if name=="RunService" then return RunService elseif name=="Players" then return Players elseif name=="Debris" then return Debris end
 error("unhandled service "..name)
end}
local task={delay=function() end,spawn=function() end,wait=function() error("unexpected task wait in Dodge fixture") end}
local script={Parent={WaitForChild=function(self,name) return name end}}
local dependencies={}
local require=function(name)
 assert(dependencies[name],"unhandled dependency "..tostring(name))
 return dependencies[name]
end
local noop=function() end
dependencies.EGGRUMBLE_InvulRuntime={filterDamage=function(h,n) return n end}
dependencies.EGGRUMBLE_FieldItemPickups={weaponDamageMultiplier=function() return 1 end,weaponReachBonus=function() return 0 end}
dependencies.EGGRUMBLE_SkillFX={emit=noop}
dependencies.EGGRUMBLE_ImpactFeedback={attacker=noop,hit=noop,clear=noop}
dependencies.EGGRUMBLE_WeaponSilhouettes={attach=noop,clear=noop}
dependencies.EGGRUMBLE_DivineMantle={cancel=noop}
dependencies.EGGRUMBLE_AttackGeometry={allowed=function() return false end}
dependencies.EGGRUMBLE_StatusTickFence={}
