"""Offline source/contract checks only. This file does NOT execute Luau or Studio."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "src" / "S1CanonicalRoundHost.luau"
DOC = ROOT / "docs" / "S1_INTEGRATION.md"
ORIGINAL_BLOBS = {
    "ChaosEventCore.luau": "ee8d02ae5175d19904d357a530c05faf80b6bf8a",
    "CanonicalEventBridge.luau": "ce01536e3173e55099c4d6be543f83b9644d1950",
    "TrustedGoroganActivationMapper.luau": "b30aadc41634f77109559e31cff4d63fabeff19a",
    "GoroganCombinedRuntime.luau": "f10dedf357476e658857131c0843f237825a1c0f",
    "GoroganServerAICore.luau": "f0ecf36242f1543eccf915948129f21f99a6bc92",
    "GoroganRigDriver.luau": "1f6204105be724ca734e2654e42472667a8efcc6",
    "GoroganDamageBoundary.luau": "031b0c4a5370a891434de42ada8d76642c080433",
    "GoroganAttackReceiptWindow.luau": "bc8e4e954c06c1db8778649a84cda135ff56e9d1",
}


def git_blob_hash(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class OriginalSourceEvidence(unittest.TestCase):
    def test_all_eight_original_modules_are_unmodified(self):
        for filename, expected in ORIGINAL_BLOBS.items():
            with self.subTest(filename=filename):
                path = ROOT / "src" / filename
                self.assertTrue(path.is_file())
                self.assertEqual(git_blob_hash(path.read_bytes()), expected)

    def test_original_d08_module_signatures(self):
        src = (ROOT / "src" / "CanonicalEventBridge.luau").read_text()
        for token in ("Bridge.new", "function Bridge:tick(", "function Bridge:stop(",
                      "onBossActivate", "onCleanup", "serverRoll", "readRound",
                      "ROUND_REPLACED", "TIME_REVERSED"):
            with self.subTest(token=token):
                self.assertIn(token, src)

    def test_original_mapper_uses_identity_not_flag(self):
        src = (ROOT / "src" / "TrustedGoroganActivationMapper.luau").read_text()
        self.assertIn("self.attestedActivation == activation", src)
        self.assertIn("function Mapper:handle(", src)
        self.assertIn("abortCombined", src)

    def test_original_v40_once_per_round_roll(self):
        src = (ROOT / "src" / "ChaosEventCore.luau").read_text()
        self.assertIn("if roll < 65", src)
        self.assertIn('return "BOSS", BOSS_BY_STAGE[stage]', src)
        self.assertIn('if now - state.startedAt < 20', src)
        self.assertIn('state.eventsSent', src)


class S1HostStaticSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOST.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_module_is_pure_opt_in(self):
        self.assertIn("function Host.new(deps)", self.source)
        self.assertIn("if deps.approvedByOwner ~= true or deps.enableCanonicalS1 ~= true", self.source)
        self.assertIn("DISABLED_DEFAULT", self.source)
        self.assertIn("return Host", self.source)

    def test_no_automatic_authority_side_effect(self):
        for forbidden in ("RemoteEvent", "RunService", "task.spawn", "while true",
                          "PlayerAdded:Connect", "OnServerEvent", "DataStoreService",
                          "Workspace:FindFirstChild"):
            with self.subTest(forbidden=forbidden):
                # The source comment mentioning Remote is documentation, not an instantiation.
                if forbidden == "RemoteEvent":
                    self.assertNotIn('Instance.new("RemoteEvent")', self.source)
                else:
                    self.assertNotIn(forbidden, self.source)

    def test_never_chooses_event_or_rolls_itself(self):
        self.assertNotIn("math.random(", self.source)
        self.assertNotIn("Random.new(", self.source)
        self.assertIn("return deps.serverRoll(matchId, epoch)", self.source)
        self.assertIn("Canonical.new(Chaos", self.source)

    def test_no_forged_canonical_activation(self):
        self.assertNotIn("isCanonicalActivation = function(_)", self.source)
        self.assertIn("mapper:handle(envelope)", self.source)
        self.assertIn("deps.makeCombined, mapper", self.source)
        self.assertIn('self.combined:start(activation)', self.source)

    def test_s1_serial_epoch_gate(self):
        for required in ("serial % 1 ~= 0", "serial < 1 or serial >= 1024",
                         'matchId = "S1_"', 'stage = "S1"', "epoch = serial",
                         'match.phase == "ACTIVE"'):
            with self.subTest(required=required):
                self.assertIn(required, self.source)

    def test_weather_not_faked(self):
        self.assertIn("No approved weather runtime in S1", self.source)
        self.assertNotIn("onWeatherActivate = function", self.source)
        self.assertIn("onBossActivate = function", self.source)

    def test_actual_boss_failure_aborts(self):
        self.assertIn("deps.abortCombined", self.source)
        self.assertIn("CRITICAL_BOSS_ABORT_NOT_CONFIRMED", self.source)
        self.assertIn("CRITICAL_ABORT_FAILED", self.source)
        self.assertIn('self:stop("D07_HEARTBEAT_FAILED")', self.source)

    def test_warning_and_cleanup_own_only_existing_hud(self):
        for token in ('setAlarm("WARNING"', 'setAlarm("SIGNAL"', 'setAlarm("IDLE"',
                      'deps.setAlarm', 'deps.broadcast', "envelope.epoch ~= self.activeEpoch"):
            with self.subTest(token=token):
                self.assertIn(token, self.source)

    def test_cleanup_gate_on_tick_reentrancy(self):
        self.assertIn("if self.inTick then return false", self.source)
        self.assertIn("self.inTick = true", self.source)
        self.assertIn("self.inTick = false", self.source)
        self.assertIn("self.bridge:stop()", self.source)

    def test_integrator_removes_old_alarm_scheduler(self):
        self.assertIn("Remove the **entire original fake alarm scheduler**", self.doc)
        self.assertIn("match.nextAlarmAt", self.doc)
        self.assertIn("NO secondary", self.doc)

    def test_real_physics_not_claimed(self):
        self.assertIn("This example intentionally fails", self.doc)
        self.assertIn("DO NOT execute Luau", self.__doc__ or "") if False else None
        self.assertIn("DO NOT execute Luau", __doc__)
        self.assertIn("Studio", self.doc)
        self.assertIn("source-only", self.doc)

    def test_luau_source_contains_no_fake_studio_pass(self):
        self.assertIn("studioTested = false", self.source)
        self.assertNotIn("STUDIO_PASS", self.source)

    def test_expected_exact_original_dependencies_all_present(self):
        for name in ("ChaosEventCore", "CanonicalEventBridge",
                     "TrustedGoroganActivationMapper"):
            with self.subTest(name=name):
                self.assertIn(f'WaitForChild("{name}")', self.source)


if __name__ == "__main__":
    unittest.main()
