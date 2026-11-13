#!/usr/bin/env python3
"""Strict actual complete H1 private Rojo place source identity and fail-closed source checks."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
OWN=Path(__file__).resolve().parents[1]
PROJECT=OWN/"dist/TRAP_RAIDERS_H1_JOY_STUDIO_ONLY"
p=argparse.ArgumentParser()
p.add_argument("--place",required=True)
a=p.parse_args()
src={p.relative_to(PROJECT/"src").as_posix():p.read_text(encoding="utf8")
     for p in sorted((PROJECT/"src").rglob("*.luau"))}
assert len(src)==30,len(src)
receipt=json.loads((PROJECT/"SOURCE_RECEIPT.json").read_text(encoding="utf8"))
assert receipt["script_total"]==30 and receipt["exact_base_28_files"]==28
assert len(receipt["original_all_28_gitblobs"])==28
place=Path(a.place)
root=ET.parse(place).getroot()
embedded=[];types=collections.Counter()
for obj in root.iter("Item"):
    kind=obj.attrib.get("class")
    if kind not in ("Script","LocalScript","ModuleScript"):continue
    props=obj.find("Properties")
    if props is None:continue
    source=next((c.text or "" for c in props if c.attrib.get("name")=="Source"),None)
    if source is None:continue
    embedded.append(source)
    types[kind]+=1
assert types=={"Script":2,"LocalScript":5,"ModuleScript":23},types
assert collections.Counter(embedded)==collections.Counter(src.values()),"Rojo source byte mismatch"
assert len(embedded)==30
server=src["server/Game.server.luau"]
client=src["client/EggJoy.client.luau"]
pure=src["client/EggJoyRules.luau"]
assert server.count('remote.Name = "TrapRaidersS1Remote"')==1
assert src["server/H1FunWorld.server.luau"].count('RunService:IsStudio()')>=1
assert "if not RunService:IsStudio() then return end" in client
assert "OnClientEvent:Connect" in client
for forbidden in ('FireServer','Instance.new("RemoteEvent")','MarketplaceService',
                  'DataStoreService','TakeDamage','Robux'):
    assert forbidden not in client and forbidden not in pure,forbidden
for anchor in ('snap.updateId <= previous.updateId','previous.serial ~= current.serial',
               'current.scores[current.team] > previous.scores[current.team]',
               'previous.carrying == "" and current.carrying ~= ""'):
    assert anchor in pure,anchor
for prohibited in ('Instance.new("Part")','Instance.new("Sound")','task.spawn(function() while'):
    assert prohibited not in client,prohibited
for name in receipt["original_all_28_gitblobs"]:
    content=src[name].encode("utf8")
    ident=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
    assert ident==receipt["original_all_28_gitblobs"][name],name
print("P0D_EGG_JOY_ROJO_TRUE_30_SOURCE_BYTE_EXACT_ORIGINAL28_CLIENT2_PASS")
print("P0D_EGG_JOY_ROJO_FILE_BYTES",place.stat().st_size)
print("P0D_EGG_JOY_ROJO_SHA256",hashlib.sha256(place.read_bytes()).hexdigest())
print("ROBOLOX_STUDIO_OWNER_FUN=NOT_TESTED")
