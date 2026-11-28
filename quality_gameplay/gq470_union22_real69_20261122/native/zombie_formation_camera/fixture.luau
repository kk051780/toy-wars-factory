-- Native API doubles; the complete selected production client is appended below.
local t=100
local os={clock=function() return t end}
local function signal()
 local subscriptions={}
 return {
  Connect=function(_,cb)
   local sub={cb=cb,live=true}
   table.insert(subscriptions,sub)
   return {Disconnect=function() sub.live=false end}
  end,
  Fire=function(_,...)
   for _,sub in ipairs(table.clone(subscriptions)) do
    if sub.live then sub.cb(...) end
   end
  end,
 }
end
local queued={}
local task={delay=function(seconds,callback)
 table.insert(queued,{at=t+seconds,callback=callback})
end}
local function advance(delta)
 local untilAt=t+delta
 while true do
  table.sort(queued,function(a,b) return a.at<b.at end)
  local nextCall=queued[1]
  if not nextCall or nextCall.at>untilAt then break end
  table.remove(queued,1)
  t=math.max(t,nextCall.at)
  nextCall.callback()
 end
 t=untilAt
end
local Enum={CameraType={Custom="CUSTOM",Scriptable="SCRIPTABLE",Fixed="FIXED"}}
local workspace={cameraChanged=signal()}
function workspace:GetPropertyChangedSignal(name)
 assert(name=="CurrentCamera")
 return self.cameraChanged
end
local function selectCamera(camera)
 workspace.CurrentCamera=camera
 workspace.cameraChanged:Fire()
end
local function camera(kind,subject)
 return setmetatable({CameraType=kind,_subject=subject,writes=0},{
  __index=function(self,key)
   if key=="CameraSubject" then return self._subject end
  end,
  __newindex=function(self,key,value)
   assert(key=="CameraSubject","unexpected camera property write: "..key)
   self.writes+=1
   rawset(self,"_subject",value)
  end,
 })
end
local Players={PlayerAdded=signal(),PlayerRemoving=signal()}
local RunService={IsStudio=function() return true end,PreSimulation=signal()}
local game={GetService=function(_,name)
 if name=="Players" then return Players end
 if name=="RunService" then return RunService end
 error("unexpected service "..name)
end}
local function makePlayer(id)
 local p={UserId=id,Parent=Players,attrs={},attributeSignals={},CharacterAdded=signal(),
  CharacterRemoving=signal(),AncestryChanged=signal()}
 function p:GetAttribute(name) return self.attrs[name] end
 function p:SetAttribute(name,value)
  if self.attrs[name]==value then return end
  self.attrs[name]=value;self:GetAttributeChangedSignal(name):Fire()
 end
 function p:GetAttributeChangedSignal(name)
  self.attributeSignals[name]=self.attributeSignals[name] or signal()
  return self.attributeSignals[name]
 end
 return p
end
local player=makePlayer(42)
local peer=makePlayer(43)
Players.LocalPlayer=player
function Players:GetPlayers() return {player,peer} end
local function subject(kind,parent,health)
 return {IsA=function(_,class) return kind==class end,Parent=parent,Health=health}
end
local function character(health)
 local props={}
 local c={Parent=workspace,children={}}
 function c:GetAttribute(name) return props[name] end
 function c:SetAttribute(name,value) props[name]=value end
 function c:GetChildren() return self.children end
 function c:FindFirstChildOfClass(kind)
  for _,item in ipairs(self.children) do
   if item.Parent==self and item:IsA(kind) then return item end
  end
  return nil
 end
 function c:FindFirstChild() return nil end
 local h=subject("Humanoid",c,health)
 if health then table.insert(c.children,h) end
 return c,h
end
local function remove(p)
 if not p.Character then return end
 local previous=p.Character
 p.CharacterRemoving:Fire(previous)
 p.Character=nil
end
local function spawn(p,newCharacter)
 remove(p)
 p.Character=newCharacter
 p.CharacterAdded:Fire(newCharacter)
end
