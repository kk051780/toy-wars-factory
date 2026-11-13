"""Source-locked integration preflight, not an actual Luau/Studio execution."""
from pathlib import Path
import hashlib
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RULES = (ROOT / "src/S1First90ClassicWaypointRules.luau").read_text(encoding="utf-8")
GAME_PATH = REPO / "releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau"
COACH_PATH = REPO / "releases/P0D_S1_KIDS_RC01/src/client/FirstMinuteCoach.client.luau"
MODEL_PATH = REPO / "releases/P0D_S1_KIDS_RC01/src/shared/FirstMinuteModel.luau"

# These authoritative source blobs were inspected on frozen RC HEAD
# 1263a03701211a652b99b91d2339575dc8104eff.
EXPECTED_GAME_GIT_BLOB = "7c5229f600f17537bc1bbbb0b96b6a2435875374"
EXPECTED_COACH_GIT_BLOB = "63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9"
EXPECTED_MODEL_GIT_BLOB = "fcdc399bf95b6cd0532691718f5a54e8a4fd84b4"


def git_blob(path: Path) -> str:
    content = path.read_bytes()
    raw = b"blob " + str(len(content)).encode() + b"\0" + content
    return hashlib.sha1(raw).hexdigest()


# Python reference fixture only; models admission requirements, does not
# claim that the Luau source was executed in a Roblox/Luau runtime.
def reference_select(s):
    if not isinstance(s, dict) or s.get("phase") != "ACTIVE" or s.get("alive") is not True:
        return None
    if s.get("team") not in ("RED", "BLUE"):
        return None
    serial, seconds = s.get("serial"), s.get("elapsedSeconds")
    if type(serial) is not int or not (1 <= serial <= 100000000):
        return None
    if type(seconds) not in (int, float) or not (0 <= seconds < 90):
        return None

    def valid_point(p):
        return isinstance(p, dict) and all(
            type(p.get(k)) in (int, float) and lo <= p[k] <= hi
            for k, lo, hi in (("x", -200, 200), ("y", -50, 100), ("z", -120, 120))
        )

    if s.get("carryingEgg") is True:
        if s.get("ownEggHome") is False:
            return {"kind": "RECOVER"}
        if s.get("ownEggHome") is not True or not valid_point(s.get("ownScorePad")):
            return None
        return {"kind": "HOME", **s["ownScorePad"]}
    if s.get("carryingEgg") is not False:
        return None
    if any(s.get(k) is not True for k in (
        "enemyEggFree", "enemyPromptEnabled", "enemyEggVisible"
    )):
        return None
    if not valid_point(s.get("enemyEgg")):
        return None
    return {"kind": "EGG", **s["enemyEgg"]}


def base():
    return {
        "serial": 1, "phase": "ACTIVE", "team": "RED", "alive": True,
        "elapsedSeconds": 10, "carryingEgg": False, "ownEggHome": True,
        "enemyEggFree": True, "enemyPromptEnabled": True,
        "enemyEggVisible": True, "enemyEgg": {"x": 88, "y": 3, "z": 0},
        "ownScorePad": {"x": -90, "y": 3, "z": 0},
    }


class SourceContract(unittest.TestCase):
    def test_original_rc_game_exact(self):
        self.assertEqual(git_blob(GAME_PATH), EXPECTED_GAME_GIT_BLOB)

    def test_original_rc_client_exact(self):
        self.assertEqual(git_blob(COACH_PATH), EXPECTED_COACH_GIT_BLOB)
        self.assertEqual(git_blob(MODEL_PATH), EXPECTED_MODEL_GIT_BLOB)

    def test_existing_single_authority(self):
        src = GAME_PATH.read_text(encoding="utf-8")
        self.assertIn('error("DUPLICATE_S1_RUNTIME:', src)
        self.assertEqual(src.count('Instance.new("RemoteEvent")'), 1)
        self.assertEqual(src.count('remote.OnServerEvent:Connect'), 1)
        self.assertIn("match.startedAt = serverNow()", src)
        self.assertIn("map.teams[team].scorePad", src)

    def test_new_policy_read_only(self):
        forbidden = ["RemoteEvent", "DataStore", "Instance.new", ":FireServer",
                     "OnServerEvent", "UpdateAsync", "HttpService", "SetAsync"]
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, RULES)
        self.assertIn("function Rules.select(", RULES)
        self.assertIn('return {kind = "RECOVER"}', RULES)
        self.assertIn('coords("EGG"', RULES)

    def test_requires_server_verified_original_egg(self):
        for token in ("enemyEggFree", "enemyPromptEnabled", "enemyEggVisible",
                      "ownEggHome", "elapsedSeconds", "snapshot.alive"):
            with self.subTest(token=token):
                self.assertIn(token, RULES)


class BehavioralReference(unittest.TestCase):
    def test_eligible_egg(self):
        self.assertEqual(reference_select(base()), {"kind": "EGG", "x": 88, "y": 3, "z": 0})

    def test_carry_return_own_pad(self):
        v = base()
        v["carryingEgg"] = True
        self.assertEqual(reference_select(v), {"kind": "HOME", "x": -90, "y": 3, "z": 0})

    def test_cannot_score_recover_without_leaking_enemy_carrier(self):
        v = base()
        v["carryingEgg"] = True
        v["ownEggHome"] = False
        self.assertEqual(reference_select(v), {"kind": "RECOVER"})

    def test_unavailable_egg_fails_closed(self):
        for k in ("enemyEggFree", "enemyPromptEnabled", "enemyEggVisible"):
            v = base()
            v[k] = False
            with self.subTest(k=k):
                self.assertIsNone(reference_select(v))

    def test_round_end_and_90_seconds(self):
        for phase, sec in (("LOBBY", 10), ("RESULTS", 10),
                           ("ACTIVE", 90), ("ACTIVE", -1)):
            v = base()
            v["phase"], v["elapsedSeconds"] = phase, sec
            with self.subTest(phase=phase, sec=sec):
                self.assertIsNone(reference_select(v))

    def test_no_ghost_coordinate(self):
        for bad in (None, {}, {"x": 100000, "y": 3, "z": 0},
                    {"x": float("nan"), "y": 3, "z": 0}):
            v = base()
            v["enemyEgg"] = bad
            with self.subTest(bad=bad):
                self.assertIsNone(reference_select(v))

    def test_carry_home_unknown_not_assumed(self):
        v = base()
        v["carryingEgg"], v["ownEggHome"] = True, None
        self.assertIsNone(reference_select(v))

    def test_only_living_authenticated_team(self):
        for k, bad in (("team", "NONE"), ("alive", False),
                       ("serial", 0), ("serial", 2.3)):
            v = base()
            v[k] = bad
            with self.subTest(k=k):
                self.assertIsNone(reference_select(v))


if __name__ == "__main__":
    unittest.main()
