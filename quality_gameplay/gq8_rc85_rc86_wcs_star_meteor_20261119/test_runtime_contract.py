#!/usr/bin/env python3
"""Original real Crystal Canyon WCS server safety and no-duplicate owner gate."""
from pathlib import Path
root=Path(__file__).parent
s=(root/"EGGRUMBLE_LegacyCanyonRoutes.server.luau").read_text(encoding="utf8")
b=(root/"compose_real67.py").read_text(encoding="utf8")
for m in [
"GQ8_RC85_WCS_REUSE_STAR_METEOR_REAL67_20261119",
'if not RunService:IsStudio() then return end',
'"LegacyFlags","WCS_F01_C01"',
'"ExistingStarStepsReused",10',
'"ExistingMeteorSegmentsReused",12',
'"StarStepsOwned",0',
'"MeteorOwnedSegments",0',
'"UniqueStarPathReused",true',
'"UniqueMeteorRouteReused",true',
'"GQ8_RC86_StarfallPath"',
'"GQ8_RC86_MeteorShortcut"',
'"AlwaysOpenSafeRoute"',
'"ShortcutBridge"',
'"ShortcutGate"',
'"CrystalCanyonBottom"',
'Workspace.ChildAdded:Connect',
'os.clock()+14','os.clock()+4',
'p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode',
'p:GetAttribute("EGGRUMBLE_Eliminated")==true',
'rp.RespectCanCollide=true',
'if gateOpen and os.clock()>=gateUntil and not occupied(-15,13) then',
'candidate.EGGRUMBLE_REALM_BATTLE_CORE:FindFirstChild("GQ8_RC86_StarfallPath")',
'candidate.EGGRUMBLE_REALM_BATTLE_CORE:FindFirstChild("GQ8_RC86_MeteorShortcut")',
]: assert s.count(m)==1,(m,s.count(m))
assert 'for i=1,6 do' in s and 'for i=1,7 do' in s
assert s.count('block("WestAccessStep_"..i')==1
assert s.count('block("EastAccessStep_"..i')==1
for duplicate in ('StarSwitch_','local starOpen','setStar(','MeteorBridge_',
                  'local meteor:','setMeteor(','task.wait(55)',
                  'Instance.new("RemoteEvent")','DataStoreService','MarketplaceService',
                  'ProcessReceipt','TakeDamage(','SetAsync('):
 assert duplicate not in s,duplicate
for term in ('SOURCE66_PRESERVE_','PARENT65_BYTES_','NO_DUP_GAME_OR_LOSS',
'REQUIRE_ALREADY_ADOPTED_STAR_FROM_879','REQUIRE_ALREADY_ADOPTED_METEOR_FROM_884',
'NO_OVERWRITE','OLD_EXPLORE','STUDIO_ONLY','parent_all66_byte_identical'):
 assert term in b,term
assert b.count('{"$path":REL}')==1
print("GQ8_RC85_WCS_ONLY_NO_DOUBLE_STAR_OR_METEOR_PASS")
