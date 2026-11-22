-- Native service and seat fixtures for full, unchanged Realm execution.
-- No live Roblox physics, networking, streaming or Studio evidence.
local NumberRange={new=function(low,high)return {Min=low,Max=high or low}end}
local ReplicatedStorage=Instance.new('ReplicatedStorage')
local preRealmService=game.GetService
game.GetService=function(self,name)
 if name=='ReplicatedStorage'then return ReplicatedStorage end
 return preRealmService(self,name)
end
workspace._props.ChildAdded=workspace._props.ChildAdded or signal()
workspace._props.ChildRemoved=workspace._props.ChildRemoved or signal()
allowedNil.Occupant=true
local preRealmIsA=methods.IsA
function methods:IsA(class)
 return preRealmIsA(self,class)or class=='BasePart'and self.ClassName=='VehicleSeat'
end
local preRealmNew=Instance.new
Instance.new=function(class)
 local item=preRealmNew(class)
 item._props.AncestryChanged=signal();item._props.OnServerEvent=signal()
 item._props.Sit=false;item._props.ThrottleFloat=0;item._props.SteerFloat=0
 return item
end
function methods:Sit(h)
 self.Occupant=h;h.SeatPart=self;h.Sit=true
end
frameMeta.__index=function(_frame,key)
 if key=='Rotation'then return CFrame.Angles(0,0,0)end
 return nil
end
workspace.Blockcast=function(_self,_frame,_size,_direction,params)
 assert(params.RespectCanCollide==true,'actual Realm flight requests collision-respecting cast')
 -- All flight cases remain over open sky. This is a bounded no-collision fixture.
 return nil
end

