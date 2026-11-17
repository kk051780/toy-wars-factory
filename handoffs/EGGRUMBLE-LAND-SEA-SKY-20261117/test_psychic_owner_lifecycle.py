#!/usr/bin/env python3
"""Protect caster-phase truth; no psychic BR warp after owner death/exit."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE=Path(__file__).resolve().parent
SRC=(HERE/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text("utf-8")
spec=importlib.util.spec_from_file_location("psy",HERE/"make_psychic_owner_native.py")
psy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(psy)


class PsychicOwnerGuard(unittest.TestCase):
    def test_owner_and_victim_both_authorized_at_touch(self):
        body=psy.extract(SRC)
        self.assertIn('matchHuman(owner,mode,world,"TRAPPER")',body)
        self.assertIn("casterHumanoid.Health<=0",body)
        self.assertIn("owner.Character~=casterCharacter",body)
        self.assertIn("matchHuman(guest,mode,world,nil)",body)
        self.assertIn("safeMove(guest,seaRaft.Position",body)
        self.assertIn('mode~="BATTLE_ROYALE"',SRC)

    def test_died_respawn_eliminated_logout_disconnects(self):
        for exact in (
            'local diedConnection=casterHumanoid.Died:Connect(function()',
            "local respawnConnection=owner.CharacterRemoving:Connect(function()",
            '"EGGRUMBLE_Eliminated"):Connect(function()',
            "local ancestryConnection=owner.AncestryChanged:Connect(function()",
            "diedConnection:Disconnect()",
            "respawnConnection:Disconnect()",
            "eliminatedConnection:Disconnect()",
            "ancestryConnection:Disconnect()",
            "if owner:GetAttribute(\"EGGRUMBLE_Eliminated\")==true and t.Parent then",
            "if not owner.Parent and t.Parent then t:Destroy() end"
        ):
            with self.subTest(text=exact):
                self.assertIn(exact,SRC)

    def test_still_one_bounded_server_trap_and_no_new_game_authority(self):
        self.assertEqual(SRC.count('t.Touched:Connect(function(other)'),1)
        self.assertEqual(SRC.count("GQ8_LSS_PSYCHIC_OWNER_LIFECYCLE_BEGIN"),1)
        self.assertIn("MAX_LIVE_TRAPS = 2",SRC)
        for bad in ('Instance.new("RemoteEvent")', "DataStoreService",
                    'TakeDamage(', 'SetAttribute("EGGRUMBLE_NeutralKOs"'):
            self.assertNotIn(bad,SRC)

    def test_native_callback_is_real_source_and_mutant_is_different(self):
        with TemporaryDirectory() as temp:
            a=Path(temp)/"good.luau"
            b=Path(temp)/"old_mutant.luau"
            psy.write(a,b)
            self.assertIn('matchHuman(owner,mode,world,"TRAPPER")',a.read_text())
            self.assertNotIn('matchHuman(owner,mode,world,"TRAPPER")',b.read_text())
            self.assertIn('LSS_ACTUAL_PSYCHIC_OWNER_LUAU_10_CASES_PASS',a.read_text())
            self.assertEqual(a.read_text().count("safeMove(guest,"),1)
            self.assertIn('guest.Character=ch', a.read_text())
            self.assertIn('case=="move_rejected"', a.read_text())


if __name__=="__main__":unittest.main()
