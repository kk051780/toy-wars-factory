-- PREP QA: native executable test of the ACTUAL extracted runtime scanner.
-- Roblox engine, live physics, networking, audio and Studio remain NOT_TESTED.
local cases=0
local function check(ok,label) assert(ok,label); cases+=1 end
local enabled=true
local arena={}
function arena:FindFirstChild(name)
    if name~="RED_CASTLE" and name~="BLUE_CASTLE" then return nil end
    local castle={}
    function castle:FindFirstChild(eggName)
        if eggName~="RED_EGG" and eggName~="BLUE_EGG" then return nil end
        local egg={}
        function egg:FindFirstChildOfClass(kind)
            if kind=="ProximityPrompt" then return {Enabled=enabled} end
            return nil
        end
        return egg
    end
    return castle
end
local active={folder={Parent=arena}}
local RED={Name="RED"};local BLUE={Name="BLUE"};local NEUTRAL={Name="NONE"}
local players={}
local Players={}
function Players:GetPlayers() return players end
local function pos(x)
    return setmetatable({X=x,Y=0,Z=0},{
        __sub=function(a,b) return {Magnitude=math.abs(a.X-b.X)} end
    })
end
local function person(name,team,x,alive)
    local p={Name=name,Team=team,UserId=#players+1}
    p.Character={}
    p._root={Position=pos(x)}
    p._alive=alive~=false
    table.insert(players,p)
    return p
end
local function aliveRoot(p)
    if p._alive then return p._root else return nil end
end
local blocked=false;local rays=0
local Workspace={}
function Workspace:Raycast(from,delta,params)
    rays+=1
    if blocked then return {Instance="WALL"} end
    return nil
end
local RaycastParams={}
function RaycastParams.new() return {} end
local Enum={RaycastFilterType={Exclude="Exclude"}}
-- ACTUAL_SCANNER_HERE
local p=person("Red",RED,0)
local enemy=person("Blue",BLUE,7)
local observed, root, status=visibleEnemy(p,{remaining=3})
check(observed==enemy and root==enemy._root,"VISIBLE_OPPONENT")
check(rays==1,"ONE_REAL_RAY")
enabled=false
observed,root,status=visibleEnemy(p,{remaining=3})
check(observed==nil and rays==1,"LOBBY_FAIL_CLOSED")
enabled=true
players={p}
for i=1,20 do person("Friendly"..i,RED,70) end
table.insert(players,enemy)
observed,root,status=visibleEnemy(p,{remaining=3})
check(observed==enemy,"FRIENDLIES_NOT_COUNTED")
blocked=true
rays=0
observed,root,status=visibleEnemy(p,{remaining=3})
check(observed==nil and status=="COMPLETE","BLOCKED_LOS_IS_NOT_ENEMY")
check(rays==1,"LOS_FILTER_RAN")
players={p}
for i=1,15 do person("Opponent"..i,BLUE,8) end
rays=0
observed,root,status=visibleEnemy(p,{remaining=3})
check(observed==nil and status=="INCOMPLETE","RAY_EXHAUSTION_IS_UNKNOWN")
check(rays==3,"EXACT_THREE_RAYS")
rays=0
observed,root,status=visibleEnemy(p,{remaining=40})
check(observed==nil and status=="INCOMPLETE","TWELVE_ELIGIBLE_CANDIDATES_CAPPED")
check(rays==12,"EXACT_TWELVE_CANDIDATES")
-- Exercise the ACTUAL automatic pass with the rotating observer start.
blocked=false
players={p,enemy}
local lastAlertTarget={}
local scanCursor=1
local function speak(recipient,speaker,mode,whichArena,target,targetRoot)
    return "ENEMY_ALERT"
end
local inspected={}
local actual=visibleEnemy
visibleEnemy=function(recipient, quota)
    table.insert(inspected,recipient.Name)
    return actual(recipient,quota)
end
-- ACTUAL_PASS_HERE
autoPass()
check(inspected[1]=="Red","ROUND_ROBIN_FIRST_RED")
inspected={}
autoPass()
check(inspected[1]=="Blue","ROUND_ROBIN_NEXT_BLUE")
print("P0D_NPC_REAL_RUNTIME_SCANNER_PASS",cases)
