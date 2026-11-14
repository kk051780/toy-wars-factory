import tempfile,unittest
from pathlib import Path
from rc_fastlane import apply_p0_round_epoch78 as m

class RoundEpochRole78(unittest.TestCase):
    def test_fenced_original_authority(self):
        s=Path(m.__file__).read_text("utf8")
        for required in ("local startupSerial=match.serial",
          'if match.phase~="ACTIVE" or match.serial~=startupSerial then return end',
          'player:GetAttribute("P0D_LateJoinSpectator")==true',
          'roles[entrant]="RAIDER"',
          'lastRoleChange[entrant]=-math.huge',
          'assert {p for p in original if original[p]!=result[p]}=={GAME}',
          'other77_sources_byte_exact', "assert read(base)==original",
          "assert not out.exists()", "os.replace(stage,out)"):
            self.assertIn(required,s)
        self.assertEqual(m.GAME,"server/Game.server.luau")
    def test_off_zero_write_and_bad_parent_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            self.assertFalse(m.apply(p/"absent",p/"candidate",False))
            self.assertFalse((p/"candidate").exists())
            (p/"wrong").mkdir()
            with self.assertRaises(AssertionError):
                m.apply(p/"wrong",p/"candidate",True)
            self.assertFalse((p/"candidate").exists())
    def test_replay_marker_and_epoch_outside_reset_forbidden(self):
        text=Path(m.__file__).read_text("utf8")
        self.assertIn('assert FEATURE not in src',text)
        self.assertIn('src.count("local function resetRound()")==1',text)
        self.assertIn('src.count("remote.OnServerEvent:Connect(")==1',text)
        self.assertIn('body.index(EPOCH_GUARD)<body.index("setObjectiveEnabled(true)")',text)
        self.assertIn('body.index(EPOCH_GUARD)<body.index("startCanonical()")',text)
    def test_race_proof_is_separate_from_feature_expansion(self):
        self.assertIn("scripts\":78",Path(m.__file__).read_text("utf8"))
        self.assertIn("new_feature_ids\":0",Path(m.__file__).read_text("utf8"))
if __name__=="__main__":unittest.main()
