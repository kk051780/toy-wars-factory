#!/usr/bin/env python3
"""Offline negative tests for one original-author source-locked spatial repair."""
import unittest

from patch_ridge import (
    HOST, ITEMS, ORIGINAL_GIT_BLOB, NEW, OLD,
    collision_report, git_blob, patch_author_host,
)


class CentralRidgeClearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = HOST.read_text(encoding="utf-8")
        cls.items = ITEMS.read_text(encoding="utf-8")

    def test_01_original_head_blob_is_pinned(self):
        self.assertEqual(git_blob(self.host), ORIGINAL_GIT_BLOB)

    def test_02_real_item_site_is_center_route_shield(self):
        self.assertIn('{x=0,z=470,kind="SHIELD"}', self.items)
        self.assertIn('xCenter=if session.mode=="TEAM" then -620 else 620', self.items)
        self.assertEqual(self.items.count('{x=0,z=470,kind="SHIELD"}'), 1)

    def test_03_original_collidable_ridge_embeds_item(self):
        self.assertEqual(self.host.count(OLD), 1)
        self.assertIn('p.Anchored=true', self.host)
        self.assertTrue(collision_report()["before_embedded_in_collidable_ridge"])

    def test_04_patch_changes_only_one_host_block(self):
        patched = patch_author_host(self.host, self.items)
        self.assertEqual(patched.count(NEW), 1)
        self.assertEqual(patched.replace(NEW, OLD), self.host)
        self.assertNotIn(OLD, patched)
        self.assertEqual(HOST.read_text(encoding="utf-8"), self.host)

    def test_05_middle_corridor_safely_clears_pickup(self):
        report = collision_report()
        self.assertEqual(report["after_open_passage_studs"], 24)
        self.assertGreaterEqual(report["after_pickup_edge_margin_each_side_studs"], 10)
        self.assertFalse(report["engine_verified"])
        # Shoulder A [-647,-632], shoulder B [-608,-593] in local arena X.
        shoulders = ((-647.0, -632.0), (-608.0, -593.0))
        self.assertAlmostEqual(shoulders[1][0]-shoulders[0][1], 24)
        # SHIELD sphere and human clearance radius do not intersect shoulders.
        self.assertLess(-620+1.1+2.0, shoulders[1][0])
        self.assertGreater(-620-1.1-2.0, shoulders[0][1])

    def test_06_battle_lobby_and_other_mode_left_alone(self):
        patched = patch_author_host(self.host, self.items)
        for token in (
            'MODE_SEATS=16', 'COUNTDOWN=12',
            '"BATTLE_ROYALE"', '"TEAM"',
            'Rules.start(session.rules)',
            'BotActors.start(session,Rules)',
            'SwarmCombat.start(session)',
            'RaidItemIntake.start(session,root,FieldItems)',
            'for j=1,3 do',
            'session.closeRound=function',
            'SevenRoleCombat.equip(session,p,role)',
        ):
            self.assertEqual(patched.count(token), self.host.count(token))
        self.assertIn('if mode=="TEAM" then\n  -- GQ ridge access:', patched)

    def test_07_reject_stale_original_author_blob(self):
        with self.assertRaisesRegex(ValueError, "original #482 host Git blob changed"):
            patch_author_host(self.host.replace('MODE_SEATS=16', 'MODE_SEATS=32'), self.items)

    def test_08_reject_original_item_lane_drift(self):
        with self.assertRaisesRegex(ValueError, "item site changed"):
            patch_author_host(self.host, self.items.replace('x=0,z=470,kind="SHIELD"', 'x=50,z=470,kind="SHIELD"'))

    def test_09_reject_mode_origin_drift(self):
        with self.assertRaisesRegex(ValueError, "mode origin changed"):
            patch_author_host(self.host, self.items.replace('then -620 else 620', 'then -600 else 620'))

    def test_10_refuse_repeat_application(self):
        modified = patch_author_host(self.host, self.items)
        with self.assertRaisesRegex(ValueError, "original #482 host Git blob changed"):
            patch_author_host(modified, self.items)

    def test_11_no_second_game_or_item_author(self):
        patched = patch_author_host(self.host, self.items)
        self.assertEqual(patched.count('local Players=game:GetService("Players")'), 1)
        self.assertEqual(patched.count('local FieldItems=require('), 1)
        self.assertEqual(patched.count('session.itemIntakeStarted'), self.host.count('session.itemIntakeStarted'))

    def test_12_span_stays_same_and_mode_guard_is_retained(self):
        patched = patch_author_host(self.host, self.items)
        self.assertIn('local sideWidth=(54-centerPassage)/2', patched)
        self.assertIn('local ridgeOffset=side*(centerPassage/2+sideWidth/2)', patched)
        self.assertIn('if side==-1 then "CentralRidge" else "CentralRidgeRight"', patched)
        self.assertEqual(patched.count('local centerPassage=24'), 1)


if __name__ == "__main__":
    unittest.main()
