"""Read-only full S1 spatial ring + independent two-defect Host/Binding overlay composition.
This verifies source/pack provenance and negative contracts, NOT native Luau runtime.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "candidate"
OVERLAY = ROOT / "overlay-source"
ORIGINAL = Path("handoffs/P0D-S1-D07-SPATIAL-STOMP-RING-20261111-01/candidate")
OVERLAY_GIT_BLOBS = {
    "S1CanonicalRoundHost": "61501c982619e54db6a09cf11b188ef872c1666e",
    "S1GoroganLiveBindings": "9cde26d7806a6ec20cd8648953eb37d1eefdc2c8",
}

def blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()

class CorrectedSpatialComposite(unittest.TestCase):
    def test_two_and_only_two_original_server_modules_changed(self):
        expected = {n + ".luau" for n in OVERLAY_GIT_BLOBS}
        for file in (GAME / "src/server").glob("*.luau"):
            old = ORIGINAL / "src/server" / file.name
            self.assertTrue(old.is_file(), file.name)
            if file.name in expected:
                self.assertNotEqual(file.read_bytes(), old.read_bytes())
            else:
                self.assertEqual(file.read_bytes(), old.read_bytes(), file.name)

    def test_independent_original_corrective_overlay_exact_bytes(self):
        for name, expected in OVERLAY_GIT_BLOBS.items():
            updated = GAME / "src/server" / (name + ".luau")
            source = OVERLAY / "src/server" / (name + ".luau")
            self.assertEqual(updated.read_bytes(), source.read_bytes(), name)
            self.assertEqual(blob(updated), expected, name)

    def test_full_original_server_AI_damage_v40_D08_unchanged(self):
        for name in [
            "ChaosEventCore", "CanonicalEventBridge",
            "TrustedGoroganActivationMapper", "GoroganServerAICore",
            "GoroganRigDriver", "GoroganAttackReceiptWindow",
            "GoroganDamageBoundary", "GoroganCombinedRuntime"
        ]:
            a = GAME / "src/server" / (name + ".luau")
            b = ORIGINAL / "src/server" / (name + ".luau")
            self.assertEqual(a.read_bytes(), b.read_bytes(), name)

    def test_base_game_server_and_HUD_unchanged(self):
        for name in [
            "src/server/Game.server.luau", "src/client/HUD.client.luau",
            "src/client/GoroganVisualPolicy.luau",
            "default.project.json",
        ]:
            self.assertEqual((GAME/name).read_bytes(), (ORIGINAL/name).read_bytes(), name)

    def test_only_client_replay_lifetime_fix(self):
        a = (ORIGINAL/"src/client/S1GoroganStompRing.client.luau").read_text("utf-8")
        b = (GAME/"src/client/S1GoroganStompRing.client.luau").read_text("utf-8")
        self.assertIn('lastEventId = nil', a)
        self.assertIn('local function endVisual()', b)
        self.assertIn('if result == "ENDED" then endVisual() end', b)
        self.assertIn('if result == "EXPIRED" then endVisual() end', b)
        self.assertIn('lastEventId = nil -- only reset for a NEW epoch', b)
        self.assertEqual(b.count("lastEventId = nil"),1)
        self.assertEqual(b.count("lastEventId = s.eventId"),1)
        self.assertIn('if visual ~= nil or lastEventId ~= nil', b)
        self.assertEqual(b.count("local function clearRound()"),1)

    def test_terminal_host_and_studio_negative_id_fixes_preserved(self):
        h = (GAME/"src/server/S1CanonicalRoundHost.luau").read_text("utf-8")
        bind = (GAME/"src/server/S1GoroganLiveBindings.luau").read_text("utf-8")
        self.assertIn('return true, "EVENT_FINISHED"',h)
        self.assertIn('m.serial ~= self.activeEpoch',h)
        self.assertIn('self.bridge.retired[key] ~= true',h)
        self.assertIn('playerId:match("^%-?%d+$")',bind)
        self.assertIn('tostring(player.UserId) == playerId',bind)
        self.assertIn("if found ~= nil then return nil end",bind)

    def test_only_one_server_bootstrap_and_existing_s1_remote(self):
        scripts=list((GAME/"src/server").glob("*.server.luau"))
        self.assertEqual([x.name for x in scripts],["Game.server.luau"])
        s=scripts[0].read_text("utf-8")
        self.assertEqual(s.count('Instance.new("RemoteEvent")'),1)
        self.assertEqual(s.count("OnServerEvent:Connect"),1)
        self.assertEqual(s.count("math.random(0, 99)"),1)
        self.assertNotIn("nextAlarmAt",s)

    def test_all_27_module_bytes_in_canonical_manifest(self):
        m=json.loads((GAME/"BUILD_MANIFEST.json").read_text("utf-8"))
        self.assertEqual(set(m), {"files", "format", "game_id","packet_id",
                                  "public_source_allowed","work_id"})
        self.assertEqual(len(m["files"]),27)
        names={x["path"] for x in m["files"]}
        self.assertEqual(len(names),27)
        self.assertIn("src/server/S1CanonicalRoundHost.luau",names)
        self.assertIn("src/server/S1GoroganLiveBindings.luau",names)
        self.assertIn("src/client/S1GoroganStompRing.client.luau",names)
        for item in m["files"]:
            b=(GAME/item["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),item["sha256"])
            self.assertEqual(len(b),item["size"])

    def test_owner_safety_gates_remain_explicitly_off(self):
        g=(GAME/"src/server/Game.server.luau").read_text("utf-8")
        self.assertIn("local CANONICAL_S1_ENABLED = false",g)
        self.assertIn("local D07_D08_RELEASE_REVIEW_APPROVED = false",g)
        self.assertNotIn("PublishAsync",g)
        self.assertNotIn("game:BindToClose",g)

if __name__ == "__main__":
    unittest.main()
