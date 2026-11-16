-- Pure Native Luau behavioral checks against the REAL EGGRUMBLE_RoundReplay module.
-- The harness prepends local fake game services, then the verbatim source before these cases.
local checks=0
local function check(cond:boolean,message:string)
 checks+=1
 assert(cond,message)
end
local function phase(value:string,winner:any)
 return {rules={phase=value,winner=winner}}
end

-- A match that has not ended must never schedule teardown.
local active=phase("ACTIVE",nil)
local activeCalls=0
check(Replay.schedule(active,function() activeCalls+=1 end)==false,"active must not close")
check(#pending==0,"active scheduled a timer")
local unresolved=phase("FINISHED",nil)
check(Replay.schedule(unresolved,function() error("premature") end)==false,"winner missing")
check(#pending==0,"missing winner scheduled a timer")

-- A genuine concluded round is closed exactly once and only after the result banner.
local red=phase("FINISHED","RED")
local closeCount=0
check(Replay.schedule(red,function() closeCount+=1 end)==true,"finished round not scheduled")
check(red.roundReplayScheduled==true,"replay lock missing")
check(#pending==1,"expected one timer")
check(pending[1].seconds==10,"result must last 8s before 10s cleanup")
check(Replay.schedule(red,function() error("double teardown") end)==false,"double schedule succeeded")
check(#pending==1,"duplicate timer created")
check(closeCount==0,"closed before result held")
pending[1].fn()
check(closeCount==1,"finished round not closed")
check(activeCalls==0,"active match closed")

-- A stale finish timer must never destroy a new ACTIVE round instance.
pending={}
local stale=phase("FINISHED","BLUE")
local invalidated=0
check(Replay.schedule(stale,function() invalidated+=1 end)==true,"stale case not scheduled")
stale.rules.phase="ACTIVE"
pending[1].fn()
check(invalidated==0,"old round timer destroyed newly active round")
pending={}

-- TEAM / BR are independent queues and independent timers; no global singleton.
local team=phase("FINISHED","RED")
local br=phase("FINISHED","AI_14")
local teamEnds=0
local brEnds=0
check(Replay.schedule(team,function() teamEnds+=1 end),"team timer missing")
check(Replay.schedule(br,function() brEnds+=1 end),"royale timer missing")
check(#pending==2,"two modes did not receive independent timers")
pending[2].fn()
check(brEnds==1 and teamEnds==0,"BR timer changed TEAM match")
pending[1].fn()
check(brEnds==1 and teamEnds==1,"TEAM timer changed BR match")
pending={}

-- Studio-only constraint is enforced at execution time.
studio=false
local ok=pcall(function() Replay.schedule(phase("FINISHED","RED"),function() end) end)
check(not ok,"preview replay allowed outside Studio")
studio=true

-- Human case: clear per-round KO, stealth etc while retaining chosen role.
local ret={x=5,y=8,z=-5}
local health={Health=100,WalkSpeed=20,attributes={EGGRUMBLE_OriginalWalkSpeed=20,EGGRUMBLE_SlowExpiry=99999,EGGRUMBLE_MarkedUntil=99999}}
function health:SetAttribute(name:string,value:any) self.attributes[name]=value end
local root={CFrame=nil}
local shield={Parent=true,destroyed=false}
function shield:IsA(typeName:string) return typeName=="ForceField" end
function shield:Destroy() self.Parent=nil;self.destroyed=true end
local stats={ko={Value=29}}
function stats:FindFirstChild(key)
 return if key=="NeutralKO" then self.ko else nil
end
function stats.ko:IsA(typeName:string)
 return typeName=="IntValue"
end
local human={
 Parent=playersService,UserId=124,attributes={EGGRUMBLE_SelectedRole="MAGE"},
 stats=stats,Character={humanoid=health,root=root},loads=0
}
function human:SetAttribute(key:string,value:any) self.attributes[key]=value end
function human:FindFirstChild(name:string)
 return if name=="leaderstats" then self.stats else nil
end
function human.Character:FindFirstChildOfClass(typeName:string)
 return if typeName=="Humanoid" then self.humanoid else nil
end
function human.Character:FindFirstChild(name:string)
 return if name=="HumanoidRootPart" then self.root
  elseif name=="EGGRUMBLE_ItemShield" then shield else nil
end
function human:LoadCharacter() self.loads+=1 end
local serverBaseline=Replay.captureWalkBaseline(human)
check(serverBaseline==20,"actual server pre-item walk speed not recorded")
health.WalkSpeed=27 -- original FieldItemPickups.DASH applies this for five seconds
check(Replay.resetHuman(human,ret,serverBaseline)==nil,"reset should return no value")
check(health.WalkSpeed==20,"DASH speed persisted into next lobby")
check(health.attributes.EGGRUMBLE_OriginalWalkSpeed==nil and health.attributes.EGGRUMBLE_SlowExpiry==nil,
 "old combat slow restored speed after item/lobby reset")
check(health.attributes.EGGRUMBLE_MarkedUntil==nil,"old mark status persisted")
check(shield.destroyed and shield.Parent==nil,"old field item SHIELD persisted into next match")
health.WalkSpeed=1000
check(Replay.captureWalkBaseline(human)==16,"out-of-range walk speed must not become next match baseline")
health.WalkSpeed=20
check(root.CFrame and root.CFrame.position==ret,"alive human not returned to lobby")
check(human.loads==0,"alive human was forcibly respawned")
check(human.attributes.EGGRUMBLE_SelectedRole=="MAGE","chosen role lost")
check(human.attributes.EGGRUMBLE_QueuedMode==nil,"stale queue attribute")
check(human.attributes.EGGRUMBLE_Eliminated==nil,"eliminated marker retained")
check(human.attributes.EGGRUMBLE_NeutralKOs==0 and stats.ko.Value==0,"fake replay KO kept")
check(human.attributes.EGGRUMBLE_BattleLevel==1,"level did not reset")
check(human.attributes.EGGRUMBLE_SlashEvolution=="BASE","old skill tier kept")
check(human.attributes.EGGRUMBLE_Role==nil,"old role match attr retained")

-- If eliminated and dead, server requests a new humanoid so next match is playable.
local dead={Parent=playersService,UserId=125,attributes={},loads=0,Character={}}
function dead:SetAttribute(key:string,value:any) self.attributes[key]=value end
function dead:FindFirstChild(name:string) return nil end
function dead.Character:FindFirstChildOfClass(name:string) return nil end
function dead.Character:FindFirstChild(name:string) return nil end
function dead:LoadCharacter() self.loads+=1 end
Replay.resetHuman(dead,ret)
check(dead.loads==1,"dead player not respawned for replay")

-- A transient failed LoadCharacter request is retried once without a loop.
pending={}
local retry={Parent=playersService,UserId=127,attributes={},loads=0,Character={}}
function retry:SetAttribute(key:string,value:any) self.attributes[key]=value end
function retry:GetAttribute(key:string):any return self.attributes[key] end
function retry:FindFirstChild(name:string) return nil end
function retry.Character:FindFirstChildOfClass(name:string) return nil end
function retry.Character:FindFirstChild(name:string) return nil end
function retry:LoadCharacter()
 self.loads+=1
 if self.loads==1 then error("temporary Studio respawn refused") end
end
Replay.resetHuman(retry,ret)
check(retry.loads==1,"failed respawn did not attempt immediately")
check(#pending==1 and pending[1].seconds==1,"failed respawn did not schedule bounded retry")
pending[1].fn()
check(retry.loads==2,"failed respawn did not recover on retry")
check(#pending==1,"unexpected unbounded retry loop")

-- A stale retry must not touch a player who has already entered a different mode.
pending={}
local queued={Parent=playersService,UserId=128,attributes={},loads=0,Character={}}
function queued:SetAttribute(key:string,value:any) self.attributes[key]=value end
function queued:GetAttribute(key:string):any return self.attributes[key] end
function queued:FindFirstChild(name:string) return nil end
function queued.Character:FindFirstChildOfClass(name:string) return nil end
function queued.Character:FindFirstChild(name:string) return nil end
function queued:LoadCharacter()
 self.loads+=1
 if self.loads==1 then error("first attempt declined") end
end
Replay.resetHuman(queued,ret)
check(queued.loads==1 and #pending==1,"queued player did not schedule retry")
queued.attributes.EGGRUMBLE_QueuedMode="BATTLE_ROYALE"
pending[1].fn()
check(queued.loads==1,"old lobby retry touched an active new match")

-- A bot-filled active session must not block the next arrival once the final human leaves.
pending={}
local orphanTeam={mode="TEAM",rules={phase="ACTIVE",winner=nil},
 roster={{id="201",isAI=false,team="RED"},{id="AI_1",isAI=true,team="BLUE"}}}
local present={[201]="TEAM"}
playersService.active[201]={UserId=201}
local orphanCloses=0
check(Replay.abandonIfEmpty(orphanTeam,present,function() orphanCloses+=1 end)==false,
 "connected human was incorrectly abandoned")
check(orphanCloses==0,"connected session was closed")
present[201]=nil -- PlayerRemoving has already cleared joined
check(Replay.abandonIfEmpty(orphanTeam,present,function() orphanCloses+=1 end)==true,
 "last-human disconnect must abandon orphan AI match")
check(orphanCloses==1,"orphan cleanup did not run exactly once")
check(orphanTeam.roundReplayScheduled==true,"abandonment must lock duplicate cleanup")
check(#pending==0,"orphan match must not wait for a fake winner or 10s result")
check(Replay.abandonIfEmpty(orphanTeam,present,function() error("double teardown") end)==false,
 "orphan cleanup repeated")
check(orphanTeam.rules.winner==nil,"orphan cleanup fabricated a victorious bot")

-- Mixed teams: keep the match while at least one real human is still present.
local twoHumans={mode="TEAM",rules={phase="ACTIVE",winner=nil},
 roster={{id="301",isAI=false,team="RED"},{id="302",isAI=false,team="BLUE"},
         {id="AI_1",isAI=true,team="BLUE"}}}
local stillJoined={[301]="TEAM",[302]="TEAM"}
playersService.active[301]={UserId=301}
playersService.active[302]={UserId=302}
local humanCloses=0
stillJoined[301]=nil
check(Replay.abandonIfEmpty(twoHumans,stillJoined,function() humanCloses+=1 end)==false,
 "one remaining player must preserve PvP match")
check(humanCloses==0,"one remaining player was torn down")
stillJoined[302]=nil
check(Replay.abandonIfEmpty(twoHumans,stillJoined,function() humanCloses+=1 end)==true,
 "empty human session did not release arena")
check(humanCloses==1,"second abandonment must close exactly once")

-- A genuinely finished match must keep its result banner, not be abandoned.
local finished=phase("FINISHED","RED")
finished.roster={{id="401",isAI=false}}
finished.mode="TEAM"
local fakeCloses=0
check(Replay.abandonIfEmpty(finished,{},function() fakeCloses+=1 end)==false,
 "genuine result banner was bypassed")
check(fakeCloses==0,"result of a finished round was thrown away")

-- Ownership: never abandon a live match based on an unrelated mode's joined table.
local isolated={mode="BATTLE_ROYALE",rules={phase="ACTIVE",winner=nil},
 roster={{id="501",isAI=false},{id="AI_1",isAI=true}}}
playersService.active[501]={UserId=501}
check(Replay.abandonIfEmpty(isolated,{[501]="BATTLE_ROYALE"},function() error("wrong mode") end)==false,
 "BR user must preserve BR match")

-- Left players are ignored, and no cross-player mutations occur after removal.
local gone={Parent=nil,UserId=126,attributes={}}
function gone:SetAttribute(key:string,v:any) self.attributes[key]=v end
Replay.resetHuman(gone,ret)
check(next(gone.attributes)==nil,"left player mutated after leaving")
-- Waiting-room modes can be switched, cancelled, and requeued without stale timers.
local waitAlice={UserId=601}
local waitBob={UserId=602}
local waitCarol={UserId=603}
local waitEpoch={TEAM=0,BATTLE_ROYALE=0}
local waitQ={TEAM={waitAlice},BATTLE_ROYALE={}}
local waitJoined={[601]="TEAM"}
local waitSessions={}
check(Replay.canStartCountdown("TEAM",0,waitQ,waitEpoch,waitSessions)==true,
 "new TEAM queue should start after its own countdown")
check(Replay.canStartCountdown("BATTLE_ROYALE",0,waitQ,waitEpoch,waitSessions)==false,
 "empty BR queue should not start")
check(Replay.leaveWaitingQueue("TEAM",waitBob,waitQ,waitJoined,waitEpoch,waitSessions)==false,
 "unregistered person removed a queue")
check(#waitQ.TEAM==1 and waitJoined[601]=="TEAM","invalid cancellation mutated queue")
check(Replay.leaveWaitingQueue("TEAM",waitAlice,waitQ,waitJoined,waitEpoch,waitSessions)==true,
 "tapping same gate did not cancel")
check(#waitQ.TEAM==0 and waitJoined[601]==nil,"cancel did not release waiting seat")
check(waitEpoch.TEAM==1 and waitEpoch.BATTLE_ROYALE==0,
 "last waiter must advance only TEAM epoch")
check(Replay.canStartCountdown("TEAM",0,waitQ,waitEpoch,waitSessions)==false,
 "stale TEAM timer may not start on an emptied queue")
table.insert(waitQ.TEAM,waitBob)
waitJoined[602]="TEAM"
check(Replay.canStartCountdown("TEAM",0,waitQ,waitEpoch,waitSessions)==false,
 "stale old TEAM timer started new human's match early")
check(Replay.canStartCountdown("TEAM",1,waitQ,waitEpoch,waitSessions)==true,
 "fresh TEAM queue must get a full new countdown")

-- If another waiting teammate remains, their original timer stays valid.
table.insert(waitQ.TEAM,waitCarol)
waitJoined[603]="TEAM"
check(Replay.leaveWaitingQueue("TEAM",waitBob,waitQ,waitJoined,waitEpoch,waitSessions)==true,
 "first of two humans could not withdraw")
check(#waitQ.TEAM==1 and waitQ.TEAM[1]==waitCarol,"wrong player removed")
check(waitEpoch.TEAM==1,"withdrawal with another waiter reset timer")
check(Replay.canStartCountdown("TEAM",1,waitQ,waitEpoch,waitSessions)==true,
 "remaining teammate lost their legitimate timer")

-- The other gate can be selected before a mode starts, without editing its session.
check(Replay.leaveWaitingQueue("TEAM",waitCarol,waitQ,waitJoined,waitEpoch,waitSessions)==true,
 "cannot switch out of TEAM waiting")
table.insert(waitQ.BATTLE_ROYALE,waitCarol)
waitJoined[603]="BATTLE_ROYALE"
check(waitEpoch.TEAM==2 and waitEpoch.BATTLE_ROYALE==0,
 "switch corrupted BR timer or failed to invalidate empty TEAM")
check(Replay.canStartCountdown("TEAM",1,waitQ,waitEpoch,waitSessions)==false,
 "old TEAM mode timer survived switch")
check(Replay.canStartCountdown("BATTLE_ROYALE",0,waitQ,waitEpoch,waitSessions)==true,
 "BR mode cannot accept switched player")
check(Replay.leaveWaitingQueue("TEAM",waitCarol,waitQ,waitJoined,waitEpoch,waitSessions)==false,
 "wrong mode removed switched player")
check(#waitQ.BATTLE_ROYALE==1 and waitJoined[603]=="BATTLE_ROYALE",
 "wrong-mode cancellation changed active BR waiting seat")

-- Players in an existing match cannot cancel or switch via a lobby gate.
waitSessions.BATTLE_ROYALE={rules={phase="ACTIVE"}}
check(Replay.leaveWaitingQueue("BATTLE_ROYALE",waitCarol,waitQ,waitJoined,waitEpoch,waitSessions)==false,
 "live round participant escaped via queue cancellation")
check(Replay.canStartCountdown("BATTLE_ROYALE",0,waitQ,waitEpoch,waitSessions)==false,
 "existing match received another start timer")
waitSessions.BATTLE_ROYALE=nil
check(Replay.leaveWaitingQueue("BATTLE_ROYALE",waitCarol,waitQ,waitJoined,waitEpoch,waitSessions)==true,
 "pre-match BR candidate cannot cancel")
check(waitEpoch.BATTLE_ROYALE==1 and #waitQ.BATTLE_ROYALE==0,
 "BR timer was not cancelled when last waiter left")

-- Hidden production runtime should reject even these helper entry points.
studio=false
check(not pcall(function()
 Replay.leaveWaitingQueue("TEAM",waitAlice,waitQ,waitJoined,waitEpoch,waitSessions)
end),"live Roblox server allowed Studio-only queue mutation")
check(not pcall(function()
 Replay.canStartCountdown("TEAM",2,waitQ,waitEpoch,waitSessions)
end),"live Roblox server allowed Studio-only queue timer")
studio=true

-- Rejoining the SAME actual castle after dying: live avatar and castle only.
local respawnHome={x=18,y=7,z=90}
local respawnHero={UserId=711,Parent=playersService}
local respawnCharacter={root={CFrame=nil},humanoid={Health=100}}
function respawnCharacter:FindFirstChildOfClass(key:string):any
 return if key=="Humanoid" then self.humanoid else nil
end
function respawnCharacter:FindFirstChild(key:string):any
 return if key=="HumanoidRootPart" then self.root else nil
end
respawnHero.Character=respawnCharacter
local respawnSession={rules={phase="ACTIVE",castles={["711"]={alive=true}}},
 world={Parent={}},castleLocations={["711"]={x=0,y=0,z=0}}}
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==true,
 "surviving hero could not re-enter their fortress")
check(respawnCharacter.root.CFrame and respawnCharacter.root.CFrame.position==respawnHome,
 "re-entry did not teleport actual new HumanoidRootPart")
local lastFrame=respawnCharacter.root.CFrame
check(Replay.returnToActiveCastle(respawnSession,respawnHero,{root={}},respawnHome)==false,
 "stale CharacterAdded re-entered or teleported a new avatar")
check(respawnCharacter.root.CFrame==lastFrame,"stale avatar changed live player's position")

respawnSession.rules.castles["711"].alive=false
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==false,
 "destroyed personal castle respawned hero")
respawnSession.rules.castles["711"].alive=true
respawnSession.rules.phase="FINISHED"
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==false,
 "finished round accepted re-entry")
respawnSession.rules.phase="ACTIVE"
respawnSession.world.Parent=nil
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==false,
 "destroyed arena accepted re-entry")
respawnSession.world.Parent={}
respawnCharacter.humanoid.Health=0
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==false,
 "dead new avatar could enter castle")
respawnCharacter.humanoid.Health=100
respawnSession.castleLocations["711"]=nil
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==false,
 "owner lacking physical fortress respawned")
respawnSession.castleLocations["711"]={}
respawnHero.Parent=nil
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==false,
 "player who left Roblox server could be teleported")
respawnHero.Parent=playersService
respawnCharacter.root=nil
check(Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)==false,
 "missing physical HumanoidRootPart accepted")
respawnCharacter.root={CFrame=nil}
studio=false
check(not pcall(function()
 Replay.returnToActiveCastle(respawnSession,respawnHero,respawnCharacter,respawnHome)
end),"preview respawn helper callable on published server")
studio=true

print("[EGGRUMBLE ROUND REPLAY NATIVE] PASS",checks,"functional assertions; STUDIO/ANDROID NOT RUN")
