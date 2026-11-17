#!/usr/bin/env python3
"""GQ8-LSS: original optional32 shared prompt() server visibility contract.

Source-derived negative/mutation gate, NOT a substitute for Roblox Studio,
Android or network replay testing.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "EGGRUMBLE_LandSeaSkyTraversal.server.luau"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
OLD_UNSAFE = "if (root.Position-part.Position).Magnitude>17 then return end"


def check_live_prompt(source: str) -> None:
    if source.count("local function prompt(part,verb,object,callback)") != 1:
        raise AssertionError("RED_PROMPT_SINGLE_AUTHORITY")
    prompt = source.split("local function prompt(part,verb,object,callback)", 1)[1].split(
        "local function matchHuman(", 1
    )[0]
    contract = (
        'q.RequiresLineOfSight=true',
        'if not root or not hum or hum.Health<=0 then return end',
        '(root.Position-part.Position).Magnitude>q.MaxActivationDistance+1',
        'local head=ch:FindFirstChild("Head")',
        'params.FilterType=Enum.RaycastFilterType.Exclude',
        'params.FilterDescendantsInstances={ch}',
        'params.RespectCanCollide=true',
        'local hit=Workspace:Raycast(origin,direction,params)',
        'if hit and hit.Instance~=part',
        'part.Parent:IsA("Model") and hit.Instance:IsDescendantOf(part.Parent)',
        'then return end',
        'callback(player,hum,root)',
    )
    for line in contract:
        if line not in prompt:
            raise AssertionError("RED_PROMPT_MISSING_" + line)
    if OLD_UNSAFE in prompt:
        raise AssertionError("RED_PROMPT_OLD_OVERREACH")
    order = (
        'hum.Health<=0',
        'q.MaxActivationDistance+1',
        'Workspace:Raycast(origin,direction,params)',
        'if hit and hit.Instance~=part',
        'callback(player,hum,root)',
    )
    idx = [prompt.index(token) for token in order]
    if idx != sorted(idx):
        raise AssertionError("RED_PROMPT_AUTHORIZATION_ORDER")
    if "seat.Occupant~=h" not in source:
        raise AssertionError("RED_COCKPIT_PILOT_AUTHORITY_LOST")
    if "matchHuman(p2,mode,world,nil)" not in source:
        raise AssertionError("RED_CURRENT_WORLD_MATCH_GUARD_LOST")


class ServerSightSourceGate(unittest.TestCase):
    def test_reach_wall_and_pilot_guards(self):
        check_live_prompt(SOURCE)

    def test_negative_mutants_all_red(self):
        replacements = [
            ('q.MaxActivationDistance+1', '17'),
            ('params.RespectCanCollide=true', 'params.RespectCanCollide=false'),
            ('Workspace:Raycast(origin,direction,params)', 'nil'),
            ('if hit and hit.Instance~=part', 'if false and hit.Instance~=part'),
            ('params.FilterDescendantsInstances={ch}', 'params.FilterDescendantsInstances={}'),
            ('seat.Occupant~=h', 'seat.Occupant==h'),
        ]
        for original, mutant in replacements:
            with self.subTest(mutant=mutant):
                self.assertIn(original, SOURCE)
                with self.assertRaises(AssertionError):
                    check_live_prompt(SOURCE.replace(original, mutant, 1))

    def test_lock_matches_real_optional_source_and_off31(self):
        data = SOURCE_PATH.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        manifest = json.loads(
            (ROOT.parent.parent / "rc_fastlane" / "EGGRUMBLE_V3_LSS_OPTIONAL32.json").read_text()
        )
        lock = json.loads((ROOT / "GQ8_RC32_SOURCE_LOCK.json").read_text())
        self.assertEqual(manifest["added_source_git_blob"], blob)
        self.assertEqual(manifest["gq8_orphan_craft_owner"]["source_git_blob"], blob)
        self.assertEqual(manifest["gq8_prompt_server_sight"]["source_git_blob"], blob)
        self.assertEqual(lock["optional_profile"]["source_blob_sha"], blob)
        self.assertEqual(manifest["source_count"], 32)
        self.assertEqual(lock["optional_profile"]["original31_script_count"], 31)
        self.assertTrue(lock["authority"]["canonical_v3_31_profile_untouched"])


if __name__ == "__main__":
    unittest.main()
