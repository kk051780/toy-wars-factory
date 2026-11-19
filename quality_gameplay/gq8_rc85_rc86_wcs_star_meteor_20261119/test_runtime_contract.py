#!/usr/bin/env python3
"""Static, source- and owner-based safety check; Native/Rojo & Studio are separate."""
from pathlib import Path
p=Path(__file__).parent
lua=(p/"EGGRUMBLE_LegacyCanyonRoutes.server.luau").read_text(encoding="utf8")
builder=(p/"compose_real67.py").read_text(encoding="utf8")
def once(s:str): assert lua.count(s)==1,(s,lua.count(s))
for marker in [
 "GQ8_RC85_RC86_WCS_METEOR_REUSE_STAR_REAL67_20261119",
 'if not RunService:IsStudio() then return end',
 '"WCS_F01_C01,METEOR_FOURTH_V1"',
 '"ExistingStarSource","GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119"',
 '"ExistingStarStepsReused",10',
 '"UniqueStarPathReused",true',
 '"StarStepsOwned",0',
 '"GQ8_RC86_StarfallPath"',
 '"AlwaysOpenSafeRoute"',
 '"ShortcutGate"',
 '"CrystalCanyonBottom"',
 '"MeteorWarningAnchor"',
 'arena.Destroying:Connect',
 'Workspace.ChildAdded:Connect',
 'while candidate.Parent==lobby and (candidate:FindFirstChild("TacticalBattlefield")==nil',
 'os.clock()+14',
 'os.clock()+4',
 'task.wait(55)',
 'task.wait(5)',
 'local endsAt=os.clock()+22',
 '"GQ8_RC85_WCS_StarMeteor"',
 'p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode',
 'p:GetAttribute("EGGRUMBLE_Eliminated")==true',
 'rp.RespectCanCollide=true',
 'if gateOpen and os.clock()>=gateUntil and not occupied(15,13) then',
 'or (os.clock()>=endsAt and not occupied(-17,9))',
]:once(marker)
assert lua.count('block("WestAccessStep_"..i')==1
assert lua.count('block("EastAccessStep_"..i')==1
assert 'for i=1,6 do' in lua
assert 'for i=1,8 do' in lua
assert 'for i=1,7 do' in lua
assert 'StarSwitch_' not in lua and 'local stones:' not in lua
assert 'local starOpen' not in lua and 'setStar(' not in lua
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
print("GQ8_REAL67_WCS_METEOR_USE_EXISTING_STARRY_BRIDGE_NO_DUPLICATE_PASS")
