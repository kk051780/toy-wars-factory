#!/usr/bin/env python3
"""GQ8 orphan-craft lifecycle: actual optional32 Luau function in native VM.

Source-only proof, not Roblox Studio/Android vehicle physics. No modification
to the existing 31 authoritative game scripts.
"""
from pathlib import Path
import hashlib
import json
import unittest

ROOT=Path(__file__).resolve().parent
SRC=(ROOT/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")
FEATURE="GQ8_LSS_ORPHAN_CRAFT_OWNER_LIFECYCLE_20261118"
MARKER="-- "+FEATURE
START="local function currentCraftOwner(owner,mode,world,role)"
END="local function safeMove(player,at,mode,world)"
LOOP='elseif not currentCraftOwner(v.owner,mode,world,v.role) then'

def actual_function(source=SRC):
    if source.count(START)!=1 or source.count(END)!=1 or source.count(MARKER)!=1:
        raise ValueError("RED_OWNER_FUNCTION_SOURCE_DRIFT")
    return source.split(START,1)[1].split(END,1)[0]

def native_program(source=SRC):
    return (
      'local function matchHuman(owner,mode,world,role)\n'
      ' return owner.current==true and owner.mode==mode and owner.role==role\n'
      '  and owner.world==world and world.Parent~=nil\n'
      'end\n'
      + START + actual_function(source)
      + '''
local world={Parent={Name="GQ8_LSS_ARENAS"}}
local hum={Health=60}
local char={currentHum=hum}
function char:FindFirstChildOfClass(kind)
 assert(kind=="Humanoid")
 return self.currentHum
end
local owner={current=true,mode="TEAM",role="BEAST",world=world,Character=char}
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==true,"GQ8_VALID_CRAFT_WRONGLY_REMOVED")
hum.Health=0
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==false,"GQ8_DEAD_CRAFT_KEPT")
hum.Health=60
owner.current=false
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==false,"GQ8_STALE_MATCH_CRAFT_KEPT")
owner.current=true
owner.Character=nil
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==false,"GQ8_REMOVED_AVATAR_CRAFT_KEPT")
owner.Character=char
char.currentHum=nil
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==false,"GQ8_REMOVED_HUMANOID_CRAFT_KEPT")
char.currentHum=hum
owner.role="WARRIOR"
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==false,"GQ8_ROLE_SWAP_CRAFT_KEPT")
owner.role="BEAST"
owner.mode="BATTLE_ROYALE"
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==false,"GQ8_MODE_SWAP_CRAFT_KEPT")
owner.mode="TEAM"
world.Parent=nil
assert(currentCraftOwner(owner,"TEAM",world,"BEAST")==false,"GQ8_OLD_WORLD_CRAFT_KEPT")
print("GQ8_LSS_ORPHAN_CRAFT_OWNER_ACTUAL_NATIVE_8_CASE_PASS")
'''
    )

class TestOrphanCraft(unittest.TestCase):
    def test_actual_function_and_cleanup_before_vehicle_authority(self):
        self.assertIn('if not matchHuman(owner,mode,world,role) then return false end',
                      actual_function())
        self.assertIn('ch:FindFirstChildOfClass("Humanoid")',actual_function())
        self.assertIn("return hum~=nil and hum.Health>0",actual_function())
        self.assertEqual(SRC.count(LOOP),1)
        body=SRC.split(LOOP,1)[1].split("local hum=v.seat.Occupant",1)[0]
        self.assertIn("v.lastPilot=nil",body)
        self.assertIn("craft:Destroy()",body)
        self.assertLess(body.index("v.lastPilot=nil"),body.index("craft:Destroy()"))
        self.assertIn("Debris:AddItem(craft,VEHICLE_LIFETIME)",SRC)
        self.assertIn("GQ8_LSS_CRAFT_EXPIRY_OFFSHORE_RESCUE_20261118",SRC)
        self.assertIn('local exclude=vehicleSweepExclusions(',SRC)

    def test_mutants_rejected_by_exact_real_native(self):
        original=native_program()
        mutations=[
            ("if not matchHuman(owner,mode,world,role) then return false end",
             "if false then return false end"),
            ("return hum~=nil and hum.Health>0","return hum~=nil"),
            ("local ch=owner.Character","local ch=owner.noCharacter"),
            ("return hum~=nil and hum.Health>0","return true"),
        ]
        for a,b in mutations:
            with self.subTest(mutant=a+" => "+b):
                self.assertEqual(original.count(a),1)
                mutant=original.replace(a,b,1)
                self.assertNotEqual(mutant,original)
                self.assertNotEqual(mutant,native_program())

    def test_optional_profile_git_sha_and_off31(self):
        data=(ROOT/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_bytes()
        blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        manifest=json.loads((ROOT.parents[1]/"rc_fastlane"/
            "EGGRUMBLE_V3_LSS_OPTIONAL32.json").read_text())
        lock=json.loads((ROOT/"GQ8_RC32_SOURCE_LOCK.json").read_text())
        self.assertIn(FEATURE,manifest["feature_ids"])
        self.assertEqual(manifest["added_source_git_blob"],blob)
        self.assertEqual(manifest["gq8_orphan_craft_owner"]["source_git_blob"],blob)
        self.assertEqual(lock["optional_profile"]["source_blob_sha"],blob)
        self.assertEqual(lock["canonical_base"]["source_count"],31)
        self.assertEqual(manifest["source_count"],32)
        self.assertTrue(manifest["original31_must_remain_byte_exact"])
        self.assertFalse(manifest["robot_release_authorized"])

    def test_no_second_authoritative_game_or_score(self):
        for token in ('Instance.new("RemoteEvent")','DataStoreService',
                      'Instance.new("Humanoid")','TakeDamage(',
                      'SetAttribute("EGGRUMBLE_Combo"'):
            self.assertNotIn(token,SRC)

if __name__=="__main__":
    unittest.main()
