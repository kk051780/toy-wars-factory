"""Strict source and actual-place integration QA. Does not claim Studio gameplay."""
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('build_undead_rc85', HERE/'build_undead_rc85.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ActualUndeadRC85Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=mod.build()
        cls.xml=(HERE/'P0D_FB026_NECROMANCER_SIEGE_CUMULATIVE_PRIVATE85.rbxlx').read_bytes()
        cls.root=ET.fromstring(cls.xml)
        cls.scripts={n:s.text for n,(_,_,s) in mod.sources(cls.root).items()}
        with ZipFile(HERE/'parent_rc84.zip') as outer:
            with ZipFile(io.BytesIO(outer.read(outer.namelist()[0]))) as inner:
                cls.base=ET.fromstring(inner.read([x for x in inner.namelist() if x.endswith('.rbxlx')][0]))
                cls.before={n:s.text for n,(_,_,s) in mod.sources(cls.base).items()}

    def test_01_actual_place_85(self):
        self.assertEqual(85,len(self.scripts))
        self.assertEqual(84,len(self.before))
        self.assertEqual(830812,len(self.xml))
        self.assertEqual('fdd7ed3397c02825c67e986ca0fb1755dbe15f9523ac065cbef1cdc66d81d978',mod.digest(self.xml))

    def test_02_original_83_unchanged(self):
        for name,source in self.before.items():
            if name!='Game':self.assertEqual(source,self.scripts[name],name)

    def test_03_source_lock_exact(self):
        sl=json.loads((HERE/'SOURCE_LOCK.json').read_text())
        feat=json.loads((HERE/'RC_FEATURE_LOCK.json').read_text())
        self.assertEqual(sl['blobs'],feat['source_gitblobs'])
        self.assertEqual(85,sl['total_scripts'])
        self.assertEqual(85,feat['total_sources'])
        self.assertEqual(sorted(mod.blob(s) for s in self.scripts.values()), sorted(sl['blobs'].values()))

    def test_04_real_server_module_class_path(self):
        installed=mod.sources(self.root)['UndeadSquad']
        self.assertEqual('ModuleScript',installed[1].get('class'))
        parent=installed[0]
        self.assertTrue(any(item is installed[1] for item in parent.findall('Item')))
        self.assertEqual(self.scripts['UndeadSquad'],(HERE/'UndeadSquad.luau').read_text())
        all_nodes=[n for n in self.root.iter('Item') if n.attrib.get('referent')]
        refs=[n.attrib['referent'] for n in all_nodes]
        self.assertEqual(len(refs),len(set(refs)))

    def test_05_real_3_npcs_attack(self):
        m=self.scripts['UndeadSquad']
        for marker in ['local COUNT = 3','local MAX_TICKS = 240','buildZombie',
                'task.wait(.2)','ctx.targets()','ctx.hit(position, aim.Unit, 8)',
                'squad.mode == "GUARD"','squad.mode ~= "FOLLOW"',
                'player:SetAttribute("P0D_UndeadCommand", old.mode)']:
            self.assertIn(marker,m)

    def test_06_real_game_authority_not_second_remote(self):
        m=self.scripts['UndeadSquad']
        game=self.scripts['Game']
        for blocked in ('RemoteEvent','FireServer','OnServerEvent','DataStoreService',
                        'player.Character.Humanoid.Health =', 'personalNeutralKOs', 'Game.server'):
            self.assertNotIn(blocked,m)
        self.assertIn('return sevenJobStrike(player,position,dir,dmg)',game)
        self.assertIn('and sevenJobPickAckSeq[player]==castAck',game)
        self.assertIn('and match.serial==castSerial',game)
        self.assertIn('and sevenJobs[player]=="NECROMANCER"',game)
        self.assertIn('and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false',game)

    def test_07_all_revoke_sites(self):
        patch=self.scripts['Game']
        self.assertEqual(6, patch.count('SevenJobs.Undead.clear('))
        self.assertIn('local function resetRound()\n    for _,p',patch)
        self.assertIn('SevenJobs.Undead.clear(player) -- no old squad',patch)

    def test_08_non_collision(self):
        m=self.scripts['UndeadSquad']
        self.assertIn('p.CanCollide = false',m)
        self.assertIn('p.CanQuery = false',m)
        self.assertIn('p.CanTouch = false',m)
        self.assertIn('p.Anchored = true',m)
        self.assertIn('workspace:Raycast(position + Vector3.new(0, 1.4, 0)',m)
        self.assertIn('root.Position.Y-1.6',m)

    def test_09_deterministic_rebuild(self):
        before=self.xml
        self.assertEqual(self.receipt,mod.build())
        self.assertEqual(before,(HERE/'P0D_FB026_NECROMANCER_SIEGE_CUMULATIVE_PRIVATE85.rbxlx').read_bytes())

    def test_10_corrupted_original_anchor_fail_closed(self):
        game=self.before['Game'].replace('sevenJobStrike(player,root.Position,facing,14)', 'sevenJobStrike(player,root.Position,facing,15)')
        with self.assertRaisesRegex(ValueError,'SOURCE_DRIFT_NECRO_REAL_SQUAD'):
            mod.patch_game(game)

    def test_11_changed_source_is_not_claimed_native(self):
        for flag in ('native_luau','rojo','studio','android'):
            self.assertEqual('NOT_RUN',self.receipt[flag])
        self.assertFalse(self.receipt['official_rc_write'])
        self.assertFalse(self.receipt['owner_accepted'])


    def test_12_siege_gate_carrier_and_warp_modules_unchanged(self):
        for n in ('MapBuilder', 'SoloTeamBots', 'TrapperWarpService', 'SevenJobArmamentM1', 'Horde', 'TrapRaidersHUD'):
            if n in self.before:
                self.assertEqual(self.before[n], self.scripts[n], n)
        self.assertIn('SoloTeamBots', self.scripts)
        self.assertIn('MapBuilder', self.scripts)
        self.assertIn('TrapperWarpService', self.scripts)

    def test_13_private_place_parent_locked(self):
        self.assertEqual('89b47d4d919a04b4ea72304681749f2b8f01da768698bf5a1838b8bb5c331e7e', mod.PARENT_SHA)
        self.assertEqual(85, self.receipt['script_count'])
        self.assertTrue(self.receipt['old_83_scripts_byte_exact'])


    def test_14_wall_and_true_target_raycast_regression(self):
        module = self.scripts['UndeadSquad']
        self.assertIn('lineHit.Instance:IsDescendantOf(neutral.model)', module)
        self.assertIn('if lineHit == nil or lineHit.Instance:IsDescendantOf(neutral.model)', module)
        self.assertIn('if workspace:Raycast(position + Vector3.new(0, 1.4, 0),', module)
        self.assertIn('Vector3.new(path.X, 0, path.Z), sight) == nil then', module)
        self.assertNotIn('if (position-root.Position).Magnitude > 29 then position = desired end', module)

    def test_15_source_lock_no_alternate_authority_or_duplicate_modules(self):
        from collections import Counter
        self.assertEqual(1, sum(1 for n in self.scripts if n == 'Game'))
        self.assertEqual(1, sum(1 for n in self.scripts if n == 'UndeadSquad'))
        self.assertIn('TrapperWarpService', self.scripts)
        self.assertIn('MapBuilder', self.scripts)
        self.assertIn('SoloTeamBots', self.scripts)

if __name__=='__main__':unittest.main()