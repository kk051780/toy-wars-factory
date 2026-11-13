#!/usr/bin/env python3
"""Verify real full 32-source Rojo .rbxlx unchanged #270 game + actual D18 local landmarks."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
OWN=Path(__file__).resolve().parents[1]
DST=OWN/"dist/TRAP_RAIDERS_H1_D18_WORLD_DISCOVERY_STUDIO_ONLY"
p=argparse.ArgumentParser();p.add_argument("--place",required=True);a=p.parse_args()
receipt=json.loads((DST/"SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
sources={p.relative_to(DST/"src").as_posix():p.read_text(encoding="utf-8")
         for p in (DST/"src").rglob("*.luau")}
assert len(sources)==32
assert len(receipt["original_game_sources_sha1"])==30
assert set(sources)-set(receipt["original_game_sources_sha1"])=={
    "client/D18Batch10Catalog.luau","client/D18PairRouteDiscover.client.luau"}
for name,sha in receipt["original_game_sources_sha1"].items():
    data=sources[name].encode("utf-8")
    blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    assert blob==sha,("BASE_GAME_CHANGED",name)
tree=ET.parse(a.place).getroot()
embedded=[];types=collections.Counter()
for item in tree.iter("Item"):
    kind=item.attrib.get("class")
    if kind not in {"Script","LocalScript","ModuleScript"}:continue
    props=item.find("Properties")
    if props is None:continue
    src=next((n for n in props if n.attrib.get("name")=="Source"),None)
    if src is None:continue
    embedded.append(src.text or "")
    types[kind]+=1
assert types=={"Script":2,"LocalScript":6,"ModuleScript":24},types
assert len(embedded)==32
assert collections.Counter(embedded)==collections.Counter(sources.values()),"REAL_ROJO_SOURCE_MISMATCH"
new=sources["client/D18PairRouteDiscover.client.luau"]
cat=sources["client/D18Batch10Catalog.luau"]
assert "local DATA=" in cat and "TRCA-BE-108" in cat and "TRCA-TR-090" in cat
assert new.count("TRCA-BE-108")==1 and new.count("TRCA-TR-090")==1
for expected in ('RunService:IsStudio()', 'MAX_NEARBY_MODELS=2',
                 'CanCollide=false','CanTouch=false','CanQuery=false',
                 'ProximityPrompt','local discovered={}','discoveredCount+=1'):
    assert expected in new,expected
assert sources["server/Game.server.luau"].count('remote.Name = "TrapRaidersS1Remote"')==1
for banned in ('FireServer','DataStoreService','MarketplaceService','RemoteEvent',
               'SetAsync','GetAsync','TakeDamage','ProcessReceipt','Humanoid.WalkSpeed'):
    for name in ("client/D18Batch10Catalog.luau","client/D18PairRouteDiscover.client.luau"):
        assert banned not in sources[name],(name,banned)
assert receipt["game_server_mutated"] is False
assert receipt["gameplay_scoring_changed"] is False
assert receipt["multiegg_feature_integrated"] is False
print("P0D_H1_D18_ACTUAL_FULL_ROJO_32_SOURCE_BYTE_EXACT_GAME30_UNCHANGED_PASS")
print("D18_TWO_ORIGINAL_ASSETS_BOTH_TEAM_LOCAL_SAFE_2_INSTANCE_CAP_PASS")
print("PLACE_SHA256",hashlib.sha256(Path(a.place).read_bytes()).hexdigest())
print("PLACE_BYTES",Path(a.place).stat().st_size)
print("ACTUAL_ROBLOX_STUDIO_OWNER_FUN_NOT_TESTED")
