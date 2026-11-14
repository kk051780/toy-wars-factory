"""The complete six-art preview must never mutate canonical RC66."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from rc_fastlane import build_art_composite as art


class SixArtCandidateSafety(unittest.TestCase):
    def test_all_five_real_source_blobs(self):
        self.assertEqual(len(art.pinned_art()),6)

    def test_composite_includes_no_server_game_replacement(self):
        a=art.pinned_art()
        self.assertEqual(set(a),{
            "server/CastleBattlefield.server.luau",
            "server/FantasyWorldArt.server.luau",
            "server/H1CoastalSeascape.server.luau",
            "server/H1SeaGroundRepair.server.luau",
            "server/ArtMinionSilhouette.server.luau",
            "client/FB015CharacterArt.client.luau",
        })
        self.assertNotIn("server/Game.server.luau",a)
        self.assertNotIn("server/GoroganRigDriver.luau",a)

    def test_minion_and_gorogan_cosmetics_have_distinct_owners(self):
        a=art.pinned_art()
        self.assertNotIn(b"MUSOU_MINION_",a["client/FB015CharacterArt.client.luau"])
        self.assertNotIn(b"Gorogan_ServerRig",a["server/ArtMinionSilhouette.server.luau"])

    def test_coastal_solid_floor_is_carved_into_real_water_and_dry_paths(self):
        scripts=art.pinned_art()
        code=scripts["server/H1SeaGroundRepair.server.luau"].decode("utf8")
        self.assertIn('if not RunService:IsStudio() then return end',code)
        self.assertIn('sea:GetAttribute("WaterTerrainCreated")==true',code)
        self.assertIn('math.abs(grass.Size.X-370)',code)
        self.assertIn('dryLand("NORTH_HIGHLANDS"',code)
        self.assertIn('dryLand("SOUTH_MAINLAND"',code)
        self.assertIn('dryLand("WEST_COAST_FLANK"',code)
        self.assertIn('dryLand("EAST_COAST_FLANK"',code)
        self.assertIn('grass.Transparency = 1',code)
        self.assertIn('grass.CanCollide = false',code)
        self.assertIn('terrain:FillBlock(',code)
        self.assertIn('Vector3.new(246,7,52)',code)
        self.assertIn('Vector3.new(side*85,-2.95,-53)',code)
        self.assertIn('SeaRouteVisualOnly',scripts["server/H1CoastalSeascape.server.luau"].decode("utf8"))
        self.assertNotIn('Instance.new("RemoteEvent")',code)

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
