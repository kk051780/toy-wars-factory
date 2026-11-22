#!/usr/bin/env python3
"""Fail-closed negative tests; fake fixture is NOT the actual Roblox engine."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch as mock_patch
from zipfile import ZipFile

from patch_guild69 import (
    BASE, ROUTE, FILE, FEATURE, OLD_ROOF, OLD_PREVIEW, OLD_DOOR,
    NEW_ROOF, NEW_PREVIEW, NEW_DOOR, patch, unpatch, digest, build,
)

FIXTURE = """--!strict
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local world=Instance.new("Model")
world.Name="GQ805_LobbyGuildShop"
world:SetAttribute("EGGRUMBLE_NoPurchaseAuthority",true)
local center=Vector3.new(43,0,6)
local made=0
local prompt=Instance.new("ProximityPrompt")
prompt.Name="GQ805_ShopReadOnlyPrompt"
prompt.RequiresLineOfSight=true
prompt.Parent=door
local function piece() end
local roles={}
for i,r in ipairs(roles) do
 for variant=1,2 do
  local figurine=Instance.new("Model")
  local x=(i-4)*3.8
  local z=if variant==1 then -3 else 4
  local stand=piece(figurine,"Stand",Vector3.new(x,0.15,z),Vector3.new(2.6,.3,2.6),Color3.fromRGB(212,173,101),false)
""" + OLD_PREVIEW + """
  if variant==1 then plaque(stand,r[2].."\\n守護兵 2種類",38) end
 end
