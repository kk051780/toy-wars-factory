#!/usr/bin/env python3
"""Reject missing/extra H2 lab source, an extra Game/Remote or score spoof entrypoint."""
import argparse,collections,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument("--place",required=True)
a=p.parse_args()
original={}
for file in sorted((ROOT/"src").rglob("*.luau")):
    original[file.name]=file.read_text(encoding="utf8")
assert len(original)==3 and len(set(original))==3
place=Path(a.place)
assert place.is_file() and place.stat().st_size>1000
item_sources={}
kinds=collections.Counter()
for item in ET.parse(place).iter("Item"):
    kind=item.attrib.get("class")
    if kind not in {"Script","LocalScript","ModuleScript"}:continue
    properties=item.find("Properties")
    assert properties is not None
    name=next((x.text for x in properties if x.attrib.get("name")=="Name"),None)
    source=next((x.text or "" for x in properties if x.attrib.get("name")=="Source"),None)
    assert name is not None and source is not None
    assert name not in item_sources,"DUPLICATE_NAME"
    item_sources[name]=source;kinds[kind]+=1
assert kinds=={"Script":1,"LocalScript":1,"ModuleScript":1},kinds
assert collections.Counter(item_sources.values())==collections.Counter(original.values())
rules=original["MultiEggRules.luau"]
server=original["MultiEggLab.server.luau"]
hud=original["MultiEggHUD.client.luau"]
for anchor in ('R1="RED"','R2="RED"','B1="BLUE"','B2="BLUE"','N1="NEUTRAL"',
               'Rules.LENGTH_SECONDS = 240','m.carryByPlayer[playerId] ~= nil',
               'bonus=if egg.owner == "NEUTRAL" then 10 else 12',
               'egg.bonusClaimed[playerTeam]=true','function Rules.assertConserved'):
    assert anchor in rules,anchor
for anchor in ('Rules.pickup(match,id,holder,side)',
               'Rules.deposit(match,holder,name)','Rules.drop(match,holder)',
               'Rules.advance(match,1)','if not RunService:IsStudio() then return end',
               'pu.Triggered:Connect','MaxActivationDistance=9','HumanoidRootPart'):
    assert anchor in server,anchor
assert 'OnServerEvent' not in server
assert 'FireServer' not in hud
assert 'RunService:IsStudio()' in hud
for name,code in original.items():
    for unsafe in ('MarketplaceService','DataStoreService','Instance.new("RemoteEvent")',
                   'TakeDamage','Robux','GamePass'):
        assert unsafe not in code,(name,unsafe)
print("P0D_H2_FIVE_EGG_STUDIO_LAB_ACTUAL_ROJO_XML_3_OF_3_EXACT_AUTHORITY_SAFETY_PASS")
print("STUDIO_LAB_PRIVATE_PLACE_SHA256",hashlib.sha256(place.read_bytes()).hexdigest())
print("STUDIO_LAB_PRIVATE_PLACE_BYTES",place.stat().st_size)
print("OWNER_H1_REAL_GAME_MIGRATION=NOT_DONE; STUDIO_PLAY_FPS_FUN=NOT_TESTED")
