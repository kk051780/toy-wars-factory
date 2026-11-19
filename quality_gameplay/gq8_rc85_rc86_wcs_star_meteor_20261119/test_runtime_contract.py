#!/usr/bin/env python3
"""Static source contract and negative tests for the Studio-only RC85/86 route
adaptation. Native Luau / Rojo and actual Studio tests are separate gates.
"""
from pathlib import Path
p=Path(__file__).parent
lua=(p/"EGGRUMBLE_LegacyCanyonRoutes.server.luau").read_text(encoding="utf8")
builder=(p/"compose_real67.py").read_text(encoding="utf8")
def assert_once(s):assert lua.count(s)==1,(s,lua.count(s))
for s in [
 "GQ8_RC85_RC86_WCS_STARRY_METEOR_REAL67_20261119",
 'if not RunService:IsStudio() then return end',
 '"WCS_F01_C01,STARRY_PATH_V1,METEOR_FOURTH_V1"',
 '"AlwaysOpenSafeRoute"',
 '"ShortcutGate"',
 '"CrystalCanyonBottom"',
 '"MeteorWarningAnchor"',
 'arena.Destroying:Connect',
 'Workspace.ChildAdded:Connect',
 'while candidate.Parent==lobby and candidate:FindFirstChild("TacticalBattlefield")==nil',
 'os.clock()+14',
 'os.clock()+16',
 'os.clock()+4',
 'os.clock()+7',
 'task.wait(55)',
 'task.wait(5)',
 'local endsAt=os.clock()+22',
 '"GQ8_RC85_WCS_StarMeteor"',
 'p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode',
 'p:GetAttribute("EGGRUMBLE_Eliminated")==true',
 'rp.RespectCanCollide=true',
 'if starOpen and os.clock()>=starUntil and not occupied(-35,9) then',
 'if gateOpen and os.clock()>=gateUntil and not occupied(0,13) then',
 'or (os.clock()>=endsAt and not occupied(-17,9))',
]:assert_once(s)
assert lua.count('block("WestAccessStep_"..i')==1
assert lua.count('block("EastAccessStep_"..i')==1
assert 'for i=1,10 do' in lua # original ten steps, access ten
assert 'for i=1,8 do' in lua # capped meteor <=12
assert 'for i=1,7 do' in lua # original canyon crystal scenery
assert 'not RunService:IsStudio()' in lua
for dangerous in ('game:GetService("DataStoreService")',
                  'game:GetService("MarketplaceService")',
                  'game:GetService("ReplicatedStorage")',
                  'Instance.new("RemoteEvent")',
                  'Humanoid:TakeDamage','DataStore:','SetAsync(',
                  'ProcessReceipt','TeleportService'):
 assert dangerous not in lua,dangerous
for keyword in ("SOURCE66_PRESERVE_", "PARENT65_BYTES_", "NO_DUP_GAME_OR_LOSS",
                "REAL66_PLACE_MISSING","OLD_EXPLORE","STUDIO_ONLY","parent_all66_byte_identical"):
 assert keyword in builder,keyword
assert builder.count('{"$path":REL}')==1
print("GQ8_REAL67_WCS_STAR_METEOR_POLICY_STATIC_AND_NO_EXTRA_GAME_OWNER_PASS")
