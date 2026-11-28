-- Native UI boundary only. NOT_STUDIO: no rendering, physics, networking, input
-- hit testing or real commerce. The runner inserts three whole original/candidate
-- bodies once at the markers below. Cases use the same boundary for both variants.
local function fixture()
 local f={now=0,errors={},warnings={},threads={},waits={},gates={},cache={},
  failures={},created={},timers={},timeoutArguments={},readonlyControls=0}
 local function expect(ok,message) if not ok then error(message,2) end end
 local function resume(thread,...)
  local result=table.pack(coroutine.resume(thread,...))
  if not result[1] then table.insert(f.errors,tostring(result[2])) end
  return result
 end
 local function launch(callback,...)
  local thread=coroutine.create(callback);table.insert(f.threads,thread)
  resume(thread,...)
  return thread
 end
 local function signal()
  local s={connections={}}
  function s:Connect(callback)
   local c={Connected=true,callback=callback}
   function c:Disconnect()self.Connected=false end
   table.insert(self.connections,c);return c
  end
  function s:Fire(...)
   local threads={}
   for _,c in ipairs(table.clone(self.connections))do
    if c.Connected then table.insert(threads,launch(c.callback,...)) end
   end
   return threads
  end
  function s:activeCount()
   local count=0;for _,c in ipairs(self.connections)do if c.Connected then count+=1 end end
   return count
  end
  return s
 end
 local methods={}
 local meta={}
 function meta.__index(object,key)return methods[key] or object._properties[key]end
 function meta.__newindex(object,key,value)
  local props=object._properties
  local old=props[key]
  if old==value then return end
  if key=='Parent' then
   if old then
    local index=table.find(old._children,object)
    if index then table.remove(old._children,index) end
    old.ChildRemoved:Fire(object)
   end
   props.Parent=value
   if value then table.insert(value._children,object);value.ChildAdded:Fire(object) end
   object.AncestryChanged:Fire(object,value)
  else props[key]=value end
  local changed=object._propertySignals[key];if changed then changed:Fire() end
  if object.Changed then object.Changed:Fire(key) end
 end
 local Instance={}
 function Instance.new(class,parent)
  local object=setmetatable({_properties={ClassName=class,Name=class,Enabled=true,
   Visible=true,ResetOnSpawn=true,Active=false,BackgroundTransparency=0},
   _children={},_attributes={},_attributeSignals={},_propertySignals={}},meta)
  object.Destroying=signal();object.AncestryChanged=signal();object.Changed=signal()
  object.ChildAdded=signal();object.ChildRemoved=signal()
  if class=='TextButton' then object.Activated=signal() end
  table.insert(f.created,object)
  if parent then object.Parent=parent end
  return object
 end
 function methods:IsA(class)
  return self.ClassName==class or class=='Instance' or (class=='BasePart' and self.ClassName=='Part')
 end
 function methods:GetChildren()return table.clone(self._children)end
 function methods:GetDescendants()
  local result={}
  for _,child in ipairs(self._children)do
   table.insert(result,child)
   for _,descendant in ipairs(child:GetDescendants())do table.insert(result,descendant) end
  end
  return result
 end
 function methods:FindFirstChild(name,recursive)
  for _,child in ipairs(self._children)do if child.Name==name then return child end end
  if recursive then
   for _,child in ipairs(self._children)do local found=child:FindFirstChild(name,true);if found then return found end end
  end
  return nil
 end
 function methods:FindFirstChildOfClass(class)
  for _,child in ipairs(self._children)do if child.ClassName==class then return child end end
  return nil
 end
 function methods:FindFirstChildWhichIsA(class,recursive)
  for _,child in ipairs(self._children)do if child:IsA(class) then return child end end
  if recursive then for _,child in ipairs(self._children)do local found=child:FindFirstChildWhichIsA(class,true);if found then return found end end end
  return nil
 end
 function methods:FindFirstAncestor(name)
  local parent=self.Parent
  while parent do if parent.Name==name then return parent end;parent=parent.Parent end
  return nil
 end
 function methods:IsDescendantOf(other)
  local parent=self.Parent
  while parent do if parent==other then return true end;parent=parent.Parent end
  return false
 end
 function methods:SetAttribute(name,value)
  if self._attributes[name]==value then return end
  self._attributes[name]=value
  local changed=self._attributeSignals[name];if changed then changed:Fire() end
 end
 function methods:GetAttribute(name)return self._attributes[name]end
 function methods:GetAttributeChangedSignal(name)
  self._attributeSignals[name]=self._attributeSignals[name] or signal()
  return self._attributeSignals[name]
 end
 function methods:GetPropertyChangedSignal(name)
  self._propertySignals[name]=self._propertySignals[name] or signal()
  return self._propertySignals[name]
 end
 function methods:Destroy()
  if self._properties.Destroyed or self._properties.DestroyInProgress then return end
  self._properties.DestroyInProgress=true
  self.Destroying:Fire()
  for _,child in ipairs(self:GetChildren())do child:Destroy() end
  self.Parent=nil
  self._properties.Destroyed=true
  self._properties.DestroyInProgress=false
 end
 function methods:WaitForChild(name,timeout)
  local found=self:FindFirstChild(name)
  if found then return found end
  expect(timeout==nil or (type(timeout)=='number' and timeout>=0),'invalid WaitForChild timeout')
  local waiting={object=self,name=name,thread=coroutine.running(),
   deadline=if timeout then f.now+timeout else nil,done=false}
  table.insert(f.waits,waiting);table.insert(f.timeoutArguments,timeout or 'UNBOUNDED')
  return coroutine.yield('WAIT_CHILD',waiting)
 end
 local Vector3={};local vectorMeta={}
 function Vector3.new(x,y,z)return setmetatable({X=x,Y=y,Z=z},vectorMeta)end
 function vectorMeta.__sub(a,b)return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z)end
 function vectorMeta.__index(v,k)if k=='Magnitude' then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end end
 local Vector2={new=function(x,y)return {X=x,Y=y}end}
 local Color3={fromRGB=function(r,g,b)return {r=r,g=g,b=b}end,new=function(r,g,b)return {r=r,g=g,b=b}end}
 local UDim={new=function(scale,offset)return {Scale=scale,Offset=offset}end}
 local UDim2={}
 function UDim2.new(xs,xo,ys,yo)return {X=UDim.new(xs,xo),Y=UDim.new(ys,yo)}end
 function UDim2.fromScale(x,y)return UDim2.new(x,0,y,0)end
 function UDim2.fromOffset(x,y)return UDim2.new(0,x,0,y)end
 local Enum=setmetatable({},{__index=function(t,k)
  local group=setmetatable({},{__index=function(_,name)return k..'.'..name end})
  rawset(t,k,group);return group
 end})
 local workspace=Instance.new('Workspace')
 local player=Instance.new('Player');player.Name='LocalPlayer';player.UserId=1001
 player.CharacterAdded=signal();player.CharacterRemoving=signal()
 local playerGui=Instance.new('PlayerGui');playerGui.Name='PlayerGui';playerGui.Parent=player
 local function character()
  local avatar=Instance.new('Model');avatar.Name='Avatar';avatar.Parent=workspace
  local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Position=Vector3.new(0,0,0);root.Parent=avatar
  local hum=Instance.new('Humanoid');hum.Name='Humanoid';hum.Health=100;hum.MaxHealth=100
  hum.HealthChanged=signal();hum.Died=signal();hum.Parent=avatar
  return avatar,root,hum
 end
 local avatar,root,hum=character();player.Character=avatar
 local RunService={Heartbeat=signal(),RenderStepped=signal(),IsStudio=function()return true end}
 local Prompts={PromptTriggered=signal(),PromptHidden=signal()}
 local ReplicatedStorage=Instance.new('ReplicatedStorage')
 local services={RunService=RunService,Players={LocalPlayer=player},
  ProximityPromptService=Prompts,ReplicatedStorage=ReplicatedStorage}
 local game={GetService=function(_,name)return assert(services[name],'forbidden/unmodelled service '..name)end}
 local building=Instance.new('Model');building.Name='GQ805_LobbyGuildShop';building.Parent=workspace
 building:SetAttribute('EGGRUMBLE_ShopPreviewOnly',true)
 local door=Instance.new('Part');door.Name='GuildEntry';door.Position=Vector3.new(0,0,0);door.Parent=building
 local prompt=Instance.new('ProximityPrompt');prompt.Name='GQ805_ShopReadOnlyPrompt';prompt.Parent=door
 local folder=Instance.new('Folder');folder.Name='GQ805Shop';folder.Parent=ReplicatedStorage
 local catNode=Instance.new('ModuleScript');catNode.Name='EGGRUMBLE_LobbyShopCatalog';catNode.Parent=folder
 local viewNode=Instance.new('ModuleScript');viewNode.Name='EGGRUMBLE_LobbyShopView';viewNode.Parent=folder
 local sourceWorld=Instance.new('Folder');sourceWorld.Name='EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW';sourceWorld.Parent=workspace
 local function arena(mode,phase,class)
  local result=Instance.new(class or 'Folder');result.Name=mode..'_Arena';result.Parent=sourceWorld
  result:SetAttribute('EGGRUMBLE_MatchPhase',phase);return result
 end
 local team=arena('TEAM','WAITING');local br=arena('BATTLE_ROYALE','WAITING')
 local function warn(...)table.insert(f.warnings,table.pack(...))end
 local os={clock=function()return f.now end}
 local task={}
 function task.spawn(fn,...)return launch(fn,...)end
 function task.defer(fn,...)local args=table.pack(...);table.insert(f.timers,{deadline=f.now,fn=function()launch(fn,table.unpack(args,1,args.n))end})end
 function task.delay(seconds,fn,...)local args=table.pack(...);table.insert(f.timers,{deadline=f.now+seconds,fn=function()launch(fn,table.unpack(args,1,args.n))end})end

 local function bodyCatalog()
