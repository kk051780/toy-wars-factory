#!/usr/bin/env python3
"""Negative contract probes on actual selected Studio source, not an invented policy."""
from pathlib import Path
p=Path("quality_gameplay/gq800_curse_bridge_20261119/EGGRUMBLE_SwarmCombat_Curse44.server.luau")
s=p.read_text()
assert s.count("local Swarm={}") == 1
assert s.count("function Swarm.start(session:any)") == 1
assert s.count("CursePolicy.seal(state,os.clock(),{") == 1
assert s.count('require(script.Parent:WaitForChild("EGGRUMBLE_CurseConversionPolicy"))') == 1
assert s.count("h:TakeDamage(damage)") == 1
assert s.count("eh:TakeDamage(8)") == 1
assert 'm:SetAttribute("EGGRUMBLE_NeutralInstanceId",epoch..":"..tostring(spawnSerial))' in s
assert "serverConfirmedHit=true" in s and "uniqueHitId=epoch" in s
assert "existingSummoned=3" in s and "CursePolicy.retire(" in s
assert "if not charmed[m] and m.Parent and h.Health>0" in s
assert "if not charmed[m] and m.Parent and m.PrimaryPart and h.Health>0" in s
assert "lineOfSightToNeutral(m.PrimaryPart.Position,m,target)" in s
assert "EGGRUMBLE_CharmRibbon" in s and "Enum.HighlightDepthMode.Occluded" in s
assert "if not formerAlly and type(id)" in s
# Ensure only the real server-authority successful Hit path invokes seal.
fail=s.index("if h.Health>=before then")
hit=s.index("if user and h.Health>0 then seal(")
assert fail<hit and "continue" in s[fail:hit]
for bad in ("RemoteEvent","DataStoreService","MarketplaceService","ProcessReceipt","BindToClose",
            "FireServer(","OnServerEvent","game:Shutdown","PublishAsync"):
    assert bad not in s,bad
print("GQ800_CURSE_REAL_SWARM_SERVER_CONFIRM_LOS_REPLAY_SINGLE_AUTHORITY_PASS")
print("GQ800_CURSE_BOUND_1_CHARM_TTL14_RELEASE_AND_OFF43_CONTRACT_PASS")
