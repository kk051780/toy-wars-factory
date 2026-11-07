-- Test the actual read-only Studio Command Bar script with deterministic Lua mocks.
-- This is NOT Studio; its purpose is to ensure no skipped-mode is reported as fully verified.
local smoke = 'tools/studio_readonly_smoke_v2.lua'
local function object(kind, children, props)
    local o=props or {}
    o.ClassName=kind
    o._children=children or {}
    function o:IsA(className) return self.ClassName==className or (className=='BasePart' and self.ClassName=='Part') end
    function o:FindFirstChild(name) return self._children[name] end
    return o
end
local B={PLAYABLE_IDS={'pon','guardon','tankuru','curebo'}}
function B.isUnit(id) return id=='pon' or id=='guardon' or id=='tankuru' or id=='curebo' end
function B.productionInterval(lv) if lv<1 or lv>6 then return nil end return 3-.3*(lv-1) end
function B.junkThreat(wave)
    if wave==1 then return {hp=38,damage=6} end
    if wave==11 then return {hp=46,damage=7} end
    if wave==50 then return {hp=102,damage=14} end
    return {hp=38,damage=6}
end
function B.junkBoss(wave) if wave%10~=0 then return nil end return wave==50 and {hp=306,damage=18,reward=140} or {hp=114,damage=10,reward=60} end
function B.canBuy(id,coins,count) return count<20 and B.isUnit(id) end
function B.buy(id,coins,count) if not B.isUnit(id) or coins<10 then return nil end return coins-10 end
local function run(phase,options)
    options=options or {}
    local logs={}
    local function log(prefix,...) local xs={...};for i=1,#xs do xs[i]=tostring(xs[i]) end;logs[#logs+1]=prefix..table.concat(xs,' ') end
    local mod=object('ModuleScript')
    local replicated=object('ReplicatedStorage',{ToyWarsBalance=mod,ToyWarsSelectUnit=object('RemoteEvent')})
    local servers=object('ServerScriptService', options.missingServerScripts and {} or {ToyWarsServer=object('Script'),ToyWarsSmokeTest=object('Script')})
    local starter=object('StarterPlayer',{StarterPlayerScripts=object('StarterPlayerScripts',{ToyWarsHUD=object('LocalScript')})})
    local world=object('Folder',{ToyWarsLobbySpawn=object('SpawnLocation')})
    local workshop=object('Folder',{ToyPrinter=object('Part',{Caption=object('BillboardGui',{TextLabel=object('TextLabel',nil,{Text='TOY PRINTER\\n3.0s / toy'})})})})
    world._children.Workshop_101=workshop
    local statusChildren={}
    for _,n in ipairs({'FactoryLevel','BaseHP','Allies','Enemies','SelectedToy','RoundOutcome'}) do
      statusChildren[n]=object('IntValue')
    end
    statusChildren.FactoryLevel.Value=1
    local player=object('Player',{
      ToyWarsStatus=object('Folder',statusChildren),
      leaderstats=object('Folder',{Coins=object('IntValue'),Wave=object('IntValue'),Defeated=object('IntValue')}),
      PlayerGui=object('PlayerGui',{ToyWarsHUD=object('ScreenGui',{StatusPanel=object('Frame'),SelectToy=object('Frame')})})
    },{UserId=101})
    if options.missingWorld then world=nil end
    if options.invalidPrinterLabel then
      workshop:FindFirstChild('ToyPrinter'):FindFirstChild('Caption'):FindFirstChild('TextLabel').Text='incorrect speed'
    end
    local outsider=object('Player',{}, {UserId=202})
    local service={
      RunService={IsStudio=function() return phase~='NON_STUDIO' end,IsRunning=function() return phase~='EDIT' end,IsClient=function() return phase=='PLAY_CLIENT' end},
      ReplicatedStorage=replicated,
      -- A real Roblox client cannot inspect ServerScriptService descendants.
      ServerScriptService=phase=='PLAY_CLIENT' and object('ServerScriptService') or servers,
      StarterPlayer=starter,
      Players={LocalPlayer=(options.noPlayer and nil or player),GetPlayers=function() return options.noPlayer and {} or (options.foreignFirst and {outsider,player} or {player}) end}
    }
    local env=setmetatable({
        game={GetService=function(_,name) return assert(service[name],name) end},
        workspace=object('Workspace',{ToyWarsWorld=world}),
        require=function(v) assert(v==mod);return B end,
        print=function(...) return log('',...) end,
        warn=function(...) return log('WARN ',...) end,
    },{__index=_G})
    local fn,err=loadfile(smoke,'t',env);assert(fn,err)
    fn()
    return table.concat(logs,'\n')
