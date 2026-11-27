local now=100
local os={clock=function() return now end}
local function signal()
 local listeners={}
 return {
  Connect=function(_,fn)
   local bound={on=true,fn=fn}
   table.insert(listeners,bound)
   return {Disconnect=function() bound.on=false end}
  end,
  Fire=function(_,...)
   for _,bound in ipairs(listeners) do if bound.on then bound.fn(...) end end
  end,
 }
end
local created={}
local played={}
local function instance(class,name)
 local a={ClassName=class,Name=name or class,_attrs={},_signals={},HealthChanged=signal(),Died=signal(),IsPlaying=false}
 function a:IsA(wanted) return self.ClassName==wanted end
 function a:GetAttribute(key) return self._attrs[key] end
 function a:GetAttributeChangedSignal(key)
  self._signals[key]=self._signals[key] or signal()
  return self._signals[key]
 end
 function a:SetAttribute(key,value)
  if self._attrs[key]==value then return end
  self._attrs[key]=value
  self:GetAttributeChangedSignal(key):Fire()
 end
 function a:GetChildren()
  local all={}
  for _,item in ipairs(created) do if item.Parent==self then table.insert(all,item) end end
  return all
 end
 function a:FindFirstChild(child)
  for _,item in ipairs(self:GetChildren()) do if item.Name==child then return item end end
  return nil
 end
 function a:FindFirstChildOfClass(kind)
  for _,item in ipairs(self:GetChildren()) do if item.ClassName==kind then return item end end
  return nil
 end
 function a:WaitForChild(child) return self:FindFirstChild(child) end
 function a:Stop() self.IsPlaying=false end
 function a:Play()
  self.IsPlaying=true
  table.insert(played,{id=self.SoundId,voice=self,volume=self.Volume,speed=self.PlaybackSpeed})
 end
 function a:Destroy() self.Parent=nil end
 table.insert(created,a)
 return a
end
local Instance={new=instance}
local workspace=instance("Workspace")
local Players=instance("Players")
local player=instance("Player")
player.Parent=Players
Players.LocalPlayer=player
player.CharacterAdded=signal()
player.CharacterRemoving=signal()
player.AncestryChanged=signal()
local function avatar(rig)
 local char=instance("Model","Avatar")
 char.Parent=workspace
 local humanoid=instance("Humanoid")
 humanoid.Health=100
 humanoid.RigType=rig
 humanoid.Parent=char
 return char,humanoid
end
local function equip(id)
 local character=player.Character
 for _,child in ipairs(character:GetChildren()) do
  if child:IsA("Tool") then child.Parent=nil end
 end
 local tool=instance("Tool","Actual equipped tool")
 tool:SetAttribute("EGGRUMBLE_InternalToolId",id)
 tool.Parent=character
 return tool
end
player.Character=avatar("R6")
player:SetAttribute("EGGRUMBLE_Role","MAGE")
player:SetAttribute("EGGRUMBLE_GrowthActive",true)
player:SetAttribute("EGGRUMBLE_SkillCastSignature","MAGE:A:19")
local gui=instance("ScreenGui")
local soundService=instance("SoundService")
local RunService={IsStudio=function() return true end}
local game={GetService=function(_,name)
 if name=="Players" then return Players end
 if name=="SoundService" then return soundService end
 if name=="RunService" then return RunService end
 error(name)
end}
local Vector2={new=function(x,y) return {X=x,Y=y} end}
local UDim2={
 fromOffset=function(x,y) return {x=x,y=y,mode="offset"} end,
 fromScale=function(x,y) return {x=x,y=y,mode="scale"} end,
}
local Color3={fromRGB=function(r,g,b) return {r=r,g=g,b=b} end}
local tones={MAGE=Color3.fromRGB(97,212,255),WARRIOR=Color3.fromRGB(255,214,91)}
local Enum={EasingStyle={Quad="Quad"},EasingDirection={Out="Out"}}
local TweenInfo={new=function(t) return t end}
local tweens={}
local TweenService={Create=function(_,target,duration,goal)
 local tween={target=target,duration=duration,goal=goal,played=false,cancelled=false}
 function tween:Play() self.played=true end
 function tween:Cancel() self.cancelled=true end
 table.insert(tweens,tween)
 return tween
end}
local callbacks={}
local task={delay=function(delay,fn) table.insert(callbacks,{time=now+delay,fn=fn}) end}
local function advance(dt)
 now+=dt
 for i=#callbacks,1,-1 do
  if callbacks[i].time<=now then
   local row=table.remove(callbacks,i)
   row.fn()
  end
 end
end
