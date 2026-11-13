-- Child-friendly collection previews. ONLY inside a ViewportFrame WorldModel.
local Catalog=require(script.Parent.D18Batch10Catalog)
local Factory={}
local ACTIVE=setmetatable({},{__mode="k"})
local MAX_ACTIVE=12
local POSES={idle=true,tap=true,win=true,loss=true}
local function render(st)
 local pose=st.definition.pose_offsets[st.pose] or {}
 for _,slot in ipairs(st.parts) do
  local s=slot.spec; local off=pose[s.group] or {}
  slot.part.CFrame=st.origin*CFrame.Angles(0,math.rad(st.yaw),0)*CFrame.new(s.position[1],s.position[2],s.position[3])*CFrame.Angles(math.rad(s.rotation[1]),math.rad(s.rotation[2]),math.rad(s.rotation[3]))*CFrame.new(0,off.dy or 0,0)*CFrame.Angles(0,0,math.rad(off.rz or 0))
  slot.part.Transparency=(st.far and not s.far) and 1 or 0
 end
end
function Factory.Build(parent,id,origin)
 if typeof(parent)~="Instance" or not parent:IsA("WorldModel") then return nil,"VIEWPORT_ONLY" end
 if typeof(origin)~="CFrame" then return nil,"INVALID_ORIGIN" end
 local pos=origin.Position
 if pos.X~=pos.X or pos.Y~=pos.Y or pos.Z~=pos.Z or math.abs(pos.X)>10000 or math.abs(pos.Y)>10000 or math.abs(pos.Z)>10000 then return nil,"INVALID_ORIGIN" end
 local data=Catalog.get(id);if not data then return nil,"UNKNOWN_ID" end
 local n=0;for m,_ in pairs(ACTIVE) do if m.Parent then n+=1 else ACTIVE[m]=nil end end
 if n>=MAX_ACTIVE then return nil,"PREVIEW_LIMIT" end
 local m=Instance.new("Model");m.Name="D18Batch10_"..id;m:SetAttribute("P0DDisplayOnly",true)
 local st={origin=origin,definition=data,parts={},far=false,pose="idle",yaw=0}
 for _,spec in ipairs(data.parts) do
  local p=Instance.new("Part");p.Name=spec.name;p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false;p.CastShadow=false;p.Material=Enum.Material.SmoothPlastic
  p.Shape=Enum.PartType[spec.shape];p.Size=Vector3.new(spec.size[1],spec.size[2],spec.size[3]);local color=data.palette[spec.color];p.Color=Color3.fromRGB(color[1],color[2],color[3]);p:SetAttribute("P0DDisplayOnly",true);p.Parent=m
  table.insert(st.parts,{spec=spec,part=p})
 end
 ACTIVE[m]=st;m.Parent=parent;render(st);return m,nil
end
function Factory.SetPose(m,pose) local s=ACTIVE[m];if not s or not POSES[pose] then return false end s.pose=pose;render(s);return true end
function Factory.SetLod(m,far) local s=ACTIVE[m];if not s or type(far)~="boolean" then return false end s.far=far;render(s);return true end
function Factory.SetYaw(m,yaw) local s=ACTIVE[m];if not s or type(yaw)~="number" or yaw~=yaw or yaw<0 or yaw>=360 or yaw%45~=0 then return false end s.yaw=yaw;render(s);return true end
function Factory.Destroy(m) if not ACTIVE[m] then return false end ACTIVE[m]=nil;m:Destroy();return true end
return Factory
