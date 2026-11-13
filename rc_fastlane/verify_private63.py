#!/usr/bin/env python3
"""Read actual cumulative private63 dist + generated Rojo XML to verify a *testable* joined game.

Not an engine test, and never writes official RC/main. Validate the real
Studio-private 63-source candidate's team targeting, runtime feature start
configuration and third-route physical source topology.
"""
from __future__ import annotations
import argparse
import base64
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--dist", type=Path, required=True)
p.add_argument("--place", type=Path, required=True)
a=p.parse_args()

root=a.dist/"src"
game=(root/"server/Game.server.luau").read_text("utf8")
hud=(root/"client/HUD.client.luau").read_text("utf8")
wcs=(root/"server/WCS_CrystalCanyon.server.luau").read_text("utf8")
star=(root/"server/StarfallPath.server.luau").read_text("utf8")
shards=(root/"server/StarShardHunt.server.luau").read_text("utf8")
meteor=(root/"server/MeteorFourth.server.luau").read_text("utf8")
project=json.loads((a.dist/"default.project.json").read_text("utf8"))["tree"]
storage=project["ServerStorage"]
assert storage["$className"]=="ServerStorage"
assert storage["$attributes"]["P0D_RC_ENABLE_WCS_F01_C01"] is True
assert storage["$attributes"]["P0D_RC_ENABLE_SEVEN_JOBS_PVE"] is True
assert storage["$attributes"]["P0D_RC_ENABLE_STARRY_PATH_V1"] is True
assert storage["$attributes"]["P0D_RC_ENABLE_STAR_SHARDS_V1"] is True
assert storage["P0D_ENABLE_METEOR_SHORTCUT_V1"]=={"$className":"BoolValue","$properties":{"Value":True}}
assert storage["P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]=={
    "$className":"BoolValue","$properties":{"Value":True}}, "RELAY_BOOT_NOT_INSTALLED"
assert "if not RunService:IsStudio() then return end" in star
assert 'GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")~=true' in star
assert 'GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")~=true' in wcs
assert game.count("remote.OnServerEvent:Connect(")==1, "DUPLICATE_GAME_REMOTE_AUTHORITY"
assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
assert game.count("local function applyClassicEggRelay(")==1

# Actual owner Game assigns Roblox Team instances, including roster rebalance.
# HUD teammate target must match the same server snapshot team field.
for val in ('if player.Team == teamInstances.RED then return "RED" end',
            'if player.Team == teamInstances.BLUE then return "BLUE" end',
            'player.Team = teamInstances[name]',
            'player.Team = teamInstances[move.to]',
            'team=getTeamName(player)', 'team=getTeamName(target)'):
    assert val in game, ("GAME_TEAM_AUTHORITY_DRIFT",val)
assert hud.count("local function nearestRelayTeammate()")==1
block=hud.split("local function nearestRelayTeammate()",1)[1].split(
    "local function fireClassicEggRelay()",1)[0]
assert re.search(r"other\.Team\.Name\s*==\s*s\.team",block), "HUD_TEAM_TARGET_DRIFT"
assert "horizontal<=8" in block and "math.abs(delta.Y)<=4" in block
assert 'P0D_RC_ENABLE_EGG_RELAY_CLASSIC' in game
assert 'return flag ~= nil and flag:IsA("BoolValue")' in game, "RELAY_NIL_FAIL_OPEN"

