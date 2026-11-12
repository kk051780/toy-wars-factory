--!strict
-- OWNER-only, disabled-by-default, UNPUBLISHED isolated Studio demo.
-- Changes only decorative eclipse colors, NEVER collisions, gravity, game authority.
local ENABLE_FOUR_RARE_REALMS_DEMO = false
if not ENABLE_FOUR_RARE_REALMS_DEMO then return end

local RunService=game:GetService("RunService")
assert(RunService:IsStudio(),"RARE_WORLD_NO_LIVE_BOOT")
assert(workspace:FindFirstChild("TRAP_RAIDERS_S1")==nil,
    "RARE_WORLD_NO_OFFICIAL_S1_OVERLAP")
local Scene=require(script.Parent.RareRealmScene)
local Cycle=require(script.Parent.RareRealmCycle)
local scene=Scene.build(workspace)
local since=os.clock()
local elapsed=0
local conn
local lastPhase=""
conn=RunService.Heartbeat:Connect(function(dt)
    elapsed+=math.clamp(dt,0,0.25)
    if elapsed < 0.25 then return end
    elapsed=0
    local phase=Cycle.phase(os.clock()-since)
    if phase==lastPhase then return end
    lastPhase=phase
    local sun=scene.eclipsePanels[1]
    local moon=scene.eclipsePanels[2]
    if sun and moon and sun.Parent and moon.Parent then
        sun.Transparency=phase=="SUN" and 0.08 or 0.55
        moon.Transparency=phase=="MOON" and 0.08 or 0.55
    end
    print("P0D_RARE_REALM_STUDIO_DECOR_ONLY phase="..phase..
        " both_eclipse_routes_always_free=true no_npc_ai=true")
end)
game:BindToClose(function()
    if conn then conn:Disconnect() end
    if scene.folder and scene.folder.Parent then scene.folder:Destroy() end
end)
