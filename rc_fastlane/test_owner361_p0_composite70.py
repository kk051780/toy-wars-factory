"""P0-composite safety/authority tests; engine behavior must be Studio-tested."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json, ast, unittest
import apply_owner361_p0_composite70 as m

class CompositeP0PreviewTest(unittest.TestCase):
    def test_pinned_exact_authors(self):
        self.assertEqual(len(m.FEATURE_IDS),5)
        self.assertEqual(len(m.ADDED),4)
        self.assertEqual(len(m.CHANGED),4)
        self.assertEqual(len(set(m.FEATURE_IDS)),5)
        m.check_authors()
        ast.parse(Path(m.__file__).read_text("utf8"))

    def test_source_level_order_is_compatible(self):
        s=Path(m.__file__).read_text("utf8")
        self.assertIn('script=solo.patch_game(base)',s)
        self.assertIn('script=ready.patch_game(script)',s)
        self.assertIn('script=lobby.patch_game(script)',s)
        self.assertIn('v4=lobby.patch_v4(',s)
        self.assertIn('client=ready.patch_hud(',s)
        self.assertIn('config=ready.patch_config(',s)

    def test_active_map_bounds_are_flank_safe(self):
        s=Path(m.__file__).read_text("utf8")
        self.assertIn('position.X) > 182 or math.abs(position.Z) > 144',s)
        self.assertIn('grass.Size = Vector3.new(370, 4, 294)',s)
        self.assertIn('X182/Z144_ACTIVE_ONLY',s)
        self.assertTrue(m.castle.SOURCE.exists())

    def test_one_owner_no_second_game_or_remote(self):
        self.assertEqual(len([p for p in m.ADDED if p.endswith("/Game.server.luau")]),0)
        for dest,(p,pin) in m.ADDED.items():
            t=p.read_text("utf8")
            self.assertEqual(m.blob(p.read_bytes()),pin)
            self.assertNotIn('Instance.new("RemoteEvent")',t)
            self.assertNotIn('PromptProductPurchase(',t)
            self.assertNotIn('DataStoreService',t)
        self.assertIn('server/Game.server.luau',m.CHANGED)

    def test_disabled_is_completely_non_mutating_even_missing_dist(self):
        with TemporaryDirectory() as t:
            root=Path(t)/"missing_private70"
            self.assertFalse(m.apply(root,False))
            self.assertFalse(root.exists())

    def test_invalid_dist_refused_before_any_files_created(self):
        with TemporaryDirectory() as t:
            d=Path(t)
            with self.assertRaises(AssertionError):
                m.apply(d,True,d/"out")
            self.assertEqual(list(d.iterdir()),[])

    def test_composed_game_guard_against_partial_source(self):
        with self.assertRaises(AssertionError):
            m.patch_owner_game("irrelevant")

    def test_symlink_escape_fails_before_any_writes(self):
        with TemporaryDirectory() as t:
            outside=Path(t)/"victim.txt"
            outside.write_text("unmodified","utf8")
            d=Path(t)/"dist"
            d.mkdir()
            (d/"src").symlink_to(outside)
            with self.assertRaisesRegex(AssertionError,"P0_SYMLINK_REFUSED"):
                m.source_map(d)
            self.assertEqual(outside.read_text("utf8"),"unmodified")

    def test_original_dist_is_not_an_output_location(self):
        with TemporaryDirectory() as t:
            d=Path(t)/"dist"
            d.mkdir()
            with self.assertRaisesRegex(AssertionError,"OUTPUT_ALREADY_EXISTS"):
                m.apply(d,True,d)

    def test_gameplay_fixes_are_in_pinned_authors(self):
        r=m.ready.patch_game.__code__.co_consts
        src=Path(m.ready.__file__).read_text("utf8")
        self.assertIn('isReady = not isReady',src)
        self.assertIn('match.phase = "LOBBY"',src)
        self.assertIn("    broadcast()",src)
        self.assertLess(src.index('if match.phase ~= "LOBBY"'),src.index('lastSeq[player] = data.seq'))
        bot=Path(m.solo.__file__).read_text("utf8")
        self.assertIn('stopRound("DRAW","SOLO_BOTS_TICK_FAILURE")',bot)
        hud=m.hud.SOURCE.read_text("utf8")
        self.assertIn("originalScoreLayout",hud)
        self.assertIn("scoreLabel.Size = originalScoreLayout.Size",hud)
        self.assertIn("instructionLabel.Visible = true",hud)

    def test_duplicate_feature_rejected(self):
        self.assertEqual(len(set(m.FEATURE_IDS)),len(m.FEATURE_IDS))
        self.assertNotIn(m.ID,m.FEATURE_IDS)

    def test_original_input_paths_are_not_authored_second_versions(self):
        code=Path(m.__file__).read_text("utf8")
        for forbidden in ('os.system(', 'subprocess.run(', 'git push', 'git checkout -B',
                          'DataStoreService', 'MarketplaceService'):
            self.assertNotIn(forbidden,code)

    def test_source_metadata_explicitly_no_real_studio_claim(self):
        code=Path(m.__file__).read_text("utf8")
        for marker in ('"full_studio_fun":"NOT_TESTED"',
                       '"android":"NOT_TESTED"',
                       '"formal_rc_adoption":False',
                       '"62_original_byte_exact":True',
                       '"rollback":'):
            self.assertIn(marker,code)

if __name__=="__main__":
    unittest.main()