--@@FULL_SOURCE_CATALOG@@
 end
 local function bodyView()
--@@FULL_SOURCE_VIEW@@
 end
 local function require(node)
  local key=if node==catNode then 'catalog' elseif node==viewNode then 'view' else nil
  expect(key~=nil,'unknown ModuleScript require')
  local queue=f.gates[key]
  if queue and #queue>0 then
   local gate=table.remove(queue,1);gate.thread=coroutine.running();gate.entered=true
   coroutine.yield('REQUIRE_GATE',gate)
  end
  if (f.failures[key] or 0)>0 then f.failures[key]-=1;error('controlled '..key..' loader exception') end
  if f.cache[key]==nil then f.cache[key]=if key=='catalog' then bodyCatalog() else bodyView() end
  return f.cache[key]
 end
 local function bodyKiosk()
--@@FULL_SOURCE_KIOSK@@
 end
 f.scriptThread=launch(bodyKiosk)
 f.player=player;f.playerGui=playerGui;f.workspace=workspace;f.building=building;f.door=door;f.prompt=prompt
 f.avatar=avatar;f.root=root;f.hum=hum;f.world=sourceWorld;f.team=team;f.br=br;f.folder=folder
 f.RunService=RunService;f.catNode=catNode;f.viewNode=viewNode;f.Instance=Instance;f.Vector3=Vector3
 function f:assertNoErrors()expect(#self.errors==0,table.concat(self.errors,' | '))end
 function f:gui()return self.playerGui:FindFirstChild('EGGRUMBLE_LobbyShop')end
 function f:trigger(target)
  local threads=Prompts.PromptTriggered:Fire(target or self.prompt,player)
  return threads[1]
 end
 function f:close()
  local gui=self:gui();if gui then gui:FindFirstChild('ShopWindow'):FindFirstChild('Close').Activated:Fire() end
 end
 function f:heartbeat(dt)
  local delta=dt or .25;self.now+=delta
  for _,waiting in ipairs(self.waits)do
   if not waiting.done and waiting.deadline and self.now>=waiting.deadline then
    waiting.done=true;resume(waiting.thread,nil)
   end
  end
  for index=#self.timers,1,-1 do
   local timer=self.timers[index]
   if timer.deadline<=self.now then table.remove(self.timers,index);timer.fn() end
  end
  RunService.Heartbeat:Fire(delta);RunService.RenderStepped:Fire(delta)
  self:assertNoErrors()
 end
 function f:holdNext(site)
  local gate={site=site,entered=false,done=false}
  self.gates[site]=self.gates[site] or {};table.insert(self.gates[site],gate)
  return gate
 end
 function f:resumeGate(gate)
  expect(gate.entered and not gate.done,'require gate unavailable');gate.done=true
  resume(gate.thread);self:assertNoErrors()
 end
 function f:withholdGui()self.playerGui.Parent=nil end
 function f:provideGui()self.playerGui.Parent=player end
 function f:waitFor(thread)
  for _,waiting in ipairs(self.waits)do if waiting.thread==thread and not waiting.done then return waiting end end
  return nil
 end
 function f:resumeGui(thread)
  local waiting=assert(self:waitFor(thread),'no pending PlayerGui wait')
  local child=waiting.object:FindFirstChild(waiting.name);expect(child~=nil,'cannot deliver nonexistent child')
  waiting.done=true;resume(waiting.thread,child);self:assertNoErrors()
 end
 function f:active(mode)
  player:SetAttribute('EGGRUMBLE_QueuedMode',mode)
  local target=if mode=='TEAM' then self.team else self.br
  target:SetAttribute('EGGRUMBLE_MatchPhase','ACTIVE')
 end
 function f:replaceCharacter()
  player.CharacterRemoving:Fire(self.avatar);self.avatar:Destroy()
  self.avatar,self.root,self.hum=character();player.Character=self.avatar
  player.CharacterAdded:Fire(self.avatar)
 end
 function f:kill()
  self.hum.Health=0;self.hum.HealthChanged:Fire(0);self.hum.Died:Fire()
 end
 function f:readonly()
  local gui=assert(self:gui(),'read-only window missing')
  expect(gui:GetAttribute('EGGRUMBLE_ReadOnlyPreview')==true,'read-only marker missing')
  local cards=0;local buttons=0
  for _,card in ipairs(gui:FindFirstChild('ShopWindow'):FindFirstChild('Products'):GetChildren())do
   if card:IsA('Frame')then
    cards+=1
    for _,button in ipairs(card:GetChildren())do
     if button:IsA('TextButton')then expect(button.Active==false,'purchase button enabled');buttons+=1 end
    end
   end
  end
  expect(cards==14 and buttons==28,'original Catalog/View output changed')
  for _,object in ipairs(self.created)do
   expect(object.ClassName~='RemoteEvent' and object.ClassName~='RemoteFunction' and object.ClassName~='UnreliableRemoteEvent','new remote created')
  end
 end
 function f:observerCount()return RunService.Heartbeat:activeCount()end
 function f:check(ok,message)expect(ok,message)end
 f:assertNoErrors()
 return f
end

local cases={}
local function case(name,baseline,fn)table.insert(cases,{name=name,baseline=baseline,run=fn})end
local function open(f)f:trigger();f:assertNoErrors();f:check(f:gui()~=nil,'expected shop open');f:readonly();return f:gui()end
local function noWindow(f,message)f:assertNoErrors();f:check(f:gui()==nil,message or 'unexpected shop window')end

case('existing_38_readonly_controls','PASS',function()
 local f=fixture();local count=0
 local function check(ok,message)f:check(ok,message);count+=1 end
 f.prompt.Name='wrong';f:trigger();check(f:gui()==nil,'wrong prompt accepted');f.prompt.Name='GQ805_ShopReadOnlyPrompt'
 f.root.Position=f.Vector3.new(14,0,0);f:trigger();check(f:gui()==nil,'outside13 accepted');f.root.Position=f.Vector3.new(0,0,0)
 f.hum.Health=0;f:trigger();check(f:gui()==nil,'dead avatar accepted');f.hum.Health=100
 f.player:SetAttribute('EGGRUMBLE_Eliminated',true);f:trigger();check(f:gui()==nil,'eliminated accepted');f.player:SetAttribute('EGGRUMBLE_Eliminated',nil)
 f:trigger();local first=f:gui();check(first~=nil and first.Enabled,'normal nearby user did not mount')
 local frame=first:FindFirstChild('ShopWindow')
 check(frame.Size.X.Scale==.9 and frame.Size.Y.Scale==.78 and first.DisplayOrder==20,'original View layout changed')
 local cards=0;local buttons=0
 for _,card in ipairs(frame:FindFirstChild('Products'):GetChildren())do
  if card:IsA('Frame')then
   cards+=1
   for _,button in ipairs(card:GetChildren())do if button:IsA('TextButton')then check(button.Active==false,'purchase enabled');buttons+=1 end end
  end
 end
 check(cards==14 and buttons==28,'original cards missing')
 f:close();check(f:gui()==nil and first.Destroyed,'close did not destroy window')
 f:trigger();check(f:gui()~=nil and f:gui()~=first,'reopen did not create a new window')
 f:close();f:assertNoErrors();check(#f.warnings==0,'unexpected warning')
 f:check(count==38,'original 38-control set changed')
 print('CONTROLS\t38')
end)

case('matching_waiting_modes_remain_available','PASS',function()
 for _,mode in ipairs({'TEAM','BATTLE_ROYALE'})do
  local f=fixture();f.player:SetAttribute('EGGRUMBLE_QueuedMode',mode);open(f);f:heartbeat();f:check(f:gui()~=nil,'waiting mode blocked')
 end
end)
case('other_active_arena_does_not_block_lobby_or_waiting','PASS',function()
 for _,mode in ipairs({'NONE','TEAM'})do
  local f=fixture();f.br:SetAttribute('EGGRUMBLE_MatchPhase','ACTIVE')
  if mode~='NONE' then f.player:SetAttribute('EGGRUMBLE_QueuedMode',mode) end
  open(f);f:heartbeat();f:check(f:gui()~=nil,'unrelated active match blocked view')
 end
end)
case('missing_nonactive_or_wrong_class_arena_remains_available','PASS',function()
 for _,state in ipairs({'MISSING','NO_PHASE','FINISHED','WRONG_CLASS'})do
  local f=fixture();f.player:SetAttribute('EGGRUMBLE_QueuedMode','TEAM')
  if state=='MISSING' then f.team:Destroy()
  elseif state=='NO_PHASE' then f.team:SetAttribute('EGGRUMBLE_MatchPhase',nil)
  elseif state=='FINISHED' then f.team:SetAttribute('EGGRUMBLE_MatchPhase','FINISHED')
  else f.team:Destroy();local impostor=f.Instance.new('Part');impostor.Name='TEAM_Arena';impostor:SetAttribute('EGGRUMBLE_MatchPhase','ACTIVE');impostor.Parent=f.world end
  open(f);f:heartbeat();f:check(f:gui()~=nil,'nonmatching active contract blocked view')
 end
end)
case('active_entry_rejected_in_both_modes','FAIL',function()
 for _,mode in ipairs({'TEAM','BATTLE_ROYALE'})do local f=fixture();f:active(mode);f:trigger();noWindow(f,'ACTIVE entry mounted');f:check(f:observerCount()==0,'rejected entry leaked observer')end
end)
case('waiting_to_active_closes_without_mode_event','FAIL',function()
 for _,mode in ipairs({'TEAM','BATTLE_ROYALE'})do
  local f=fixture();f.player:SetAttribute('EGGRUMBLE_QueuedMode',mode);local gui=open(f)
  local target=if mode=='TEAM' then f.team else f.br;target:SetAttribute('EGGRUMBLE_MatchPhase','ACTIVE')
  f:heartbeat();noWindow(f,'phase-only ACTIVE left window open');f:check(gui.Destroyed and f:observerCount()==0,'ACTIVE cleanup incomplete')
 end
end)
case('late_active_arena_arrival_closes_window','FAIL',function()
 local f=fixture();f.team:Destroy();f.player:SetAttribute('EGGRUMBLE_QueuedMode','TEAM');open(f)
 local arriving=f.Instance.new('Folder');arriving.Name='TEAM_Arena';arriving:SetAttribute('EGGRUMBLE_MatchPhase','ACTIVE');arriving.Parent=f.world
 f:heartbeat();noWindow(f,'late ACTIVE arena was missed')
end)
case('walking_away_after_mount_remains_allowed','PASS',function()
 local f=fixture();local gui=open(f);f.root.Position=f.Vector3.new(250,0,0);f:heartbeat();f:check(f:gui()==gui and gui.Enabled,'mounted exploration view closed only for distance')
end)
case('opened_window_closes_on_character_replacement','FAIL',function()
 local f=fixture();open(f);f:replaceCharacter();f:heartbeat();noWindow(f,'old avatar window remained');open(f)
end)
case('opened_window_closes_on_death_or_elimination','FAIL',function()
 for _,kind in ipairs({'dead','eliminated'})do
  local f=fixture();open(f)
  if kind=='dead' then f:kill() else f.player:SetAttribute('EGGRUMBLE_Eliminated',true) end
  f:heartbeat();noWindow(f,'ineligible avatar window remained')
 end
end)
case('manual_close_reopen_has_no_observer_growth','PASS',function()
 local f=fixture()
 for _=1,10 do
  open(f);f:check(f:observerCount()<=1,'multiple live request observers')
  f:close();f:heartbeat();noWindow(f,'manual close failed');f:check(f:observerCount()==0,'closed window left observer')
 end
end)
case('old_window_cleanup_preserves_foreign_replacement','PASS',function()
 local f=fixture();local old=open(f);old:Destroy()
 local foreign=f.Instance.new('ScreenGui');foreign.Name='EGGRUMBLE_LobbyShop';foreign.Parent=f.playerGui
 f:active('TEAM');f:heartbeat();f:check(f:gui()==foreign and not foreign.Destroyed,'old cleanup destroyed foreign replacement')
end)
case('gui_detach_disconnects_owned_observer','PASS',function()
 local f=fixture();local gui=open(f);gui.Parent=nil;f:heartbeat();f:check(f:observerCount()==0,'detached GUI leaked observer')
end)

local mutations={
 none=function()end,
 waiting=function(f)f.player:SetAttribute('EGGRUMBLE_QueuedMode','TEAM');f:heartbeat()end,
 active_team=function(f)f:active('TEAM');f:heartbeat()end,
 active_br=function(f)f:active('BATTLE_ROYALE');f:heartbeat()end,
 character=function(f)f:replaceCharacter();f:heartbeat()end,
 prompt_destroy=function(f)f.prompt:Destroy();f:heartbeat()end,
 ancestor_detach=function(f)f.building.Parent=nil;f:heartbeat()end,
 preview_revoked=function(f)f.building:SetAttribute('EGGRUMBLE_ShopPreviewOnly',false);f:heartbeat()end,
 far=function(f)f.root.Position=f.Vector3.new(14,0,0);f:heartbeat()end,
 dead=function(f)f:kill();f:heartbeat()end,
 eliminated=function(f)f.player:SetAttribute('EGGRUMBLE_Eliminated',true);f:heartbeat()end,
 active_then_waiting=function(f)f:active('TEAM');f:heartbeat();f.team:SetAttribute('EGGRUMBLE_MatchPhase','WAITING');f:heartbeat()end,
 dead_then_alive=function(f)f:kill();f:heartbeat();f.hum.Health=100;f.hum.HealthChanged:Fire(100);f:heartbeat()end,
}
local yieldCases={
 {'require_catalog_valid','catalog','none',true},
 {'require_view_valid','view','none',true},
 {'playergui_valid','playergui','none',true},
 {'playergui_queued_waiting','playergui','waiting',true},
 {'require_catalog_active_team','catalog','active_team',false},
 {'require_view_active_br','view','active_br',false},
 {'playergui_active_team','playergui','active_team',false},
 {'require_catalog_character_replaced','catalog','character',false},
 {'playergui_character_replaced','playergui','character',false},
 {'require_view_prompt_destroyed','view','prompt_destroy',false},
 {'playergui_prompt_destroyed','playergui','prompt_destroy',false},
 {'playergui_ancestor_detached','playergui','ancestor_detach',false},
 {'playergui_preview_revoked','playergui','preview_revoked',false},
 {'playergui_outside_range','playergui','far',false},
 {'require_view_dead','view','dead',false},
 {'playergui_eliminated','playergui','eliminated',false},
 {'require_catalog_active_then_waiting','catalog','active_then_waiting',false},
 {'playergui_dead_then_alive','playergui','dead_then_alive',false},
}
for _,row in ipairs(yieldCases)do
 local name,site,mutation,want=table.unpack(row)
 case(name,if want then 'PASS' else 'FAIL',function()
  local f=fixture();local gate=nil
  if site=='playergui' then f:withholdGui() else gate=f:holdNext(site) end
  local first=f:trigger();f:assertNoErrors()
  f:check(coroutine.status(first)=='suspended','did not enter controlled dependency wait')
  if gate then f:check(gate.entered,'wrong require boundary') else f:check(f:waitFor(first)~=nil,'wrong PlayerGui boundary') end
  noWindow(f,'mounted before dependency returned')
  local duplicate=f:trigger();f:check(coroutine.status(duplicate)=='dead','busy request spawned another pending open')
  noWindow(f,'busy duplicate mounted')
  mutations[mutation](f)
  if site=='playergui' then f:provideGui();f:resumeGui(first) else f:resumeGate(gate) end
  f:check(coroutine.status(first)=='dead','dependency resume did not end request')
  if want then f:readonly();f:check(f:gui()~=nil,'valid dependency resume did not mount')
  else noWindow(f,'stale dependency resume mounted');f:check(f:observerCount()==0,'retired request observer remains') end
  f:check(#f.warnings==0,'unexpected warning on cancelled request')
 end)
end

case('pending_root_or_humanoid_identity_change_is_rejected','FAIL',function()
 for _,kind in ipairs({'root','humanoid'})do
  local f=fixture();f:withholdGui();local request=f:trigger()
  if kind=='root' then
   f.root:Destroy();local replacement=f.Instance.new('Part');replacement.Name='HumanoidRootPart';replacement.Position=f.Vector3.new(0,0,0);replacement.Parent=f.avatar
  else
   f.hum:Destroy();local replacement=f.Instance.new('Humanoid');replacement.Name='Humanoid';replacement.Health=100;replacement.Parent=f.avatar
  end
  f:heartbeat();f:provideGui();f:resumeGui(request);noWindow(f,'changed avatar component revived old request')
 end
end)
case('require_exception_releases_request_for_retry','PASS',function()
 for _,site in ipairs({'catalog','view'})do
  local f=fixture();f.failures[site]=1;local request=f:trigger();f:assertNoErrors()
  f:check(coroutine.status(request)=='dead','require failure did not terminate');noWindow(f,'require exception mounted')
  f:check(#f.warnings==1,'require exception warning missing');f:check(f:observerCount()==0,'require exception leaked observer')
  open(f)
 end
end)
case('playergui_timeout_terminates_and_allows_new_prompt','FAIL',function()
 local f=fixture();f:withholdGui();local request=f:trigger()
 f:check(f.timeoutArguments[1]==5,'PlayerGui wait is not bounded to five seconds')
 f:heartbeat(5.1);f:check(coroutine.status(request)=='dead','timed-out request remained pending')
 noWindow(f,'timeout mounted');f:check(f:observerCount()==0,'timeout leaked observer')
 f:provideGui();open(f)
end)
case('old_A_resume_preserves_new_B_window_identity','FAIL',function()
 local f=fixture();f:withholdGui();local requestA=f:trigger()
 f:active('TEAM');f:heartbeat();f.team:SetAttribute('EGGRUMBLE_MatchPhase','WAITING')
 f:provideGui();local requestB=f:trigger();f:assertNoErrors()
 f:check(coroutine.status(requestB)=='dead','new request B did not finish')
 local guiB=f:gui();f:check(guiB~=nil,'cancelled A blocked valid B')
 f:resumeGui(requestA)
 f:check(f:gui()==guiB and not guiB.Destroyed,'late A replaced/destroyed B window')
 f:check(f:observerCount()==1,'A completion removed B observer or left an extra observer')
 f:close();f:heartbeat();f:check(f:observerCount()==0,'B close did not clean observer')
end)
case('old_A_timeout_does_not_unlock_pending_B','FAIL',function()
 local f=fixture();f:withholdGui();local requestA=f:trigger()
 f:active('TEAM');f:heartbeat(1);f.team:SetAttribute('EGGRUMBLE_MatchPhase','WAITING')
 local requestB=f:trigger();f:check(coroutine.status(requestB)=='suspended','new B did not own pending state')
 f:heartbeat(4.1)
 f:check(coroutine.status(requestA)=='dead','old A did not finish at its deadline')
 f:check(coroutine.status(requestB)=='suspended','old A completion terminated B')
 local extra=f:trigger();f:check(coroutine.status(extra)=='dead','old A completion unlocked B pending state')
 f:check(f:observerCount()==1,'B pending observer ownership lost')
 f:provideGui();f:resumeGui(requestB);f:readonly();f:check(f:gui()~=nil,'B did not mount')
end)
case('missing_modules_recover_without_authority','PASS',function()
 local f=fixture();f.viewNode.Parent=nil;f:trigger();noWindow(f,'missing view mounted')
 f:check(#f.warnings==1 and f:observerCount()==0,'missing module recovery incomplete')
 f.viewNode.Parent=f.folder;open(f)
end)
case('pending_revalidation_without_heartbeat_still_rejects_stale','FAIL',function()
 for _,kind in ipairs({'ACTIVE','CHARACTER','PROMPT','DISTANCE'})do
  local f=fixture();f:withholdGui();local request=f:trigger()
  if kind=='ACTIVE' then f:active('TEAM')
  elseif kind=='CHARACTER' then f:replaceCharacter()
  elseif kind=='PROMPT' then f.prompt:Destroy()
  else f.root.Position=f.Vector3.new(14,0,0) end
  f:provideGui();f:resumeGui(request);noWindow(f,'resume relied only on periodic observer')
 end
end)

local passed=0;local failed=0
for _,entry in ipairs(cases)do
 print('PLAN\t'..entry.name..'\t'..entry.baseline)
 local ok,err=pcall(entry.run)
 if ok then passed+=1;print('CASE\t'..entry.name..'\tPASS')
 else
  failed+=1
  local message=tostring(err):gsub('[\r\n\t]',' ')
  print('CASE\t'..entry.name..'\tFAIL\t'..message)
 end
end
print(string.format('SUMMARY\t%d\t%d\t%d\tNOT_STUDIO',#cases,passed,failed))
if failed>0 then error('NATIVE_SHOP_LIFECYCLE_FAILURES='..failed) end
