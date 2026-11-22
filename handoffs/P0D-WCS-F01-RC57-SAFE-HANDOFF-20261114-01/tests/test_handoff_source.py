#!/usr/bin/env python3
"""WCS F01/C01 source-only safety contract. No Roblox engine claim."""
from pathlib import Path
import hashlib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "WCS_CrystalCanyon.server.luau"
SOURCE_BLOB = "9b891ae8b0dd579ccf1cd477b8b012e03415c0b0"
AUTHOR_BLOB = "3edcb19d91de509afd3de227cbfbca5d75125ec2"
START = "-- P0D World-Character Synergy F01+C01 (S2+ isolated candidate)\n"
STOP = 'world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")\n'

def git_blob(b):
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

def verify(s):
    required = (
        'if not RunService:IsStudio() then',
        'GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")==false',
        'WaitForChild("TRAP_RAIDERS_S1",45)',
        'WaitForChild("H1_FUN_WORLD",45)',
        'if not skyWalk or not skyWalk:IsA("BasePart") then',
        'makeRoute("CANYON_ENTRY_RED"',
        'makeRoute("CANYON_ENTRY_BLUE"',
        'makePart("AlwaysOpenSafeRoute"',
        'makeMole("MoguronWest", -32)',
        'makeMole("MoguronEast", 32)',
        'math.abs(localPoint.X) <= 3.5 and math.abs(localPoint.Z) <= 8',
        'nextOpenAllowed = os.clock() + REOPEN_COOLDOWN',
        'and not playerIsInGateClosureZone() then',
        'end -- WCS-F01/C01 author world with #295 gate safety repair',
    )
    for v in required:
        if s.count(v) != 1:
            raise ValueError("MISSING_OR_DUPLICATE:" + v)
    if s.count(START) != 1 or s.count(STOP) != 1:
        raise ValueError("AUTHOR_DELIMITER_DRIFT")
    a = s.index(START)
    b = s.index(STOP, a) + len(STOP)
    if git_blob(s[a:b].encode()) != AUTHOR_BLOB:
        raise ValueError("AUTHOR_295_BLOB_DRIFT")
    if any(x in s for x in ('OnServerEvent:Connect', 'UpdateAsync', 'SetAsync',
                            'GetAsync', 'Instance.new("RemoteEvent")')):
        raise ValueError("SECOND_AUTHORITY_FORBIDDEN")
    if 'playerIsOnBridge()' in s:
        raise ValueError("OLD_GATE_CAMPING_CHECK")
    if 'if gateOpen and not open then\n        nextOpenAllowed = os.clock() + REOPEN_COOLDOWN' not in s:
        raise ValueError("REAL_CLOSE_COOLDOWN_MISSING")
    if s.count('world.Name = "P0D_WCS_CrystalCanyon"') != 1:
        raise ValueError("DUPLICATE_WORLD")
    return True

class TestWorldHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = SOURCE.read_bytes()
        cls.s = cls.b.decode("utf8")

    def test_actual_source_git_blob(self):
        self.assertEqual(git_blob(self.b), SOURCE_BLOB)

    def test_contract(self):
        self.assertTrue(verify(self.s))

    def test_no_studio_guard(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('if not RunService:IsStudio() then',
                                  'if RunService:IsStudio() then', 1))

    def test_gate_zone_drift(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('math.abs(localPoint.X) <= 3.5',
                                  'math.abs(localPoint.X) <= 27', 1))

    def test_no_close_cooldown(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('nextOpenAllowed = os.clock() + REOPEN_COOLDOWN',
                                  'nextOpenAllowed = 0', 1))

    def test_stale_bridge_camping_check(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('playerIsInGateClosureZone()',
                                  'playerIsOnBridge()', 1))

    def test_no_entry(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('makeRoute("CANYON_ENTRY_BLUE"',
                                  'makeRoute("MISSING_ENTRY_BLUE"', 1))

    def test_no_detour(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('makePart("AlwaysOpenSafeRoute"',
                                  'makePart("REMOVED_DETOUR"', 1))

    def test_duplicate_author(self):
        with self.assertRaises(ValueError):
            verify(self.s + self.s)

    def test_no_new_game_remote(self):
        with self.assertRaises(ValueError):
            verify(self.s + '\nremote.OnServerEvent:Connect(function() end)\n')

    def test_removed_world(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('world.Name = "P0D_WCS_CrystalCanyon"',
                                  'world.Name = "MISSING_WORLD"', 1))

    def test_no_author_source_rewrite(self):
        with self.assertRaises(ValueError):
            verify(self.s.replace('local OPEN_SECONDS = 14',
                                  'local OPEN_SECONDS = 40', 1))

if __name__ == "__main__":
    unittest.main()
