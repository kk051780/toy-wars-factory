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
local health={Health=100}
local root={CFrame=nil}
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
 return if name=="HumanoidRootPart" then self.root else nil
end
function human:LoadCharacter() self.loads+=1 end
check(Replay.resetHuman(human,ret)==nil,"reset should return no value")
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

-- Left players are ignored, and no cross-player mutations occur after removal.
local gone={Parent=nil,UserId=126,attributes={}}
function gone:SetAttribute(key:string,v:any) self.attributes[key]=v end
Replay.resetHuman(gone,ret)
check(next(gone.attributes)==nil,"left player mutated after leaving")
print("[EGGRUMBLE ROUND REPLAY NATIVE] PASS",checks,"functional assertions; STUDIO/ANDROID NOT RUN")
