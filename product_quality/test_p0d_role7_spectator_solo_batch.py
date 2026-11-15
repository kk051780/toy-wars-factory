"""Regression controls for exact real RC82 cumulative spectator + private solo bot merge."""
import copy
import io
import os
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
import p0d_role7_spectator_solo_batch as b

BASE=Path(os.environ.get('P0D_BOT_PARENT_ARTIFACT',Path(__file__).parent/'P0D_SOURCE_14153251141.zip'))


def original():
    with zipfile.ZipFile(BASE) as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read(outer.namelist()[0]))) as z:
            return z.read(b.PARENT_PLACE),json.loads(z.read('SOURCE_LOCK.json')),json.loads(z.read('RC_FEATURE_LOCK.json'))

class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw,cls.lock,cls.feature=original()
        _,cls.parent_script=b.locked(cls.raw,cls.lock,cls.feature)
        cls.before={n:e.text for n,(e,_,_) in cls.parent_script.items()}
        cls.game,cls.bots=b.patch_sources(cls.before['Game'],cls.before['SoloTeamBots'])

    def test_01_parent_verified(self):
        self.assertEqual(b.sha(self.raw),b.PARENT_SHA)
        self.assertEqual(self.lock['blobs'][b.GAME],b.PARENT_GAME)
    def test_02_script_count(self):self.assertEqual(len(self.before),82)
    def test_03_egg_authority_exact(self):self.assertEqual(b.egg_block(self.game),b.egg_block(self.before['Game']))
    def test_04_spectator_waiting_island_kept(self):
        self.assertEqual(self.game.count('if map.model:FindFirstChild("P0D_SAFE_LOBBY")==nil then'),1)
        self.assertEqual(self.game.count('LobbyIsland.build(map.model)'),2)
    def test_05_horde_is_not_attacking_observers(self):
        self.assertIn('horde:tick(now,eligibleSoloPlayers(),healthy)',self.game)
        self.assertIn('victim:GetAttribute("P0D_LateJoinSpectator")~=true',self.game)
    def test_06_null_team_reentry_safe(self):
        self.assertIn('or root.CFrame)',self.game)
        self.assertNotIn('else map.teams[getTeamName(entrant)].spawn +',self.game)
    def test_07_private_double_opt_in(self):
        self.assertIn('game.PrivateServerId ~= ""',self.bots)
        self.assertIn('P0D_PRIVATE_LIVE_HORDE_NINE',self.bots)
        self.assertIn('P0D_PRIVATE_SOLO_TEAM_BOTS',self.bots)
    def test_08_studio_preserved(self):self.assertIn('if not (RunService:IsStudio() or',self.bots)
    def test_09_private_flag_off_stop(self):
        self.assertIn('and not privateSoloBotsTrialAllowed() then\n        SoloTeamBots.stop()',self.game)
    def test_10_original_one_game_authority_kept(self):
        self.assertEqual(self.game.count('local function privateSoloBotsTrialAllowed()'),1)
        self.assertIn('pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)',self.game)
        self.assertIn('SoloTeamBots.tryHumanHit(',self.game)
    def test_11_delayed_job_guard_preserved(self):
        self.assertIn('player.Character~=castCharacter',self.game)
        self.assertIn('sevenJobPickAckSeq[player]~=selectedAck',self.game)
    def test_12_combo_expiry_preserved(self):self.assertIn('mobComboUntil[player] or 0',self.game)
    def test_13_lock_can_reject_swapped_sources(self):
        root,els=b.locked(self.raw,self.lock,self.feature)
        els['SevenJobsRules'][0].text,els['S1RaiderWindRules'][0].text=els['S1RaiderWindRules'][0].text,els['SevenJobsRules'][0].text
        with self.assertRaisesRegex(ValueError,'CLASS_PATH_OR_SOURCE_LOCK_DRIFT'):
            b.locked(ET.tostring(root,encoding='utf-8'),self.lock,self.feature)
    def test_14_wrong_code_anchor_fails(self):
        with self.assertRaisesRegex(ValueError,'ANCHOR_DRIFT'):
            b.patch_sources(self.before['Game'].replace('if RunService:IsStudio() and studioSoloRoundStarted','if flag'),self.before['SoloTeamBots'])
    def test_15_duplicate_bot_gate_fails(self):
        with self.assertRaisesRegex(ValueError,'ANCHOR_DRIFT_OR_DUPLICATE'):
            b.patch_sources(self.game,self.bots)
    def test_16_egg_corruption_denied(self):
        wrong=self.before['Game'].replace('personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1','personalEggDeposits[player]=100')
        with self.assertRaisesRegex(ValueError,'CORE_GAMEPLAY_REGRESSION'):
            b.patch_sources(wrong,self.before['SoloTeamBots'])
    def test_17_build_exact_82(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'stage.zip'
            report=b.build(BASE.read_bytes(),out)
            self.assertEqual(report['source_count'],82)
            self.assertEqual(report['unchanged_parent_scripts'],80)
            self.assertTrue(report['egg_score_winner_source_byte_exact'])
            with zipfile.ZipFile(out) as z:
                raw=z.read(b.OUTPUT_PLACE)
                sl=json.loads(z.read('SOURCE_LOCK.json'));fl=json.loads(z.read('RC_FEATURE_LOCK.json'))
                b.locked(raw,sl,fl)
                self.assertEqual(report['place_sha256'],b.sha(raw))
    def test_18_duplicate_zip_member_denied(self):
        with zipfile.ZipFile(BASE) as outer:
            with zipfile.ZipFile(io.BytesIO(outer.read(outer.namelist()[0]))) as z:
                members={n:z.read(n) for n in z.namelist()}
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as inside:
            for n,data in members.items():inside.writestr(n,data)
            inside.writestr('SOURCE_LOCK.json',members['SOURCE_LOCK.json'])
        outer=io.BytesIO()
        with zipfile.ZipFile(outer,'w') as outside:outside.writestr('x.zip',buf.getvalue())
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'DUPLICATE_ZIP_MEMBER'):
                b.build(outer.getvalue(),Path(d)/'bad.zip')

if __name__=='__main__':unittest.main()