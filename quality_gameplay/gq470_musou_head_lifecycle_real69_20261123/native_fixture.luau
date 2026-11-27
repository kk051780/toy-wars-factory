-- Fixture API doubles; all source code below remains byte-exact.
local function Signal()
 local signal={handlers={}}
 function signal:Connect(callback)
  local connection={Connected=true}
  function connection:Disconnect() self.Connected=false end
  table.insert(self.handlers,{connection,callback})
  return connection
 end
 function signal:Fire(...)
  local copy=table.clone(self.handlers)
  for _,entry in ipairs(copy) do
   if entry[1].Connected then entry[2](...) end
  end
 end
 function signal:LiveCount()
  local n=0
  for _,entry in ipairs(self.handlers) do if entry[1].Connected then n+=1 end end
  return n
 end
 return signal
end
local function Vec(x,y,z)
 return setmetatable({X=x,Y=y,Z=z,Magnitude=math.sqrt(x*x+y*y+z*z)}, {
  __sub=function(a,b) return Vec(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end,
 })
end
local Vector3={new=Vec}
local Vector2={new=function(x,y) return {X=x,Y=y} end}
local Color3={fromRGB=function(...) return {...} end,new=function(...) return {...} end}
local ColorSequence={new=function(...) return {...} end}
local NumberRange={new=function(...) return {...} end}
local NumberSequence={new=function(...) return {...} end}
local NumberSequenceKeypoint={new=function(...) return {...} end}
local UDim2={fromOffset=function(...) return {...} end,fromScale=function(...) return {...} end}
local Enum={HighlightDepthMode={Occluded='Occluded'},Font={GothamBlack='GothamBlack'}}
local Methods={}
function Methods:FindFirstChild(name)
 for _,child in ipairs(self._children) do if child.Name==name then return child end end
 return nil
end
function Methods:WaitForChild(name)
 return assert(self:FindFirstChild(name),'fixture: missing immediate child '..name)
end
function Methods:IsA(class)
 return self.ClassName==class or class=='Instance' or (class=='BasePart' and self.ClassName=='Part')
end
function Methods:GetAttribute(name) return self._attributes[name] end
function Methods:SetAttribute(name,value)
 local old=self._attributes[name]
 self._attributes[name]=value
 if old~=value and self._attributeSignals[name] then self._attributeSignals[name]:Fire() end
end
function Methods:GetAttributeChangedSignal(name)
 if not self._attributeSignals[name] then self._attributeSignals[name]=Signal() end
 return self._attributeSignals[name]
end
function Methods:GetChildren() return table.clone(self._children) end
function Methods:Destroy()
 if self._destroyed then return end
 self._destroyed=true
 self.Destroying:Fire()
 for _,child in ipairs(table.clone(self._children)) do child:Destroy() end
 self.Parent=nil
end
function Methods:Emit(n) self.Emitted=(self.Emitted or 0)+n end
local function New(class)
 local state={ClassName=class,Name=class,ChildAdded=Signal(),ChildRemoved=Signal(),Destroying=Signal()}
 local instance={_state=state,_children={},_attributes={},_attributeSignals={}}
 return setmetatable(instance,{
  __index=function(self,key) return Methods[key] or self._state[key] end,
  __newindex=function(self,key,value)
   if key=='Parent' then
    local prior=self._state.Parent
    if prior==value then return end
    if prior then
     for i,child in ipairs(prior._children) do
      if child==self then table.remove(prior._children,i);break end
     end
    end
    self._state.Parent=value
    if prior then prior.ChildRemoved:Fire(self) end
    if value then table.insert(value._children,self);value.ChildAdded:Fire(self) end
   elseif string.sub(key,1,1)=='_' then rawset(self,key,value)
   else self._state[key]=value end
  end,
 })
end
local Instance={new=New}
local function Head(character,name)
 local head=New('Part');head.Name=name or 'Head';head.Position=Vec(0,0,0);head.Parent=character
 return head
end
local function Character(withHead)
 local character=New('Model');character.Name='ObserverCharacter'
 if withHead then Head(character) end
 return character
end
local function User(character,active)
 local user=New('Player');user.Name='ObservedPlayer';user.UserId=42;user.Character=character
 user.CharacterAdded=Signal();user.CharacterRemoving=Signal()
 user:SetAttribute('EGGRUMBLE_MusouPhase',if active then 'MUSOU' else 'OFF')
 user:SetAttribute('EGGRUMBLE_MusouRole','WARRIOR')
 user:SetAttribute('EGGRUMBLE_MusouRemaining',if active then 20 else 0)
 return user
end
local function Environment(users)
 local pending={}
 local task={defer=function(callback) table.insert(pending,callback) end}
 local players=New('Players');players.PlayerAdded=Signal();players.PlayerRemoving=Signal()
 for _,user in ipairs(users) do user.Parent=players end
 function players:GetPlayers() return self:GetChildren() end
 local workspace={CurrentCamera={CFrame={Position=Vec(0,0,10)}}}
 local game={GetService=function(_,service)
  if service=='Players' then return players end
  if service=='RunService' then return {IsClient=function() return true end} end
  error('fixture: unimplemented service '..service)
 end}
 local actualAura=(function()
--[[MUSOU_EXACT_AURA_CLIENT_BODY]]

 end)()
 local script={Parent={WaitForChild=function(_,name)
  assert(name=='EGGRUMBLE_MusouAuraClient','fixture: unknown module')
  return actualAura
 end}}
 local require=function(module) assert(module==actualAura);return module end
 local function install()
--[[MUSOU_EXACT_AURA_CONTROLLER_BODY]]

 end
 install()
 return {
  players=players,aura=actualAura,
  flush=function()
   local n=0
   while #pending>0 do
    n+=1;assert(n<100,'fixture: unbounded defer loop')
    table.remove(pending,1)()
   end
  end,
 }
end
local FOLDER='EGGRUMBLE_MUSOU_OBSERVER_AURA'
local function AuraState(character,head)
 local folder=character:FindFirstChild(FOLDER)
 local gui=folder and folder:FindFirstChild('MusouEnemyVisibleNameplate')
 local origin=head and head:FindFirstChild('MusouAuraOrigin')
 local particles=origin and origin:FindFirstChild('RoleAura')
 return {folder=folder~=nil,adorned=gui~=nil and gui.Adornee==head,
  particles=particles~=nil and particles.Enabled==true,
  present=folder~=nil and gui~=nil and gui.Adornee==head and particles~=nil and particles.Enabled==true}
end
local results={}
local function check(name,passed,detail)
 table.insert(results,{name=name,passed=passed})
 print((if passed then 'PASS' else 'FAIL')..'\t'..name..'\t'..detail)
end
local function describe(s)
 return 'folder='..tostring(s.folder)..', currentHeadAdorned='..tostring(s.adorned)..', headEmitter='..tostring(s.particles)
end
-- Control: both full source bodies execute and create the expected actual artifacts.
do
 local c=Character(true);local u=User(c,true);local e=Environment({u})
 local s=AuraState(c,c:FindFirstChild('Head'))
 check('control_head_present_initializes',s.present,describe(s))
end
-- Defect 1: an already-observed active remote player has only its model replicated.
do
 local c=Character(false);local u=User(c,true);local e=Environment({u});e.flush()
 local h=Head(c);e.flush()
 local s=AuraState(c,h)
 check('existing_character_head_arrival_renders_without_new_snapshot',s.present,describe(s))
end
-- Defect 2: CharacterAdded and its defer run before the client receives Head.
do
 local u=User(nil,true);local e=Environment({u});local c=Character(false)
 u.Character=c;u.CharacterAdded:Fire(c);e.flush()
 local h=Head(c);e.flush()
 local s=AuraState(c,h)
 check('new_character_head_arrival_renders_without_new_snapshot',s.present,describe(s))
end
-- Control: a later, unrelated server snapshot causes recovery, localizing missed subscription.
do
 local c=Character(false);local u=User(c,true);local e=Environment({u});local h=Head(c)
 u:SetAttribute('EGGRUMBLE_MusouRemaining',19);e.flush()
 local s=AuraState(c,h)
 check('control_later_snapshot_recovers_missing_aura',s.present,describe(s))
end
-- Boundary: OFF is still authoritative if it arrives before Head.
do
 local c=Character(false);local u=User(c,true);local e=Environment({u})
 u:SetAttribute('EGGRUMBLE_MusouPhase','OFF');u:SetAttribute('EGGRUMBLE_MusouRemaining',0)
 local h=Head(c);e.flush()
 local s=AuraState(c,h)
 check('control_off_before_head_remains_off',not s.folder and not s.particles,describe(s))
end
-- Boundary: an old model's late Head cannot affect the new avatar.
do
 local u=User(nil,true);local e=Environment({u});local old=Character(false)
 u.Character=old;u.CharacterAdded:Fire(old)
 u.CharacterRemoving:Fire(old);u.Character=nil
 local fresh=Character(true);u.Character=fresh;u.CharacterAdded:Fire(fresh)
 local oldHead=Head(old);e.flush()
 local a=AuraState(old,oldHead);local b=AuraState(fresh,fresh:FindFirstChild('Head'))
 check('control_old_avatar_defer_does_not_resurrect',not a.folder and not a.particles and b.present,
  'old{'..describe(a)..'} fresh{'..describe(b)..'}')
end
-- Boundary: a still-current Player.Character reference survives PlayerRemoving callbacks.
do
 local u=User(nil,true);local e=Environment({u});local c=Character(true)
 u.Character=c;u.CharacterAdded:Fire(c)
 e.players.PlayerRemoving:Fire(u);u.Parent=nil;e.flush()
 local s=AuraState(c,c:FindFirstChild('Head'))
 check('removed_player_deferred_render_does_not_resurrect',not s.folder and not s.particles,describe(s))
end
-- Boundary: CharacterRemoving is a pre-removal signal; identity alone is not a liveness token.
do
 local u=User(nil,true);local e=Environment({u});local c=Character(true)
 u.Character=c;u.CharacterAdded:Fire(c)
 u.CharacterRemoving:Fire(c);e.flush()
 local s=AuraState(c,c:FindFirstChild('Head'))
 check('removed_character_deferred_render_does_not_resurrect',not s.folder and not s.particles,describe(s))
end
-- Same-role Head replacement must clean the CURRENT origin even when a prior
-- role update already replaced that origin under the unchanged original Head.
do
 local c=Character(true);local u=User(c,true);local e=Environment({u})
 local old=c:FindFirstChild('Head');local warriorOrigin=old:FindFirstChild('MusouAuraOrigin')
 u:SetAttribute('EGGRUMBLE_MusouRole','MAGE')
 local mageOrigin=old:FindFirstChild('MusouAuraOrigin');local mageFolder=c:FindFirstChild(FOLDER)
 local roleReplaced=warriorOrigin~=nil and mageOrigin~=nil and mageOrigin~=warriorOrigin
  and warriorOrigin.Parent==nil and mageFolder~=nil and mageFolder:GetAttribute('RoleId')=='MAGE'
  and AuraState(c,old).present
 old.Parent=nil
 local h=Head(c);u:SetAttribute('EGGRUMBLE_MusouRemaining',19);e.flush()
 local s=AuraState(c,h)
 local orphan=old:FindFirstChild('MusouAuraOrigin')~=nil
 local current=c:FindFirstChild(FOLDER)
 local currentMage=current~=nil and current:GetAttribute('RoleId')=='MAGE'
 check('same_model_replaced_head_retargets_and_cleans',roleReplaced and currentMage and s.present and not orphan
  and mageOrigin~=nil and mageOrigin.Parent==nil,
  'sameHeadRoleOriginReplaced='..tostring(roleReplaced)..', currentRoleMage='..tostring(currentMage)
  ..', '..describe(s)..', detachedMageHeadEmitter='..tostring(orphan))
end
-- Foreign body parts and a non-BasePart called Head do not start an aura.
do
 local c=Character(false);local u=User(c,true);local e=Environment({u})
 local foreign=Head(c,'ForeignPart');local named=New('Folder');named.Name='Head';named.Parent=c;e.flush()
 local s=AuraState(c,named)
 check('control_foreign_child_does_not_activate_aura',not s.folder and not s.particles,
  describe(s)..', foreignEmitter='..tostring(foreign:FindFirstChild('MusouAuraOrigin')~=nil))
end
-- Existing phase/role visuals still come only from the unchanged real AuraClient.
do
 local c=Character(true);local head=c:FindFirstChild('Head');local u=User(c,true);local e=Environment({u})
 local original=c:FindFirstChild(FOLDER)
 local origin=head:FindFirstChild('MusouAuraOrigin');local particles=origin:FindFirstChild('RoleAura')
 local initial=particles.Emitted
 u:SetAttribute('EGGRUMBLE_MusouPhase','RUSH')
 local rush=original:GetAttribute('Mode')=='RUSH' and particles.Emitted==initial+12
  and string.find(original:FindFirstChild('MusouEnemyVisibleNameplate'):FindFirstChild('State').Text,'連チャン無双',1,true)~=nil
 u:SetAttribute('EGGRUMBLE_MusouPhase','KAKUHEN')
 local fever=original:GetAttribute('Mode')=='KAKUHEN' and particles.Emitted==initial+12+28
  and particles.Rate==24 and c:FindFirstChild(FOLDER)==original
 u:SetAttribute('EGGRUMBLE_MusouRole','MAGE')
 local mage=c:FindFirstChild(FOLDER);local mageOrigin=head:FindFirstChild('MusouAuraOrigin')
 local mageParticles=mageOrigin and mageOrigin:FindFirstChild('RoleAura')
 local role=mage~=original and mage~=nil and mage:GetAttribute('RoleId')=='MAGE'
  and mage:GetAttribute('Mode')=='KAKUHEN' and original.Parent==nil and origin.Parent==nil
  and mageParticles~=nil and mageParticles.Emitted==18 and AuraState(c,head).present
 u:SetAttribute('EGGRUMBLE_MusouPhase','OFF')
 local off=not AuraState(c,head).folder and head:FindFirstChild('MusouAuraOrigin')==nil
 check('control_phase_role_updates_reuse_original_visual_contract',rush and fever and role and off,
  'rush='..tostring(rush)..', fever='..tostring(fever)..', role='..tostring(role)..', off='..tostring(off))
end
-- Extra children, duplicate Head events that preserve the selected Head, and a
-- same-Head snapshot update must not recreate cosmetics or replay the start burst.
do
 local c=Character(true);local head=c:FindFirstChild('Head');local u=User(c,true);local e=Environment({u})
 local folder=c:FindFirstChild(FOLDER);local origin=head:FindFirstChild('MusouAuraOrigin')
 local particles=origin:FindFirstChild('RoleAura');local emitted=particles.Emitted
 local arm=Head(c,'ForeignPart');arm.Parent=nil
 local named=New('Folder');named.Name='Head';named.Parent=c;named.Parent=nil
 local duplicate=Head(c);duplicate.Parent=nil
 u:SetAttribute('EGGRUMBLE_MusouRemaining',19)
 u:SetAttribute('EGGRUMBLE_MusouRemaining',18);e.flush()
 local same=folder==c:FindFirstChild(FOLDER) and origin==head:FindFirstChild('MusouAuraOrigin')
  and particles.Emitted==emitted and AuraState(c,head).present
 check('control_unrelated_child_unchanged_head_no_reburst',same,
  'sameFolder='..tostring(folder==c:FindFirstChild(FOLDER))..', sameOrigin='..tostring(origin==head:FindFirstChild('MusouAuraOrigin'))
  ..', emittedBefore='..emitted..', emittedAfter='..particles.Emitted)
end
-- Observe actual signal subscriptions through twelve avatar lifetimes, then leave.
do
 local u=User(nil,true);local e=Environment({u});local retired={};local old=nil
 for _=1,12 do
  if old then u.CharacterRemoving:Fire(old);u.Character=nil;table.insert(retired,old) end
  local fresh=Character(true);u.Character=fresh;u.CharacterAdded:Fire(fresh);e.flush();old=fresh
 end
 local leaked=0
 for _,c in ipairs(retired) do leaked+=c.ChildAdded:LiveCount()+c.ChildRemoved:LiveCount()+c.Destroying:LiveCount() end
 local currentSignals=old.ChildAdded:LiveCount()+old.ChildRemoved:LiveCount()+old.Destroying:LiveCount()
 e.players.PlayerRemoving:Fire(u);u.Parent=nil;e.flush()
 local userSignals=u.CharacterAdded:LiveCount()+u.CharacterRemoving:LiveCount()
 for _,signal in pairs(u._attributeSignals) do userSignals+=signal:LiveCount() end
 local finalCharacterSignals=old.ChildAdded:LiveCount()+old.ChildRemoved:LiveCount()+old.Destroying:LiveCount()
 local s=AuraState(old,old:FindFirstChild('Head'))
 check('control_lifecycle_connections_bounded_and_disconnected',
  leaked==0 and currentSignals<=2 and userSignals==0 and finalCharacterSignals==0 and not s.folder and not s.particles,
  'retiredSignals='..leaked..', currentSignals='..currentSignals..', afterLeaveUserSignals='..userSignals
  ..', afterLeaveCharacterSignals='..finalCharacterSignals..', '..describe(s))
end
local passed=0
for _,result in ipairs(results) do if result.passed then passed+=1 end end
print('SUMMARY\t'..passed..' PASS / '..(#results-passed)..' FAIL / '..#results..' expectations')
assert(passed==#results,'Lifecycle regression expectations failed for the selected exact source bodies')
