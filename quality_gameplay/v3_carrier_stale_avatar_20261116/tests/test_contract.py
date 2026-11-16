#!/usr/bin/env python3
"""One-source behavioral fence with negative controls and exact rollback."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import compose as c

class StaleAvatarCarrierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=c.SOURCE.read_text(encoding="utf-8")
        cls.patched=c.patch(cls.original)
    def test_source_lock(self):
        self.assertEqual(c.git_blob(self.original.encode()),c.ORIGINAL_BLOB)
    def test_one_life_callback(self):
        self.assertEqual(self.original.count('humanoid.Died:Connect(function()'),1)
    def test_old_life_guard(self):
        self.assertIn('player.Character~=character',self.patched)
    def test_exact_same_session_guard(self):
        self.assertIn('sessions[mode]~=session',self.patched)
    def test_mode_guard(self):
        self.assertIn('joined[player.UserId]~=mode',self.patched)
    def test_phase_guard(self):
        self.assertIn('session.rules.phase~="ACTIVE"',self.patched)
    def test_original_exact_rollback(self):
        marker=('      -- Reject old Humanoid.Died after respawn; only the current avatar owns these eggs.\n'
                '      if joined[player.UserId]~=mode or sessions[mode]~=session\n'
                '       or player.Character~=character or session.rules.phase~="ACTIVE" then return end')
        self.assertEqual(self.patched.count(marker),1)
        self.assertEqual(self.patched.replace(marker,'      if joined[player.UserId]~=mode then return end',1),self.original)
    def test_no_other_authority_changed(self):
        for label in ('BotActors.start(session,Rules)','SwarmCombat.start(session)',
                      'RaidItemIntake.start(session,root,FieldItems)',
                      'SevenRoleCombat.equip(session,p,role)','session.refresh=function()',
                      'Rules.takeEggs(','Rules.depositEggs(','joinQueue("TEAM",p)',
                      'joinQueue("BATTLE_ROYALE",p)'):
            self.assertEqual(self.original.count(label),self.patched.count(label),label)
    def test_callback_extraction_real(self):
        source=c.native_cases(self.patched)
        self.assertIn('local function actualDiedCallback()',source)
        self.assertIn('session.dropCarrierEggs(tostring(player.UserId),',source)
        self.assertIn('GQ_STALE_AVATAR_CARRIER_REAL_CALLBACK_NATIVE=PASS',source)
    def test_private_21_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt=c.compose(Path(temp))
            self.assertEqual(receipt['source_count'],21)
            self.assertEqual(receipt['modified_original_script_count'],1)
            self.assertEqual(receipt['formal_rc'],'NOT_INTEGRATED')
            mapped=json.loads((Path(temp)/'private.project.json').read_text())
            self.assertEqual(mapped['tree']['ServerScriptService'][c.HOST_NODE]['$path'],'HostOverlay.server.luau')
            self.assertEqual((Path(temp)/'HostOverlay.server.luau').read_text(),self.patched)
            self.assertTrue((Path(temp)/'native_cases.luau').is_file())
    def test_source_drift_negative(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_LOCK'):
            c.patch(self.original.replace('session.dropCarrierEggs','session.dropOtherEggs'))
    def test_anchor_negative(self):
        other=self.original.replace('      if joined[player.UserId]~=mode then return end','      if false then return end')
        previous=c.ORIGINAL_BLOB
        try:
            c.ORIGINAL_BLOB=c.git_blob(other.encode())
            with self.assertRaisesRegex(ValueError,'SOURCE_LOCK'):
                c.patch(other)
        finally:
            c.ORIGINAL_BLOB=previous

if __name__=='__main__':
    unittest.main()
