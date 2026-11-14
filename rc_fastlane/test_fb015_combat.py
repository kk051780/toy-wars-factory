#!/usr/bin/env python3
"""FB-008/015 source-exact and transactional-rollback regression tests.

No Roblox engine, multiplayer or subjective FUN acceptance is inferred.
"""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("apply_fb015_combat", ROOT / "apply_fb015_combat.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def unpatch_horde(patched: str) -> str:
    a = patched.index("                    -- Server-only confirmation: one changing cue per REAL hit.")
    b = patched.index("                    -- A normal enemy loses its immediate melee response", a)
    return patched[:a] + patched[b:]


def snapshot(path: Path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in path.rglob("*") if p.is_file()}


class ArtCombatContract(unittest.TestCase):
    def setUp(self):
        self.raw = mod.AUTHOR.read_bytes()
        self.src = self.raw.decode("utf8")
        self.patched_horde = mod.HORDE_AUTHOR.read_bytes()
        self.original_horde = unpatch_horde(self.patched_horde.decode("utf8")).encode("utf8")

    def _fixture(self, temp: Path):
        dist = temp / "game_dist"
        paths = {
            "server/MusouHorde.luau": self.original_horde,
            "server/Game.server.luau": b'remote.OnServerEvent:Connect(function() end)',
        }
        paths.update({f"shared/Original_{n:02d}.luau": f"return {n}\n".encode()
                      for n in range(64)})
        assert len(paths) == 66
        for rel, raw in paths.items():
            f = dist / "src" / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(raw)
        old = {name: mod.blob(raw) for name, raw in sorted(paths.items())}
        (dist / "SOURCE_LOCK.json").write_text(json.dumps({
            "total_scripts": 66, "blobs": old, "extra": "keep"}))
        (dist / "RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources": 66, "source_gitblobs": old, "feature_flags": {}}))
        (dist / "default.project.json").write_text(json.dumps({
            "tree": {
                "StarterPlayer": {"StarterPlayerScripts": {
                    "ResultNextStep": {"$path": "src/client/ResultNextStep.client.luau"}}},
                "ServerScriptService": {"TrapRaidersS1": {"$path": "src/server"}}
            }
        }))
        return dist

    def test_source_pins_and_exact_horde_seam(self):
        self.assertEqual(mod.blob(self.raw), mod.PIN)
        mod.validate_visual(self.raw)
        self.assertEqual(mod.blob(self.original_horde), mod.ORIGINAL_HORDE_PIN)
        mod.validate_horde_patch(self.original_horde, self.patched_horde)

    def test_confirmed_serial_signal_not_popup_or_local_attacker(self):
        for marker in ('GetAttributeChangedSignal("P0D_ART_HIT_V1")',
                       'serial <= state.lastSerial',
                       'state.lastSerial = serial',
                       'core.Position + Vector3.new(dx, 0, dz)',
                       'model:WaitForChild("Core", 15)',
                       'workspace:WaitForChild("TRAP_RAIDERS_S1")',
                       'raw:match("^(%d+)|([KH])|([^|]+)|([^|]+)$")'):
            self.assertIn(marker, self.src)
        self.assertNotIn('GetPropertyChangedSignal("Enabled")', self.src)
        self.assertNotIn('GetPropertyChangedSignal("Text")', self.src)
        self.assertNotIn('makeArc(core.Position, root.Position', self.src)
        self.assertIn('m.artHitSeq=(m.artHitSeq or 0)+1', self.patched_horde.decode())
        self.assertIn('m.body:SetAttribute("P0D_ART_HIT_V1"', self.patched_horde.decode())

    def test_budget_and_no_authority(self):
        for marker in ("MAX_LIVE = 8", "MAX_BURSTS_PER_SECOND = 9",
                       "if UserInputService.TouchEnabled then 1 else 2",
                       "Debris:AddItem(holder, .22)", "holder.CanCollide = false",
                       "holder.CanTouch = false", "holder.CanQuery = false",
                       "model.Destroying:Connect(function() detach(model) end)"):
            self.assertIn(marker, self.src)
        for forbidden in ("FireServer(", "TakeDamage(", "DataStoreService",
                          'Instance.new("RemoteEvent")', "UpdateAsync("):
            self.assertNotIn(forbidden, self.src)
        self.assertNotIn("RunService.Heartbeat:Connect(", self.src)

    def test_static_event_order_regression_two_same_damage_and_ko(self):
        # Representative transport grammar; separate client tests still need Studio.
        seq = 0
        events = []
        for value in ("−5", "−5", "💥 撃破！"):
            seq += 1
            packed = f"{seq}|{'K' if '撃破' in value else 'H'}|1.50|-2.20"
            events.append(packed)
        self.assertEqual(len(set(events)), 3)
        self.assertEqual([s.split("|")[1] for s in events], ["H", "H", "K"])
        # Popup Enabled/Text may remain unchanged for 2nd hit; version always changes.
        self.assertIn('GetAttributeChangedSignal("P0D_ART_HIT_V1")', self.src)

    def test_clean_off_zero_write_and_exact_applied_off_restores(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = self._fixture(Path(tmp))
            initial = snapshot(dist)
            self.assertFalse(mod.apply(dist, enabled=False))
            self.assertEqual(snapshot(dist), initial)
            self.assertTrue(mod.apply(dist, enabled=True))
            after = mod.sources(dist)
            self.assertEqual(len(after), 67)
            self.assertEqual(mod.blob(after[mod.HORDE]), mod.HORDE_PATCH_PIN)
            self.assertEqual(mod.blob(after[mod.DEST]), mod.PIN)
            self.assertEqual(mod.sources(mod.backup_dir(dist))[mod.HORDE], self.original_horde)
            self.assertTrue(mod.apply(dist, enabled=False))
            self.assertEqual(snapshot(dist), initial)
            self.assertFalse(mod.backup_dir(dist).exists())

    def test_staging_exception_preserves_clean_dist(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = self._fixture(Path(tmp))
            initial = snapshot(dist)
            with patch.object(mod, "_stage_candidate", side_effect=RuntimeError("SIMULATED_STAGE_FAILURE")):
                with self.assertRaisesRegex(RuntimeError, "SIMULATED_STAGE_FAILURE"):
                    mod.apply(dist, enabled=True)
            self.assertEqual(snapshot(dist), initial)
            self.assertFalse(mod.backup_dir(dist).exists())

    def test_source_drift_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = self._fixture(Path(tmp))
            initial = snapshot(dist)
            p = dist / "src/server/MusouHorde.luau"
            p.write_bytes(self.original_horde + b"-- DRIFT")
            altered = snapshot(dist)
            with self.assertRaisesRegex(AssertionError, "ORIGINAL_HORDE_DRIFT"):
                mod.apply(dist, enabled=True)
            self.assertEqual(snapshot(dist), altered)
            self.assertNotEqual(initial, altered)

    def test_off_missing_dist_no_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "missing"
            self.assertFalse(mod.apply(dist, enabled=False))
            self.assertFalse(dist.exists())


if __name__ == "__main__":
    unittest.main()
