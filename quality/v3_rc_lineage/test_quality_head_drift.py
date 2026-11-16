"""The original #484 often advances HEAD for tests; don't falsely stop a source intake.

These tests exercise the actual touched-path filter used after independently
fetching the two immutable Git trees. This cannot authorize RC CAS.
"""
import unittest

from verify_current26 import quality_gameplay_drift


class TestQualityOnlyHEADChanges(unittest.TestCase):
    def test_quality_test_only_changes_do_not_invalidate_pinned_game_source(self):
        self.assertEqual(quality_gameplay_drift([
            "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/tests/test_bot_spatial_quality.py",
            "quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/test_nav_retarget_native.py",
            ".github/workflows/p0d-eggrumble-gq-current26-private.yml",
            "quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/README.md",
        ]), [])

    def test_bot_router_changed_must_recompose(self):
        value = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_BotPathRouter.luau"
        self.assertEqual(quality_gameplay_drift([value]), [value])

    def test_castle_lobby_and_project_must_recompose(self):
        base = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/"
        changed = [base+"EGGRUMBLE_LobbyCastleModesPreview.server.luau",
                   base+"EGGRUMBLE_V3_STUDIO.project.json"]
        self.assertEqual(quality_gameplay_drift(changed), changed)

    def test_original_composer_change_is_game_source_drift(self):
        script = "quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/compose.py"
        self.assertEqual(quality_gameplay_drift([script]), [script])

    def test_unrelated_art_or_score_owner_does_not_fake_quality_scope(self):
        self.assertEqual(quality_gameplay_drift([
            "handoffs/EGGRUMBLE-ART-SILHOUETTE-FIELD-20261116/EGGRUMBLE_FlagshipFieldArt.server.luau",
            "quality/v3_rc_lineage/verify_current26.py",
        ]), [])


if __name__ == "__main__":
    unittest.main()
