do
local FOLDER="EGGRUMBLE_PlayerContactShadow_Local"
local NAME="MatteAvatarContactDisc"
local OFF="EGGRUMBLE_PlayerContactShadowOff"
local REDUCED="EGGRUMBLE_ReducedEffects"

local function mount(touch)
 local s=ready("CONTACT_SHADOW_REAL_TEAM")
 humanoid._props.AncestryChanged=humanoid._props.AncestryChanged or signal()
 local field=s.world:FindFirstChild("TacticalBattlefield")
 local at=field.Position+Vector3.new(12,field.Size.Y*.5+3,11)
 rootPart.CFrame=CFrame.new(at)
 local head=Instance.new("Part")
 head.Name="Head";head.CFrame=CFrame.new(at+Vector3.new(0,2,0))
 head._props.Transparency=0;head._props.LocalTransparencyModifier=0
 head.Parent=character
 local surface=Instance.new("Part")
 surface.Name="DryTestSurface";surface.CanCollide=true;surface.Anchored=true
 surface._props.Transparency=0;surface._props.LocalTransparencyModifier=0
 surface.Parent=s.world
 local camera=Instance.new("Camera")
 camera.CFrame=CFrame.new(at+Vector3.new(0,4,8))
 camera.CameraType=Enum.CameraType.Custom;camera._props.CameraSubject=humanoid
 workspace.CurrentCamera=camera
 workspace._props.DescendantRemoving=signal()
 Players.LocalPlayer=player
 local service=game.GetService
 game.GetService=function(self,name)
  if name=="UserInputService" then
   return {TouchEnabled=touch,WindowFocusReleased=signal(),WindowFocused=signal()}
  end
  return service(self,name)
 end
 function vectorMethods:Cross(v)
  return Vector3.new(self.Y*v.Z-self.Z*v.Y,self.Z*v.X-self.X*v.Z,self.X*v.Y-self.Y*v.X)
 end
 function CFrame.fromMatrix(pos,x,y)
  local frame=CFrame.new(pos)
  frame.XVector=x;frame.YVector=y
  return frame
 end
 local originalState=methods.GetState
 local state={result=surface,normal=Vector3.new(0,1,0),material=Enum.Material.Grass,
  hitAt=at-Vector3.new(0,3,0),rayTimes={}}
 function methods:GetState()
  if self==humanoid and state.humanoidState then return state.humanoidState end
  return originalState(self)
 end
 local originalRay=workspace.Raycast
 workspace.Raycast=function(self,origin,direction,params)
  local filtered=params.FilterDescendantsInstances
  local folder=filtered[2]
  if folder and folder.Name==FOLDER then
   check(filtered[1]==player.Character and #filtered==2 and params.IgnoreWater==false
    and params.RespectCanCollide==true and params.FilterType==Enum.RaycastFilterType.Exclude,
    "only own avatar and visual folder excluded from dry visible floor ray")
   check((origin-player.Character.PrimaryPart.Position-Vector3.new(0,.35,0)).Magnitude<.001
    and (direction-Vector3.new(0,-7.5,0)).Magnitude<.001,"only one original down ray from exact own foot position")
   table.insert(state.rayTimes,now)
   return if state.result then {Instance=state.result,Position=state.hitAt,Normal=state.normal,Material=state.material} else nil
  end
  return originalRay(self,origin,direction,params)
 end
 local script=Instance.new("LocalScript")
 script.Name="NativeMountedShadowLOD";script.Parent=playerGui
 local client=script
 local contains=methods.IsDescendantOf
 function methods:IsDescendantOf(parent)
  if self==client and parent==game then return self.Parent~=nil end
  return contains(self,parent)
 end
 local launch=function()
-- INSERT_PHYSICAL_ART_LOD
 end
 launch()
 return state,s,head,surface,camera,client,at,launch
end

local function tick(v)
 advanceTo(now+(v or .19))
 drainDeferred()
end

local function circle()
 local folder=workspace:FindFirstChild(FOLDER)
 return folder and folder:FindFirstChild(NAME)
