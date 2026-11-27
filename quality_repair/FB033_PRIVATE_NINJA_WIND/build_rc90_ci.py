#!/usr/bin/env python3
"""FB033: exact real RC89->RC90 patch for owner-opted private Ninja wind.

Source-select ONLY existing authoritative Game. Do not touch official/main,
do not overwrite the unavailable parallel #476 5-source latest Game/HUD.
"""
from pathlib import Path
from lxml import etree
import hashlib,json,sys

PARENT_SHA="088f06d11c543c6d62fbc70359adad9a49dc2c12a8b9ca6835fed1adb79e4d2d"
EXPECTED_SHA="4302da965a6a29fe8dc472cd97691a0dbfffa9f713dee556323afe73941941bc"

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def blob(s):
    b=s.encode("utf8")
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def once(s,a,b):
    assert s.count(a)==1,"FB033_SOURCE_ANCHOR_DRIFT"
    return s.replace(a,b,1)

def apply(s):
    s=once(s,
        '    local selectedJob = RunService:IsStudio() and sevenJobSelected[player] == true',
        '''    -- FB033: The client exposes Assassin wind in the owner-opted-in private
    -- PvE trial as well as Studio. Mirror the same authenticated server flags
    -- so an acknowledged Ninja can actually use the shown R/touch button.
    -- Public servers stay OFF; the packet never chooses its own role.
    local privateTrial = privateHordeTrialAllowed()
    local selectedJob = (RunService:IsStudio() or privateTrial)
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE") ~= false
        and sevenJobSelected[player] == true''')
    s=once(s,
        '''    if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true
        or RunService:IsStudio() then''',
        '''    -- A server-acknowledged private Ninja receives the same physically proven
    -- wide-field wind corridor as Studio; legacy RAIDER behavior stays intact.
    if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true
        or RunService:IsStudio() or selectedJob then''')
    s=once(s,
        '''        if RunService:IsStudio() then
            -- Ground proof in real server geometry, not a client-sent coordinate.''',
        '''        if RunService:IsStudio() or selectedJob then
            -- Ground proof in real server geometry, not a client-sent coordinate.''')
    assert s.count('remote.OnServerEvent:Connect(')==1
    assert s.count('lastWind[player] = now')==1
    return s

def scripts(t):
    rows={}
    for i in t.xpath('//Item'):
        p=i.find('Properties')
        if p is None:continue
        n=p.find('string[@name="Name"]')
        src=next((z for z in p if z.get("name")=="Source"),None)
        if n is not None and src is not None:
            assert n.text not in rows
            rows[n.text]=(i.attrib["class"],src)
    assert len(rows)==86,len(rows)
    return rows

def run(parent,output):
    parent,output=Path(parent),Path(output)
    assert sha(parent)==PARENT_SHA and parent.stat().st_size==847911,"PINNED_PARENT_ONLY"
    assert not output.exists()
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    t=etree.parse(str(parent),parser)
    rows=scripts(t)
    original={n:(c,blob(el.text or "")) for n,(c,el) in rows.items()}
    assert original["Game"]==("Script","b1a93d38cdffb0cd37871e35e218ac6925ac8fa3")
    assert original["StagePickupLoot"][1]=="450ba944550c3bc44ce04dc9b91da943090598d9"
    assert "UndeadSquad" in rows and "TrapperWarpService" in rows
    rows["Game"][1].text=apply(rows["Game"][1].text or "")
    after={n:(c,blob(el.text or "")) for n,(c,el) in rows.items()}
    assert [n for n in original if original[n]!=after[n]]==["Game"]
    t.write(str(output),encoding="utf-8",xml_declaration=False,pretty_print=True)
    assert {n:(c,blob(el.text or "")) for n,(c,el) in scripts(etree.parse(str(output),parser)).items()}==after
    assert output.stat().st_size==848560
    assert sha(output)==EXPECTED_SHA,(sha(output),EXPECTED_SHA)
    return {"sha256":EXPECTED_SHA,"bytes":848560,"script_count":86,"changed":["Game"],"unchanged":85,
        "native":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN","official_rc":False}

if __name__=="__main__":
    assert len(sys.argv)==3,"usage: builder PARENT_RC89.rbxlx OUTPUT_RC90.rbxlx"
    print(json.dumps(run(*sys.argv[1:]),indent=2))
