#!/usr/bin/env python3
"""Regression of actual #381 overlay followed by exact #374 3D minion source."""
from __future__ import annotations
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

slash = load("apply_combat_art", "apply_fb015_combat.py")
combo = load("compose_minion_combat", "compose_fb015_minion_combat.py")

QA = load("p0d_art_combat_real_test_fixture", "test_fb015_combat.py")

def original_horde():
    return QA.original_horde()

def snapshot(d):
    return {p.relative_to(d).as_posix():p.read_bytes()
            for p in d.rglob("*") if p.is_file()}

def fixture(root):
    dist = root / "base66"
    items = {
        "server/MusouHorde.luau": original_horde(),
        "server/Game.server.luau": b'remote.OnServerEvent:Connect(function() end)',
    }
    items.update({f"shared/Original_{i:02d}.luau": f"return {i}\n".encode()
                  for i in range(64)})
    for path, raw in items.items():
        d = dist / "src" / path
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_bytes(raw)
    pins = {k:slash.blob(v) for k,v in sorted(items.items())}
    (dist/"SOURCE_LOCK.json").write_text(json.dumps({"total_scripts":66,"blobs":pins}))
    (dist/"RC_FEATURE_LOCK.json").write_text(json.dumps({
        "total_sources":66,"source_gitblobs":pins,"feature_flags":{}}))
    (dist/"default.project.json").write_text(json.dumps({
        "tree":{
            "ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}},
            "StarterPlayer":{"StarterPlayerScripts":{
                "ResultNextStep":{"$path":"src/client/ResultNextStep.client.luau"}}}
        }}))
    return dist