end

local function assertPlate(state)
 local folder=workspace:FindFirstChild(FOLDER)
 local part=folder and circle()
 check(part and #folder:GetChildren()==1,"one local physical visual in own folder")
 check(part:IsA("Part") and part.Shape==Enum.PartType.Cylinder and part.Material==Enum.Material.SmoothPlastic
  and part.Anchored and not part.CanCollide and not part.CanQuery and not part.CanTouch and not part.CastShadow,
  "author matte flat cylinder has no collision, touch, ray authority or cast")
 check(part.Color.R==24/255 and part.Color.G==34/255 and part.Color.B==45/255 and part.Size.X==.05
  and part.Reflectance==0,"original authored size and palette")
 check((part.CFrame.Position-(state.hitAt+state.normal*.045)).Magnitude<.001
  and (part.CFrame.XVector-state.normal).Magnitude<.001,
  "author cylinder local X remains aligned to floor normal and .045 clearance")
 return part
end

local function exerciseBudget(touch,cap,interval)
 local state,_,_,_,cam,_,at=mount(touch)
 tick(.025)
 local part=assertPlate(state)
 equal(part.Transparency,.76,"original near transparency")
 local originalCount=#state.rayTimes
 tick(.66)
 check(#state.rayTimes>=originalCount+4,"bounded real sample loop stays live")
 for i=2,#state.rayTimes do
  check(math.abs(state.rayTimes[i]-state.rayTimes[i-1]-interval)<.00001,"fixed authored polling rate")
 end
 cam.CFrame=CFrame.new(at+Vector3.new(cap*.86,0,0));tick()
 check(circle()==part and math.abs(part.Transparency-.88)<.00001,"same disc eases through last 28%")
 cam.CFrame=CFrame.new(at+Vector3.new(cap+.01,0,0));tick()
 check(not circle(),"beyond authored cap owns zero parts")
end

function growthCases.shadow1001_desktop()
 exerciseBudget(false,75,.10)
 return "author desktop 75 studs and 0.10s; one reusable matte disc, exact fade"
end

function growthCases.shadow1001_touch()
 exerciseBudget(true,55,.16)
 return "author Touch 55 studs and 0.16s; one reusable matte disc, exact fade"
end

function growthCases.shadow1001_floor_safety()
 local state,s,_,support=mount(true)
 tick();local part=assertPlate(state)
 state.normal=Vector3.new(.6,.8,0)
 tick();check(assertPlate(state)==part,"normal slope updates same owned independent physical disc")
 state.normal=Vector3.new(0,.77,math.sqrt(1-.77*.77))
 tick();check(not circle(),"too steep")
 state.normal=Vector3.new(0,1,0)
 support.Transparency=.75;tick();check(not circle(),"invisible collidable geom rejected")
 support.Transparency=.24;support.LocalTransparencyModifier=.4
 tick();check(not circle(),"combined client and server transparency filters hollow appearance")
 support.Transparency=0;support.LocalTransparencyModifier=0
 support.CanCollide=false;tick();check(not circle(),"nonblocking surface is ineligible")
 support.CanCollide=true;state.material=Enum.Material.Water
 tick();check(not circle(),"water hit is not replaced with a seabed ray")
 state.material=Enum.Material.Grass
 local mannequin=Instance.new("Model");mannequin.Parent=s.world
 Instance.new("Humanoid").Parent=mannequin
 local accessory=Instance.new("Model");accessory.Parent=mannequin
 support.Parent=accessory;tick();check(not circle(),"collidable rig-mounted decorative surfaces cannot take the shadow")
 support.Parent=s.world;state.result=nil;tick();check(not circle(),"missing/streamed out floor")
 state.result=support;tick();assertPlate(state)
 return "actual cast rejects steep, transparent, non-solid, water, actor-supported and missing floor"
end

function growthCases.shadow1001_camera_avatar()
 local state,_,head,_,cam,_,at=mount(false)
 tick();assertPlate(state)
 cam.CameraType=Enum.CameraType.Scriptable
 tick();check(not circle(),"freecam with retained own subject still excluded")
 cam.CameraType=Enum.CameraType.Custom;cam.CameraSubject=secondHumanoid
 tick();check(not circle(),"other live avatar observer view never draws own marker")
 cam.CameraSubject=humanoid;cam.CFrame=CFrame.new(at+Vector3.new(0,.7,0))
 tick();check(not circle(),"inside near avatar third-person boundary")
 cam.CFrame=CFrame.new(at+Vector3.new(0,2.5,8));head.LocalTransparencyModifier=1
 tick();check(not circle(),"first person concealed old head")
 head.LocalTransparencyModifier=0;tick();assertPlate(state)
 local old=player.Character
 player.CharacterRemoving:Fire(old);drainDeferred()
 check(not circle(),"old physical avatar loses shadow before new avatar can bind")
 local fresh=Instance.new("Model");fresh.Parent=workspace
 local newH=Instance.new("Humanoid");newH.Parent=fresh
 local newR=Instance.new("Part");newR.Name="HumanoidRootPart";newR.CFrame=rootPart.CFrame;newR.Parent=fresh
 fresh.PrimaryPart=newR
 local newHead=Instance.new("Part");newHead.Name="Head";newHead._props.Transparency=0
 newHead._props.LocalTransparencyModifier=0;newHead.Parent=fresh
 player.Character=fresh;tick();check(not circle(),"new avatar cannot reuse the previous camera subject")
 cam.CameraSubject=newH;tick();assertPlate(state)
 newH.Health=0;newH.Died:Fire();drainDeferred()
 check(not circle(),"new live owner's death retires before the next scheduled update")
 tick();check(not circle(),"no recreation on dead avatar")
 return "Scriptable, observer, first-person and old avatar excluded; own death clears immediately"
end

function growthCases.shadow1001_flags_and_lifetime()
 local state,_,_,_,_,client=mount(true)
 tick();assertPlate(state)
 player:SetAttribute(OFF,true);drainDeferred();check(not circle(),"donor off immediately clears")
 tick();check(not circle(),"off allocates no part")
 player:SetAttribute(OFF,nil);tick();assertPlate(state)
 player:SetAttribute(REDUCED,true);drainDeferred();check(not circle(),"reduced effects clears immediately")
 player:SetAttribute(REDUCED,nil);tick();assertPlate(state)
 humanoid.FloorMaterial=Enum.Material.Air;tick();check(not circle(),"air")
 humanoid.FloorMaterial=Enum.Material.Grass
 state.humanoidState=Enum.HumanoidStateType.Swimming;tick();check(not circle(),"swimming")
 state.humanoidState=nil;player:SetAttribute("EGGRUMBLE_RealmDepth","SUBSEA")
 tick();check(not circle(),"actual private underwater realm never gets a dry shadow")
 player:SetAttribute("EGGRUMBLE_RealmDepth","SURFACE");tick();assertPlate(state)
 player:SetAttribute("EGGRUMBLE_StealthUntil",9000);tick();check(not circle(),"server stealth hides without local deadline inference")
 player:SetAttribute("EGGRUMBLE_StealthUntil",nil);tick();assertPlate(state)
 client:Destroy();drainDeferred();check(not workspace:FindFirstChild(FOLDER),"destroy clears own entire folder")
 local rays=#state.rayTimes
 tick(.5);check(#state.rayTimes==rays and not circle(),"pending scheduled sample cannot resurrect")
 return "runtime OFF, reduced effects, underwater, stealth and script teardown own cleanup"
end

function growthCases.shadow1001_physical_off()
 local state=mount(true)
 tick(1.25)
 check(#state.rayTimes==0 and not workspace:FindFirstChild(FOLDER) and not circle(),"physical old source has no new visuals or rays")
 check(workspace:FindFirstChild("EGGRUMBLE_FarSkyFacets_Local"),"old far sky still runs under exact physical OFF")
 return "physical OFF retains original ArtDistanceLOD and has zero contact shadow work"
end
end