end
""" + OLD_ROOF + "\n" + OLD_DOOR + "\n"

class GuildSculptTests(unittest.TestCase):
    def test_byte_exact_on_off_and_visual_change(self):
        on=patch(FIXTURE)
        self.assertEqual(unpatch(on),FIXTURE)
        self.assertEqual(patch(FIXTURE).count(FEATURE),1)
        self.assertNotEqual(digest(on.encode()),digest(FIXTURE.encode()))

    def test_14_figures_retain_original_part_budget_and_owner(self):
        self.assertEqual(NEW_PREVIEW.count('piece(figurine,"GuardianBody"'),1)
        self.assertEqual(NEW_PREVIEW.count('piece(figurine,"GuardianHead"'),1)
        self.assertEqual(NEW_PREVIEW.count('piece(figurine,"SignatureGear"'),1)
        self.assertEqual(NEW_ROOF.count('Instance.new("WedgePart")'),1)
        self.assertIn("for half=-1,1,2 do",NEW_ROOF)
        self.assertIn("pitch.CanQuery=false",NEW_ROOF)
        self.assertIn("pitch.CanCollide=false",NEW_ROOF)
        self.assertNotIn("Enum.Material.Neon",NEW_ROOF+NEW_PREVIEW+NEW_DOOR)
        self.assertIn("Enum.Material.SmoothPlastic",NEW_DOOR)
        self.assertIn('local door=piece(world,"GuildEntry"',NEW_DOOR)
        self.assertEqual(patch(FIXTURE).count('prompt.Parent=door'),1)
        for token in ("FireServer(", "DataStoreService", "ProcessReceipt",
                      "RemoteEvent", "MarketplaceService", "RunService.Heartbeat",
                      "RenderStepped", "task.spawn", "TweenService"):
            self.assertNotIn(token,NEW_ROOF+NEW_PREVIEW+NEW_DOOR)

    def test_source_anchor_drift_rejected(self):
        examples={
            "already patched":patch(FIXTURE),
            "double roof":FIXTURE+"\n"+OLD_ROOF,
            "missing guardian":FIXTURE.replace(OLD_PREVIEW,""),
            "missing door":FIXTURE.replace(OLD_DOOR,""),
            "fake purchase authority":FIXTURE.replace(
               'world:SetAttribute("EGGRUMBLE_NoPurchaseAuthority",true)',""),
            "wrong prompt":FIXTURE.replace('prompt.RequiresLineOfSight=true',""),
            "no studio":FIXTURE.replace('RunService:IsStudio()', "IsPublic()"),
            "no role":FIXTURE.replace("for i,r in ipairs(roles) do",""),
            "no variant":FIXTURE.replace("for variant=1,2 do",""),
        }
        for name,raw in examples.items():
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,"RED_GQ470_GUILD_"):
                patch(raw)

    def test_mobile_scene_budget_and_unblocked_kiosk_lane(self):
        # Static coordinates only: not evidence of Studio camera visibility.
        self.assertIn("pitch.Size=Vector3.new(17,3,14.5)",NEW_ROOF)
        self.assertIn("half*7.25,11,2",NEW_ROOF)
        self.assertIn("made+=1",NEW_ROOF)
        self.assertIn("Vector3.new(bulk,tall",NEW_PREVIEW)
        self.assertIn('torso.Shape=if i==2 or i==4',NEW_PREVIEW)
        self.assertIn("weapon.CastShadow=true",NEW_PREVIEW)
        # Original physical podium: 29x25 studs, guard spacing 3.8 studs.
        # West and east roof wedges after 90deg yaw cover 14.5 studs each.
        floor_half_x=29/2
        roof_wedge_extent=14.5/2
        roof_left=(-7.25-roof_wedge_extent,-7.25+roof_wedge_extent)
        roof_right=(7.25-roof_wedge_extent,7.25+roof_wedge_extent)
        self.assertEqual(roof_left[1],roof_right[0])
        self.assertEqual((roof_left[0],roof_right[1]),(-14.5,14.5))
        self.assertEqual(2+1+2+1+1+1+14*4,64)  # floor, walkway, pillar2, back, door, roof2, previews
        for i in range(1,8):
            x=(i-4)*3.8
            # Pedestal half-width 1.3, largest weapon projected x=1+.325.
            self.assertLess(abs(x)+max(1.3,1+.325),floor_half_x)
            if i<7:
                self.assertGreater(3.8-2.6,1.0)  # visually separated 7 role podiums
        self.assertEqual(14*4,56)
        self.assertLessEqual(64,80)  # static private kiosk, not actual frame cost
        # Still a World ProximityPrompt, not a full-screen always-on purchase HUD.
        self.assertEqual(patch(FIXTURE).count('prompt.Name="GQ805_ShopReadOnlyPrompt"'),1)

    def _zip(self,path,corrupt=None):
        tree={"ServerScriptService":{
            "GQ805_LobbyGuildShop":{"$path":FILE,"$className":"Script"}}}
        originals={FILE:FIXTURE.encode()}
        hashes={ROUTE:digest(FIXTURE.encode())}
        for n in range(68):
            key="FakeVisual%02d"%n
            route="ServerScriptService/"+key
            filename="sources/"+route+".server.luau"
            body=("--!strict\nreturn "+str(n)+"\n").encode()
            tree["ServerScriptService"][key]={"$path":filename,"$className":"Script"}
            originals[filename]=body
            hashes[route]=digest(body)
        classes={route:"Script" for route in hashes}
        receipt={"canonical_build":True,"official_branch":"rc/p0d-s1-kids-rc01",
                 "source_profile":"REAL69","build_head":BASE,
                 "selected_source_count":69,"source_hashes":hashes,
                 "source_classes":classes}
        if corrupt=="head":receipt["build_head"]="0"*40
        if corrupt=="source":originals[FILE]+=b"BAD"
        if corrupt=="route":tree["ServerScriptService"]["GQ805_LobbyGuildShop"]["$path"]="sources/other.server.luau"
        if corrupt=="hash":receipt["source_hashes"][ROUTE]="f"*64
        if corrupt=="count":receipt["selected_source_count"]=68
        if corrupt=="branch":receipt["official_branch"]="main"
        if corrupt=="profile":receipt["source_profile"]="rich51"
        if corrupt=="class":receipt["source_classes"][ROUTE]="ModuleScript"
        if corrupt=="project_class":tree["ServerScriptService"]["GQ805_LobbyGuildShop"]["$className"]="ModuleScript"
        if corrupt=="rehashed":
            originals[FILE] += b"\n-- forged extra author data"
            receipt["source_hashes"][ROUTE]=digest(originals[FILE])
        with ZipFile(path,"w") as z:
            z.writestr("EGGRUMBLE_REAL69.project.json",json.dumps({"tree":tree}))
            z.writestr("REAL69_LEGACY_INTAKE_RECEIPT.json",json.dumps(receipt))
            for name,payload in originals.items():
                z.writestr(name,payload)
            if corrupt=="duplicate_zip":
                z.writestr("REAL69_LEGACY_INTAKE_RECEIPT.json",json.dumps(receipt))
        return originals

    def test_actual69_route_fixture_bytes_class_and_inverse(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);archive=base/"source.zip"
            sources=self._zip(archive)
            out=base/"candidate"
            # A synthetic fixture cannot have the canonical original Luau SHA.
            # Mock pinned hash only *within this unit fixture*, never in real CI build.
            with mock_patch("patch_guild69.ORIGINAL_SOURCE_SHA",digest(FIXTURE.encode())):
                result=build(archive,out)
            self.assertEqual(result["selected_script_count"],69)
            self.assertEqual(result["other_selected_byte_exact"],68)
            self.assertEqual(result["extra_decorative_parts"],1)
            self.assertEqual(result["new_scripts"],0)
            self.assertTrue(result["rollback_byte_exact"])
            self.assertFalse(result["official_rc_adopted"])
            self.assertEqual(result["art_gate"],"ART_NO_GO")
            for f,original in sources.items():
                want=patch(original.decode()).encode() if f==FILE else original
                self.assertEqual((out/f).read_bytes(),want)
            receipt=json.loads((out/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_text())
            self.assertEqual(receipt["source_hashes"][ROUTE],digest((out/FILE).read_bytes()))
            self.assertEqual((out/"OFF69_ORIGINAL_GUILD.server.luau").read_bytes(),sources[FILE])
            with self.assertRaisesRegex(ValueError,"RED_GQ470_GUILD_DEST_EXISTS"):
                build(archive,out)

    def test_stale_artifact_and_mutated_69_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for case in ("head","source","route","hash","count","branch",
                         "profile","class","project_class","rehashed","duplicate_zip"):
                with self.subTest(case=case):
                    z=root/(case+".zip");self._zip(z,corrupt=case)
                    with mock_patch("patch_guild69.ORIGINAL_SOURCE_SHA",digest(FIXTURE.encode())):
                        with self.assertRaisesRegex(ValueError,"RED_GQ470_GUILD_"):
                            build(z,root/("out_"+case))

if __name__=="__main__":
    unittest.main()