end
local count=0
local function test(name,fn)
    local ok,msg=pcall(fn)
    if not ok then error('TEST FAIL '..name..' '..tostring(msg)) end
    count=count+1
    print('PASS '..name)
end
local function has(out,needle) return out:find(needle,1,true)~=nil end
test('Edit mode is PARTIAL, never full PASS',function()
    local o=run('EDIT')
    assert(has(o,'mode=EDIT') and has(o,'failures=0') and has(o,'TWF_STUDIO_SMOKE_PARTIAL'))
    assert(not has(o,'TWF_STUDIO_SMOKE_LOCAL_CHECKS_PASS'))
end)
test('server Play without client HUD check is PARTIAL',function()
    local o=run('PLAY_SERVER')
    assert(has(o,'mode=PLAY') and has(o,'TWF_STUDIO_SMOKE_PARTIAL'))
end)
test('client Play skips server-only scripts without false FAIL',function()
    local o=run('PLAY_CLIENT')
    assert(has(o,'failures=0') and has(o,'TWF_SMOKE_SKIP: Server-only source scripts'))
    assert(has(o,'TWF_STUDIO_SMOKE_PARTIAL') and not has(o,'TWF_STUDIO_SMOKE_INCOMPLETE'))
    assert(not has(o,'TWF_STUDIO_SMOKE_LOCAL_CHECKS_PASS'))
end)
test('server Play still tests actual private server scripts',function()
    local o=run('PLAY_SERVER')
    assert(has(o,'TWF_SMOKE_PASS: ToyWarsServer is Script'))
    assert(has(o,'TWF_SMOKE_PASS: ToyWarsSmokeTest is Script'))
end)
test('client checks LocalPlayer instead of an unrelated first player',function()
    local o=run('PLAY_CLIENT',{foreignFirst=true})
    assert(has(o,'TWF_SMOKE_PASS: Player owns server-authoritative factory status'))
    assert(has(o,'TWF_SMOKE_PASS: Local player has responsive HUD instance'))
    assert(has(o,'failures=0'))
end)
test('missing server script in server Play is a real failure',function()
    local o=run('PLAY_SERVER',{missingServerScripts=true})
    assert(has(o,'TWF_SMOKE_FAIL: ToyWarsServer is Script'))
    assert(has(o,'TWF_STUDIO_SMOKE_INCOMPLETE'))
end)
test('printer speed label mismatch fails in Play',function()
    local o=run('PLAY_CLIENT',{invalidPrinterLabel=true})
    assert(has(o,'TWF_SMOKE_FAIL: 3D workshop printer displays the server'))
    assert(has(o,'TWF_STUDIO_SMOKE_INCOMPLETE'))
end)
test('missing 3D world reports INCOMPLETE not PASS',function()
    local o=run('PLAY_CLIENT',{missingWorld=true})
    assert(has(o,'TWF_STUDIO_SMOKE_INCOMPLETE') and not has(o,'TWF_STUDIO_SMOKE_LOCAL_CHECKS_PASS'))
end)
test('no player in Play stays PARTIAL',function()
    local o=run('PLAY_CLIENT',{noPlayer=true})
    assert(has(o,'TWF_STUDIO_SMOKE_PARTIAL') and not has(o,'TWF_STUDIO_SMOKE_LOCAL_CHECKS_PASS'))
end)
test('non-Studio execution blocks before checks',function()
    local o=run('NON_STUDIO')
    assert(has(o,'TWF_SMOKE_BLOCKED') and not has(o,'TWF_STUDIO_SMOKE_RESULT'))
end)
print('SUMMARY '..count..' / '..count..' PASS (native Lua mocks; not Roblox Studio)')
