"""The complete five-art preview must never mutate canonical RC66."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from rc_fastlane import build_art_composite as art


class FiveArtCandidateSafety(unittest.TestCase):
    def test_all_five_real_source_blobs(self):
        self.assertEqual(len(art.pinned_art()),5)

    def test_composite_includes_no_server_game_replacement(self):
        a=art.pinned_art()
        self.assertEqual(set(a),{
            "server/CastleBattlefield.server.luau",
            "server/FantasyWorldArt.server.luau",
            "server/H1CoastalSeascape.server.luau",
            "server/ArtMinionSilhouette.server.luau",
            "client/FB015CharacterArt.client.luau",
        })
        self.assertNotIn("server/Game.server.luau",a)
        self.assertNotIn("server/GoroganRigDriver.luau",a)

    def test_minion_and_gorogan_cosmetics_have_distinct_owners(self):
        a=art.pinned_art()
        self.assertNotIn(b"MUSOU_MINION_",a["client/FB015CharacterArt.client.luau"])
        self.assertNotIn(b"Gorogan_ServerRig",a["server/ArtMinionSilhouette.server.luau"])

    def test_reject_missing_source_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist=Path(tmp)/"none"
            candidate=Path(tmp)/"scratch"
            with self.assertRaises(AssertionError):
                art.compose(dist,candidate)
            self.assertFalse(candidate.exists())

    def test_all_sources_have_valid_sha_pins(self):
        for category,pin,path,name,flag in art.SPECS:
            self.assertEqual(art.gitblob((art.ART/name).read_bytes()),pin)


if __name__=="__main__":
    unittest.main()
