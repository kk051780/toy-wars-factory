#!/usr/bin/env python3
"""Adversarial Real63 -> Real65 admission tests (all must fail closed)."""
from __future__ import annotations
import copy
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from gate import (HOST, COMBAT, HUD, POLICY, SWARM, DOMAINS,
                  read_place, require_basic_dodge, verify_successor)

def fixture():
    routes = set(sum(DOMAINS.values(), [])) | {POLICY}
    for i in range(63-len(routes)):
        routes.add("ServerScriptService/TestImmutable_%02d" % i)
    assert len(routes) == 63
    a = {k: ("ModuleScript", b"return true") for k in routes}
    a[HOST] = ("Script", b"startSession()")
    a[COMBAT] = ("ModuleScript",
                 b"EGGRUMBLE_BASIC_ATTACK EGGRUMBLE_DODGE_STEP\n"
                 b"EGGRUMBLE_BasicMobilityPolicy\n"
                 b"executeCoreAction(session,p,role,action,core)")
    a[HUD] = ("LocalScript",
              b"actions.DODGE.Activated:Connect(\n"
              b"EGGRUMBLE_DODGE_STEP EGGRUMBLE_BASIC_ATTACK\n"
              b"local reserved=p.CONTEXT")
    return a

def expect_red(fn, token):
    try:
        fn()
    except ValueError as error:
        assert ("RED_" + token) in str(error), str(error)
    else:
        raise AssertionError("MUTANT_ESCAPED_" + token)

base=fixture()
assert len(require_basic_dodge(base)) == 9
valid=dict(base)
valid[HOST]=("Script",base[HOST][1]+b"\nGQ8_ViralNotification")
valid["StarterPlayer/StarterPlayerScripts/GQ8_ViralCapture"]=("LocalScript",b"return true")
report=verify_successor(base,valid)
assert report["candidate_count"] == 64
assert report["real63_normal_attack_and_dodge_retained"] is True

bad=dict(valid);del bad[POLICY]
expect_red(lambda:verify_successor(base,bad),"REAL63_SOURCE_DROPPED")
bad=dict(valid);bad[HOST]=("ModuleScript",bad[HOST][1])
expect_red(lambda:verify_successor(base,bad),"REAL63_CLASS_DRIFT")
bad=dict(valid);bad[COMBAT]=("ModuleScript",b"Real55 legacy combat only")
expect_red(lambda:verify_successor(base,bad),"LOST_REAL63_BASIC_TOOL")
bad=dict(valid);bad[HUD]=("LocalScript",b"Real55 legacy HUD")
expect_red(lambda:verify_successor(base,bad),"LOST_REAL63_HUD_DODGE_CLICK")
bad=dict(valid);bad[HUD]=("LocalScript",base[HUD][1]+b"\nactions.DODGE.Activated:Connect(")
expect_red(lambda:verify_successor(base,bad),"DUPLICATE_DODGE_TOUCH_CALLBACK")
bad=dict(valid);bad[SWARM]=("ModuleScript",b"hidden HP owner reset")
expect_red(lambda:verify_successor(base,bad),"UNAUTHORIZED_63_OWNER_CHANGE")
bad=dict(valid)
bad["ServerScriptService/EGGRUMBLE_SevenRoleCombat"]=base[COMBAT]
bad["ReplicatedStorage/SecondCombatOwner"]=("ModuleScript",b"server damage")
bad["ServerScriptService/ThirdCombatOwner"]=("ModuleScript",b"server damage")
expect_red(lambda:verify_successor(base,bad),"SUCCESSOR_SOURCE_COUNT")
bad=dict(valid)
del bad["ServerScriptService/EGGRUMBLE_CastleGuardianRuntime"]
expect_red(lambda:require_basic_dodge(bad),"DOMAIN_MISSING_CASTLES")
bad=dict(valid);bad["ServerScriptService/CopyCombat"]=("ModuleScript",b"no authority")
assert verify_successor(base,bad)["candidate_count"] == 65

# Test the same XML reader used for actual Rojo Place source/class evidence.
def construct_element_tree():
    root=ET.Element("roblox")
    for route,(kind,data) in sorted(base.items()):
        parent=root
        for part in route.split("/"):
            existing=next((c for c in parent.findall("Item")
                           if c.findtext("Properties/string[@name='Name']")==part),None)
            if existing is None:
                existing=ET.SubElement(parent,"Item",{"class":kind if part==route.split("/")[-1] else "Folder"})
                props=ET.SubElement(existing,"Properties")
                ET.SubElement(props,"string",{"name":"Name"}).text=part
            parent=existing
        ET.SubElement(parent.find("Properties"),"string",{"name":"Source"}).text=data.decode()
    return root
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/"test.rbxlx"
    ET.ElementTree(construct_element_tree()).write(p,encoding="utf-8",xml_declaration=True)
    parsed=read_place(p)
    assert parsed==base,(set(parsed)^set(base))
print("GQ8_REAL63_SUCCESSOR_NINE_DOMAIN_9_HOST_BASIC_DODGE_ADVERSARIAL_PASS")