# Guard the visually distinct third bridge rather than counting static art.
# Original WCS safe route at local z=+30 cannot disappear.
assert 'makePart("AlwaysOpenSafeRoute"' in wcs
assert 'makePart("WestBank"' in wcs and 'makePart("EastBank"' in wcs
assert 'anchor.CFrame=CFrame.new(0,32,-23)' in wcs
assert 'Vector3.new(0,9,-35)' in star
assert 'for i=1,10 do' in star
assert 'local x=-22.5+(i-1)*5' in star
assert 'makeSwitch("WEST",-34,' in star and 'makeSwitch("EAST",34,' in star
assert 'Vector3.new(x,-0.75,-35)' in star
assert 'OPEN_SECONDS=16' in star and 'REOPEN_COOLDOWN=7' in star
assert 'not occupied()' in star and 'setOpen(false)' in star
assert 'stone.CanCollide=on' in star
assert 'if (root.Position-orb.Position).Magnitude>13 then return end' in star
# New quest owns no Game/Remote/Score/HP/XP or DataStore and only activates
# on the original Starfall Path's physical, currently open stepping stones.
assert 'P0D_StarShardHunt' in shards
assert 'local locations={1,3,5,6,8,10}' in shards
assert 'local TOTAL=6' in shards
assert 'stage:GetAttribute("PathOpen")~=true' in shards
assert 'if not stone.CanCollide then return end' in shards
assert 'ServerStorage:GetAttribute("P0D_RC_ENABLE_STAR_SHARDS_V1")~=true' in shards
assert 'ServerStorage:GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")~=true' in shards
assert 'if not RunService:IsStudio() then return end' in shards
assert 'player:SetAttribute("P0D_StarShardCount",count)' in shards
assert 'Workspace:WaitForChild("P0D_STARRY_PATH",170)' in shards, "SHARDS_RACE_ON_SLOW_WCS_BOOT"
assert 'for _,side in ipairs({"WEST","EAST"}) do' in shards, "MISSING_TWO_BANK_QUEST_HINTS"
assert 'hint.Name="P0DStarShardQuestHint"' in shards, "MISSING_CHILD_VISIBLE_OBJECTIVE"
assert 'label.Text="星の橋で ★6つ を集めよう！' in shards
assert 'light.Name="StarShardGlow"' in shards
assert 'light.Enabled=false' in shards and 'lights[i].Enabled=active' in shards
assert 'prompts[i].Enabled=active' in shards, "INACTIVE_SHARDS_INTERACTIVE"
assert 'local QUIET_SECONDS = 55' in meteor
assert 'local z = (west.Position.Z + east.Position.Z) * 0.5 - 17' in meteor
assert "local function layoutRelayTouch()" in hud
assert 'relayButton.Position=UDim2.new(0,10,1,-127)' in hud
assert 'if complete then showReward(player) end' in shards
for forbidden in ('GetDataStore(', 'UpdateAsync(', 'OnServerEvent:Connect(',
                  'TakeDamage(', 'Instance.new("RemoteEvent")', 'MarketplaceService'):
    assert forbidden not in shards, ("SHARDS_AUTHORITY_CONTRACT", forbidden)
print("P0D_PRIVATE63_GAME_HUD_METEOR_SHARDS_TOUCH_CONTRACT_PASS")

# Parse actual Rojo-generated .rbxlx. Prior builds checked project JSON but
# failed to assert whether its critical BoolValue was *really packaged*.
tree=ET.parse(a.place)
def name_of(item):
    p=item.find("./Properties/string[@name='Name']")
    return None if p is None else p.text
ss=[item for item in tree.iter("Item")
    if item.get("class")=="ServerStorage" and name_of(item)=="ServerStorage"]
assert len(ss)==1, ("PLACE_SERVERSTORAGE_COUNT",len(ss))
vals=[it for it in ss[0].findall("./Item")
      if it.get("class")=="BoolValue" and name_of(it)=="P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]
assert len(vals)==1,("PLACE_RELAY_BOOLVALUE_COUNT",len(vals))
meteorboot=[it for it in ss[0].findall("./Item")
      if it.get("class")=="BoolValue" and name_of(it)=="P0D_ENABLE_METEOR_SHORTCUT_V1"]
assert len(meteorboot)==1,("METEOR_BOOT_BOOLVALUE_COUNT",len(meteorboot))
meteorval=meteorboot[0].find("./Properties/bool[@name='Value']")
assert meteorval is not None and meteorval.text=="true", "METEOR_BOOT_FALSE"
value=vals[0].find("./Properties/bool[@name='Value']")
assert value is not None and value.text=="true",("PLACE_RELAY_BOOLVALUE_NOT_TRUE",None if value is None else value.text)
# AttributeSerialize is a Rojo-rendered ServerStorage binary property.
# Encoding is Roblox-specific; the check ensures all flag names survive serialization.
attr=ss[0].find("./Properties/BinaryString[@name='AttributesSerialize']")
if attr is None:
    attr=ss[0].find("./Properties/binaryString[@name='AttributesSerialize']")
assert attr is not None and attr.text, "PLACE_SERVERSTORAGE_ATTRIBUTES_MISSING"
raw=base64.b64decode("".join(attr.text.split()),validate=True)
for flag in ("P0D_RC_ENABLE_WCS_F01_C01",
             "P0D_RC_ENABLE_SEVEN_JOBS_PVE",
             "P0D_RC_ENABLE_STARRY_PATH_V1",
             "P0D_RC_ENABLE_STAR_SHARDS_V1"):
    assert flag.encode("utf8") in raw,("PLACE_BOOT_ATTRIBUTE_NOT_SERIALIZED",flag)
# Every server Script is singular in the actual serialized Place.
names=[]
for item in tree.iter("Item"):
    if item.get("class")=="Script":
        names.append(name_of(item))
assert names.count("Game")==1, "DUPLICATE_GAME"
assert names.count("StarfallPath")==1, "MISSING_OR_DUPLICATE_STAR"
assert names.count("StarShardHunt")==1, "MISSING_OR_DUPLICATE_SHARDS"
assert names.count("MeteorFourth")==1, "MISSING_OR_DUPLICATE_METEOR"
print("P0D_PRIVATE63_REAL_ROJO_ALL_BOOT_FLAGS_AND_SIX_GAME_SCRIPTS_PASS")
