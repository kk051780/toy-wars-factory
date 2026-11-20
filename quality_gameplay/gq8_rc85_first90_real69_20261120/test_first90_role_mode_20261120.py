#!/usr/bin/env python3
"""Regression for actual V3 server role/mode attributes vs selected REAL69 first90 guide.
No synthetic gameplay completion: source/Native/Rojo proof only, engine not run.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
SRC=HERE/"EGGRUMBLE_LegacyFirst90.client.luau"
ROUTE="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90"
ORIGINAL_SHA256="15b2da4db44b603b3d90070cf16f7c01d3e488c9009e3347150c0efd86494e99"
OLD_BLOCK='''local function cue(now:number):string
 local role=player:GetAttribute("EGGRUMBLE_Role")
 local mode=player:GetAttribute("EGGRUMBLE_QueuedMode")'''
NEW_BLOCK='''-- GQ8_FB014_CANONICAL_ROLE_MODE_V3_20261120
-- Use the server's actual role stand acknowledgement during lobby and its
-- canonical BATTLE_ROYALE mode. Combat role is a fallback after deployment.
local function cue(now:number):string
 local role=player:GetAttribute("EGGRUMBLE_SelectedRole")
 if type(role)~="string" or role=="" then
  role=player:GetAttribute("EGGRUMBLE_Role")
 end
 local mode=player:GetAttribute("EGGRUMBLE_QueuedMode")'''
OLD_MODE='if type(mode)~="string" or (mode~="TEAM" and mode~="BR") then'
NEW_MODE='if type(mode)~="string" or (mode~="TEAM" and mode~="BATTLE_ROYALE") then'

def exact_rollback(candidate: bytes) -> bytes:
    text=candidate.decode("utf-8")
    if text.count(NEW_BLOCK)!=1 or text.count(NEW_MODE)!=1:
        raise AssertionError("RED_FIRST90_MISSING_UNIQUE_REPAIR")
    original=text.replace(NEW_BLOCK, OLD_BLOCK).replace(NEW_MODE, OLD_MODE)
    restored=original.encode("utf-8")
    if hashlib.sha256(restored).hexdigest()!=ORIGINAL_SHA256:
        raise AssertionError("RED_FIRST90_UNRELATED_SOURCE_EDIT")
    return restored

class First90LiveServerContract(unittest.TestCase):
    def test_only_two_necessary_logical_fixes_and_exact_old_source_rollback(self):
        restored=exact_rollback(SRC.read_bytes())
        self.assertEqual(hashlib.sha256(restored).hexdigest(),ORIGINAL_SHA256)
        self.assertLess(len(SRC.read_bytes())-len(restored),650)
    def test_server_role_and_mode_are_correct_not_legacy_shorthand(self):
        src=SRC.read_text(encoding="utf-8")
        self.assertIn('local role=player:GetAttribute("EGGRUMBLE_SelectedRole")',src)
        self.assertIn('role=player:GetAttribute("EGGRUMBLE_Role")',src)
        self.assertIn(NEW_MODE,src)
        self.assertNotIn(OLD_MODE,src)
        self.assertIn('if type(role)~="string" or role=="" then',src)
        self.assertIn('if type(mode)~="string"',src)
    def test_guide_is_bounded_studio_only_and_not_second_authority(self):
        src=SRC.read_text(encoding="utf-8")
        self.assertIn("if not RunService:IsStudio() then return end",src)
        self.assertIn("local DURATION=90",src)
        self.assertIn("MaxDistance=32",src)
        for forbidden in ("FireServer(", "RemoteEvent", "DataStoreService", "MarketplaceService", "TakeDamage("):
            self.assertNotIn(forbidden,src)
    def test_mutations_rejected_and_user_journey_simulated(self):
        original=SRC.read_bytes()
        for mutation in (
            original.replace(b"BATTLE_ROYALE",b"BR"),
            original.replace(b"EGGRUMBLE_SelectedRole",b"EGGRUMBLE_Role"),
            original+b"\n-- unexpected extra source changes\n",
        ):
            with self.assertRaises(AssertionError):
                exact_rollback(mutation)
        def cue(mode,selected_role,combat_role,elapsed):
            role=selected_role if isinstance(selected_role,str) and selected_role else combat_role
            if mode not in ("TEAM","BATTLE_ROYALE"):
                return "choose"
            if not isinstance(role,str) or not role:
                return "select_role"
            if elapsed<22:return "team" if mode=="TEAM" else "royale"
            if elapsed<48:return "steal_or_siege"
            return "deliver"
        self.assertEqual(cue("BATTLE_ROYALE","NINJA",None,10),"royale")
        self.assertEqual(cue("BATTLE_ROYALE","NINJA",None,28),"steal_or_siege")
        self.assertEqual(cue("BATTLE_ROYALE","NINJA",None,60),"deliver")
        self.assertEqual(cue("TEAM","WARRIOR",None,10),"team")
        self.assertEqual(cue(None,None,None,15),"choose")
        self.assertEqual(cue("TEAM",None,None,15),"select_role")
    def test_real_built_host_matches_attributes_when_available(self):
        base=os.environ.get("EGGRUMBLE_SELECTED_BUILD","")
        if not base:
            self.skipTest("Pass EGGRUMBLE_SELECTED_BUILD to verify actual selected 69-source Host")
        root=Path(base)
        project=json.loads((root/"EGGRUMBLE_REAL69.project.json").read_text())
        tree=project["tree"]
        def route_path(route):
            node=tree
            for part in route.split("/"):
                node=node[part]
            return root/node["$path"]
        client=route_path(ROUTE).read_bytes()
        host=route_path("ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview").read_text()
        self.assertEqual(client,SRC.read_bytes())
        self.assertEqual(client.count(b"GQ8_FB014_CANONICAL_ROLE_MODE_V3_20261120"),1)
        self.assertIn('local queues:{[string]:{Player}}={TEAM={},BATTLE_ROYALE={}}',host)
        self.assertIn('p:SetAttribute("EGGRUMBLE_QueuedMode",mode)',host)
        self.assertIn('p:SetAttribute("EGGRUMBLE_SelectedRole",role)',host)
        self.assertIn('if chosenRole[p.UserId]==nil then',host)
        self.assertIn('local role=chosenRole[p.UserId] or "WARRIOR"',host)

if __name__=="__main__":
    unittest.main()
