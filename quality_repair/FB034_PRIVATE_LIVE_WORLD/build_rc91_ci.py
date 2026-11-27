#!/usr/bin/env python3
"""FB034 RC90 -> RC91 real Place. Exactly one owner-private 3D castle world gate."""
from pathlib import Path
from lxml import etree
import sys,hashlib,json

PARENT="4302da965a6a29fe8dc472cd97691a0dbfffa9f713dee556323afe73941941bc"
EXPECTED="399297da767e765fbc583a5e9a5cc6f2b7780ad1d623921d08d8010bde57e5d3"
TARGET="Owner361CastleBattlefield"
OLD_BLOB="3599f7a86be2956d2ecf4f14267dfbb73f8f1074"
NEW_BLOB="fc67108987b931c6b69756bc4ce6cc9c89501f4e"
OLD='local RunService = game:GetService("RunService")\nif not RunService:IsStudio() then return end'
NEW='''local RunService = game:GetService("RunService")
-- FB034: The actual battle map/castles must not disappear when an OWNER runs
-- their explicitly opted-in private Live-Horde trial outside Studio.
-- Public servers NEVER get changed collision, field dimensions or world art.
-- Keep the SAME server-owned opt-in as Game.privateHordeTrialAllowed().
local fb034OwnerPrivateWorldAllowed = game.PrivateServerId ~= ""
    and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true
if not (RunService:IsStudio() or fb034OwnerPrivateWorldAllowed) then return end'''
END_OLD='print("OWNER361_CASTLE_WORLD_PRIVATE_STUDIO_ADDED_NO_GAME_AUTHORITY")'
END_NEW='''-- Read-only runtime evidence, stamped after all physical world pieces exist.
-- Game's original objective hitboxes, score and Remote are untouched.
world:SetAttribute("P0D_FB034_LIVE_CASTLE_WORLD_READY", true)
print("OWNER361_CASTLE_WORLD_STUDIO_OR_PRIVATE_TRIAL_ADDED_NO_GAME_AUTHORITY")'''

def sha(b): return hashlib.sha256(b).hexdigest()
def blob(s):
    b=s.encode('utf8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def only(s,a,b):
    if s.count(a)!=1:raise AssertionError("FB034_ANCHOR_DRIFT")
    return s.replace(a,b,1)
def scripts(tree):
    out={}
    def walk(item,parents=()):
        prop=item.find("Properties")
        name=prop.findtext('string[@name="Name"]') if prop is not None else None
        src=next((n for n in prop if n.get("name")=="Source"),None) if prop is not None else None
        current=parents+((name,) if name else ())
        if src is not None:
            key='/'.join(current)
            assert len(current)>=3 and key not in out
            out[key]=(item.get("class"),src)
        for i in item.findall("Item"):walk(i,current)
    for i in tree.getroot().findall("Item"):walk(i)
    assert len(out)==86
    return out

def build(parent,out):
    parent,out=Path(parent),Path(out)
    data=parent.read_bytes()
    assert len(data)==848560 and sha(data)==PARENT,"BAD_RC90_PARENT_SHA"
    assert not out.exists() and parent!=out,"NEVER_OVERWRITE_SOURCE"
    t=etree.ElementTree(etree.fromstring(data,etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)))
    d=scripts(t)
    key='ServerScriptService/TrapRaidersS1/'+TARGET
    assert key in d and d[key][0]=='Script'
    originals={n:(c,blob(s.text or '')) for n,(c,s) in d.items()}
    assert originals[key][1]==OLD_BLOB
    assert originals['ServerScriptService/TrapRaidersS1/Game'][1]=='a87ee607e5e6a44bff0513442368ce4913c40a75'
    src=d[key][1].text or ''
    src=only(src,OLD,NEW)
    src=only(src,END_OLD,END_NEW)
    assert 'grass.Size = Vector3.new(370, 4, 294)' in src
    assert src.count('P0D_FB034_LIVE_CASTLE_WORLD_READY')==1
    d[key][1].text=src
    after={n:(c,blob(s.text or '')) for n,(c,s) in d.items()}
    assert [n for n in originals if originals[n]!=after[n]]==[key]
    assert after[key][1]==NEW_BLOB
    t.write(str(out),encoding='utf-8',xml_declaration=False,pretty_print=True)
    assert out.stat().st_size==849249 and sha(out.read_bytes())==EXPECTED,"RC91_BINARY_MISMATCH"
    o=scripts(etree.parse(str(out),etree.XMLParser(resolve_entities=False,no_network=True)))
    assert {n:(c,blob(s.text or '')) for n,(c,s) in o.items()}==after
    return dict(parent_sha256=PARENT,output_sha256=EXPECTED,bytes=849249,
        changed=[key],unchanged=85,sources=86,official_rc_written=False,
        studio_runtime='NOT_RUN',android='NOT_RUN',owner='NOT_APPROVED')
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: builder RC90.rbxlx RC91.rbxlx')
    print(json.dumps(build(sys.argv[1],sys.argv[2]),indent=2))
