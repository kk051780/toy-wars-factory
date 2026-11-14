"""P0 FB005 original #400 pathfinder/unstuck in real 78 scripts."""
import tempfile,unittest
from pathlib import Path
from rc_fastlane import apply_p0_bot_unstuck78 as m

class BotUnstuck78(unittest.TestCase):
    def test_movement_only_and_all_other_sources_byte_exact(self):
        s=Path(m.__file__).read_text("utf8")
        self.assertEqual(m.BOT,"server/SoloTeamBots.luau")
        for phrase in (
            'MAX_INFLIGHT_PATHS=10','inflightPaths=math.max(0,inflightPaths-1)',
            '(goal-position).Magnitude>=6',
            'now-bot.lastProgressAt>=5',
            'bot.hum:MoveTo(position+detour)',
            'bot.lastGoal=goal',
            'bot.unstuckAttempts=((bot.unstuckAttempts or 0)%4)+1',
            'other77_source_bytes_exact','new_feature_ids":0',
            'assert {p for p in prev if after[p]!=prev[p]}=={BOT}',
            'assert read(base)==prev', 'os.replace(stage,out)'):
            self.assertIn(phrase,s,phrase)
    def test_off_exact_zero_and_bad_base_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            self.assertFalse(m.apply(p/"missing",p/"new",False))
            self.assertFalse((p/"new").exists())
            (p/"bad").mkdir()
            with self.assertRaises(AssertionError):
                m.apply(p/"bad",p/"new",True)
            self.assertFalse((p/"new").exists())
    def test_author_24_case_fixture_exact_source_contract(self):
        s=(Path(m.__file__).parent/"verify_p0_bot_unstuck78_native.py").read_text("utf8")
        for phrase in ('REAL_START_CREATES_FIVE_BOTS',
           'REAL_START_TWO_ALLIES_THREE_ENEMIES',
           'STALLED_HUMANOID_JUMPS',
           'FIRST_STUCK_LATERAL_DETOUR',
           'SECOND_STUCK_ATTEMPT_REVERSES_SIDE',
           'ACTUAL_MOVEMENT_RESETS_STALL_COUNTER',
           'GOAL_CHANGE_MOVES_NEW_DESTINATION',
           'PRODUCTION_NONSTUDIO_DISABLED'):
            self.assertIn(phrase,s,phrase)
    def test_stuck_detector_guards_melee_no_jitter(self):
        s=Path(m.__file__).read_text("utf8")
        self.assertIn('elseif (goal-position).Magnitude>=6 and now-bot.lastProgressAt>=5 then',s)
        self.assertNotIn('Instance.new("RemoteEvent")',s)
        self.assertIn('new_script_count":0',s)
        self.assertIn('new_game":False',s)

if __name__=="__main__": unittest.main()