class CompositeTest(unittest.TestCase):
    def test_minion_source_keeps_four_species_with_confirmed_sparks(self):
        self.assertEqual(combo.blob(combo.AUTHOR.read_bytes()), combo.PIN)
        self.assertIn(b"ELITE_BACK_BANNER",combo.AUTHOR.read_bytes())
        self.assertIn(b'core:GetAttributeChangedSignal("P0D_ART_SPARK_V1")',
                      combo.AUTHOR.read_bytes())
        self.assertNotIn(b"local flashing = item.core.Color.R > .9",
                         combo.AUTHOR.read_bytes())
        h=slash.HORDE_AUTHOR.read_bytes()
        self.assertIn(b'if RunService:IsStudio() then',h)
        self.assertIn(b'if self.artCue then',h)
        self.assertIn(b'm.body:SetAttribute("P0D_ART_SPARK_V1"',h)
        self.assertNotIn(b'OnServerEvent:Connect(',h)

    def test_compose_exact_real_66_67_68_and_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            dist=fixture(root)
            original=snapshot(dist)
            self.assertTrue(slash.apply(dist, True))
            prev=snapshot(dist)
            output=root/"private68"
            self.assertTrue(combo.compose(dist, output, True))
            scripts=combo.files(output)
            self.assertEqual(len(scripts), 68)
            self.assertEqual(scripts["server/ArtMinionSilhouette.server.luau"],combo.AUTHOR.read_bytes())
            self.assertEqual(len(combo.files(dist)),67)
            self.assertEqual(snapshot(dist),prev)
            self.assertEqual(json.loads((output/"SOURCE_LOCK.json").read_text())["total_scripts"],68)
            self.assertEqual(json.loads((output/"RC_FEATURE_LOCK.json").read_text())["total_sources"],68)
            self.assertTrue(combo.compose(dist, output, False))
            self.assertFalse(output.exists())
            self.assertEqual(snapshot(dist),prev)
            self.assertTrue(slash.apply(dist, False))
            self.assertEqual(snapshot(dist),original)

    def test_fail_closed_if_source_or_horde_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            dist=fixture(root)
            slash.apply(dist,True)
            p=dist/"src/server/MusouHorde.luau"
            p.write_bytes(p.read_bytes()+b"DRIFT")
            out=root/"private68"
            with self.assertRaisesRegex(RuntimeError,"SOURCE_PIN_HORDE_SIGNAL_DRIFT"):
                combo.compose(dist,out,True)
            self.assertFalse(out.exists())

    def test_private68_off_zero_write_if_not_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertFalse(combo.compose(root/"missing",root/"private68",False))
            self.assertFalse((root/"private68").exists())
            self.assertEqual(list(root.iterdir()),[])

    def test_off_never_deletes_ancestor_of_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            with self.assertRaisesRegex(RuntimeError,"PRIVATE_OUTPUT_MUST_BE_SEPARATE"):
                combo.compose(d,root,False)
            self.assertTrue(d.exists())

    def test_off_never_deletes_unrelated_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            slash.apply(d,True)
            output=root/"private68"
            combo.compose(d,output,True)
            unrelated=output/"SAVED_UNRELATED_FILE.txt"
            unrelated.write_text("DO NOT DELETE",encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,"ROLLBACK_REFUSED_ADDED_OR_MODIFIED_OR_MISSING_FILE"):
                combo.compose(d,output,False)
            self.assertEqual(unrelated.read_text("utf8"),"DO NOT DELETE")
            unrelated.unlink()
            self.assertTrue(combo.compose(d,output,False))
            self.assertFalse(output.exists())

    def test_interrupted_composite_off_cleanup_recover(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            slash.apply(d,True)
            original67=snapshot(d)
            output=root/"private68"
            combo.compose(d,output,True)
            record=combo.verify_private_output(output,d)
            journal=output.with_name(output.name+".fb015_delete_journal.json")
            tombstone=output.with_name(output.name+".fb015_deleting")
            journal.write_text(json.dumps(record)+"\n",encoding="utf8")
            os.rename(output,tombstone)
            self.assertTrue(combo.compose(d,output,False))
            self.assertFalse(journal.exists())
            self.assertFalse(tombstone.exists())
            self.assertFalse(output.exists())
            self.assertEqual(snapshot(d),original67)

    def test_refuse_changed_partially_deleted_tombstone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            slash.apply(d,True)
            output=root/"private68"
            combo.compose(d,output,True)
            record=combo.verify_private_output(output,d)
            journal=output.with_name(output.name+".fb015_delete_journal.json")
            tombstone=output.with_name(output.name+".fb015_deleting")
            journal.write_text(json.dumps(record)+"\n",encoding="utf8")
            os.rename(output,tombstone)
            rogue=tombstone/"INTRUDER_SAVED.txt"
            rogue.write_text("KEEP ME",encoding="utf8")
            with self.assertRaisesRegex(RuntimeError,"TOMBSTONE_EXTRA_OR_MODIFIED_FILE_ROLLBACK_REFUSED"):
                combo.compose(d,output,False)
            self.assertEqual(rogue.read_text("utf8"),"KEEP ME")
            rogue.unlink()
            self.assertTrue(combo.compose(d,output,False))
            self.assertFalse(tombstone.exists())

    def test_no_enable_while_rollback_tombstone_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            slash.apply(d,True)
            output=root/"private68"
            combo.compose(d,output,True)
            record=combo.verify_private_output(output,d)
            journal=output.with_name(output.name+".fb015_delete_journal.json")
            tombstone=output.with_name(output.name+".fb015_deleting")
            journal.write_text(json.dumps(record)+"\n",encoding="utf8")
            os.rename(output,tombstone)
            with self.assertRaisesRegex(RuntimeError,"PENDING_OFF_RECOVERY"):
                combo.compose(d,output,True)
            self.assertFalse(output.exists())
            self.assertTrue(combo.compose(d,output,False))

    def test_recover_after_tombstone_already_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=fixture(root)
            slash.apply(d,True)
            output=root/"private68"
            combo.compose(d,output,True)
            record=combo.verify_private_output(output,d)
            journal=output.with_name(output.name+".fb015_delete_journal.json")
            tombstone=output.with_name(output.name+".fb015_deleting")
            journal.write_text(json.dumps(record)+"\n",encoding="utf8")
            os.rename(output,tombstone)
            import shutil
            shutil.rmtree(tombstone)
            self.assertTrue(combo.compose(d,output,False))
            self.assertFalse(journal.exists())
            self.assertFalse(output.exists())

if __name__ == "__main__":
    unittest.main()
