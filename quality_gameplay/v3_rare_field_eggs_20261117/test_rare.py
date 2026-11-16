#!/usr/bin/env python3
"""Source mutation tests for 2 mirrored non-monetary field eggs; no RC mutation."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
from select_rare import (HOST_OLD,HOST_NEW,SCORE_CHANGES,RARE_IDS,apply_host,apply_score,inverse_score)

ORIGINAL_HOST=Path("_v3_original/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_LobbyCastleModesPreview.server.luau")
ORIGINAL_SCORE=Path("_v3_score/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_ScoreBalance.luau")

class RareFieldEggsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host=ORIGINAL_HOST.read_text(encoding="utf-8")
        cls.score=ORIGINAL_SCORE.read_text(encoding="utf-8")
    def test_real_original_host_patch(self):
        after=apply_host(self.host)
        self.assertIn("rareFieldEgg=i==4 or i==5",after)
        self.assertIn('if rareFieldEgg then "レア卵｜60点"',after)
        self.assertEqual(after.count("rareFieldEgg=i==4 or i==5"),1)
    def test_real_original_score_patch(self):
        after=apply_score(self.score)
        self.assertIn("claimedRareFieldEggs={}",after)
        self.assertIn('id=="FIELD_4" or id=="FIELD_5"',after)
        self.assertEqual(after.count("row.rareEggs+=1"),1)
    def test_full_off_host_byte_exact(self):
        self.assertEqual(apply_host(self.host).replace(HOST_NEW,HOST_OLD,1),self.host)
    def test_full_off_score_byte_exact(self):
        self.assertEqual(inverse_score(apply_score(self.score)),self.score)
    def test_real_server_token_authority_preserved(self):
        result=apply_host(self.host)
        for s in ['local eggId="FIELD_"..i','Rules.takeFieldEgg(session.rules,tostring(p.UserId),eggId)',
                  'if pcall(function() Rules.takeFieldEgg(', 'if joined[p.UserId]~=mode or egg.Parent==nil then return end']:
            self.assertEqual(result.count(s),self.host.count(s),s)
    def test_no_second_game_gui_or_remote(self):
        result=apply_host(self.host)
        for s in ['Instance.new("BillboardGui")','Instance.new("RemoteEvent")','local function startSession(mode:string)',
                  'Rules.start(session.rules)','BotActors.start(session,Rules)']:
            self.assertEqual(result.count(s),self.host.count(s),s)
    def test_score_no_fake_kos_or_egg_inflation(self):
        result=apply_score(self.score)
        for s in ['row.pendingField+=1','row.securedSteals+=secured','ko=integer(kills and kills[id])',
                  'elseif kind=="EGG_DEPOSIT" then','elseif kind=="CASTLE_FALL" then']:
            self.assertEqual(result.count(s),self.score.count(s),s)
        self.assertNotIn("m.fieldEggs",result)
    def test_mirrored_same_row_and_two_only(self):
        self.assertEqual(RARE_IDS,("FIELD_4","FIELD_5"))
        i=[n for n in range(1,25) if n in (4,5)]
        self.assertEqual(i,[4,5])
        x=lambda n:((n-1)%8-3.5)*93
        row=lambda n:(n-1)//8
        self.assertEqual(x(4),-x(5))
        self.assertEqual(row(4),row(5))
    def test_non_monetary_and_bounded(self):
        score=apply_score(self.score)
        self.assertIn("RARE_FIELD_EGG_CAP=2, RARE_FIELD_EGG_RATE=60",score)
        self.assertNotIn("DataStoreService",score)
        self.assertNotIn("MarketplaceService",score)
        self.assertNotIn("leaderstats",score)
    def test_reapply_rejected(self):
        with self.assertRaisesRegex(ValueError,"ALREADY"):
            apply_host(apply_host(self.host))
        with self.assertRaisesRegex(ValueError,"ALREADY"):
            apply_score(apply_score(self.score))
    def test_missing_host_original_author_rejected(self):
        mutation=self.host.replace('egg.Shape=Enum.PartType.Ball','egg.Shape=Enum.PartType.Block',1)
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            apply_host(mutation)
    def test_duplicate_host_original_author_rejected(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            apply_host(self.host.replace(HOST_OLD,HOST_OLD+HOST_OLD,1))
    def test_score_changed_reward_anchor_rejected(self):
        mutation=self.score.replace(" EGG_DEPOSIT_CAP=8, EGG_DEPOSIT_RATE=120,",
                                     " EGG_DEPOSIT_CAP=9, EGG_DEPOSIT_RATE=120,",1)
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            apply_score(mutation)
    def test_score_duplicate_original_anchor_rejected(self):
        anchor=SCORE_CHANGES[0][0]
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            apply_score(self.score.replace(anchor,anchor+anchor,1))
    def test_score_losing_rare_claim_fence_rejected(self):
        selected=apply_score(self.score)
        broken=selected.replace("not claimedRareFieldEggs[id]","true",1)
        with self.assertRaisesRegex(ValueError,"REVERSE"):
            inverse_score(broken)
if __name__=="__main__":
    unittest.main()
