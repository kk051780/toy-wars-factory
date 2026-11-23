"""Self-contained fake fixtures test *verifier logic*, not actual Roblox runtime.
Native/Rojo CI separately proves genuine official artifact composition.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import compose_real70 as c

class Real70OriginalLockRegression(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.place = b"fixture-only-original-place"
        (self.root / c.REAL69_PLACE).write_bytes(self.place)
        self.lss = "ServerScriptService/EGGRUMBLE_LandSeaSkyTraversal"
        self.files = {}
        self.hashes = {}
        self.classes = {}
        for i in range(68):
            route = f"ServerScriptService/FixtureOriginal_{i:02d}"
            self.files[route] = {"sha256": f"fixture{i:02d}", "class": "Script",
                                 "path": f"fixture/{i}.server.luau"}
            self.hashes[route] = self.files[route]["sha256"]
            self.classes[route] = "Script"
        lss_path = "fixture/original_lss.server.luau"
        target = self.root / lss_path
        target.parent.mkdir(parents=True)
        target.write_text('\n'.join([
            'local NAME = "EGGRUMBLE_LAND_SEA_SKY_20261117"',
            'local landDock=put(scene,"PublicSeaDock"',
            'local floor=world:FindFirstChild("TacticalBattlefield")',
            'CFrame.new(x,y+0.9,shoreZ-92)',
        ]), encoding="utf-8")
        self.files[self.lss] = {"sha256":"fixtureLSS", "class":"Script", "path":lss_path}
        self.hashes[self.lss] = "fixtureLSS"
        self.classes[self.lss] = "Script"
        self.receipt = {
            "canonical_build":True, "official_branch":c.FORMAL,
            "build_head":c.BASE, "selected_source_count":69,
            "source_hashes":self.hashes, "source_classes":self.classes,
        }
        self.write_receipt()
        self.extra = {"sha256":c.digest(c.NEW_SOURCE.read_bytes()),
                      "class":"LocalScript", "path":c.NEW_FILE}
        self.patches = [
            patch.object(c, "REAL69_BYTES", len(self.place)),
            patch.object(c, "REAL69_SHA", hashlib.sha256(self.place).hexdigest())
        ]
        for p in self.patches: p.start()
        self.addCleanup(lambda: [p.stop() for p in reversed(self.patches)])

    def write_receipt(self):
        (self.root / c.REAL69_RECEIPT).write_text(json.dumps(self.receipt),
                                                  encoding="utf-8")
    def check(self, mapping, allow_new):
        with patch.object(c, "project_scan", return_value=mapping):
            return c.original_lock(self.root, allow_new=allow_new)

    def test_01_pristine69_is_valid(self):
        out,_ = self.check(dict(self.files), False)
        self.assertEqual(set(out), set(self.hashes))
    def test_02_candidate70_preserves_original69(self):
        p = dict(self.files); p[c.NEW_ROUTE] = dict(self.extra)
        out,_ = self.check(p, True)
        self.assertEqual(len(out),69)
        self.assertNotIn(c.NEW_ROUTE,out)
    def test_03_pristine69_rejects_extra(self):
        p = dict(self.files); p[c.NEW_ROUTE] = dict(self.extra)
        with self.assertRaisesRegex(ValueError,"OFFICIAL_ORIGINAL_SCRIPT_SET"):
            self.check(p, False)
    def test_04_candidate70_requires_exactly_one(self):
        with self.assertRaisesRegex(ValueError,"CANDIDATE_EXACT_69_PLUS_1_SCRIPT_SET"):
            self.check(dict(self.files), True)
    def test_05_candidate70_rejects_two_extra(self):
        p = dict(self.files); p[c.NEW_ROUTE] = dict(self.extra)
        p["StarterPlayer/StarterPlayerScripts/Injected"] = dict(self.extra)
        with self.assertRaisesRegex(ValueError,"CANDIDATE_EXACT_69_PLUS_1_SCRIPT_SET"):
            self.check(p,True)
    def test_06_candidate70_rejects_dropped_original(self):
        p = dict(self.files); p[c.NEW_ROUTE] = dict(self.extra)
        p.pop(next(iter(self.hashes)))
        with self.assertRaisesRegex(ValueError,"CANDIDATE_EXACT_69_PLUS_1_SCRIPT_SET"):
            self.check(p,True)
    def test_07_candidate70_rejects_original_sha_change(self):
        p = dict(self.files); p[c.NEW_ROUTE] = dict(self.extra)
        key = next(iter(self.hashes))
        p[key] = {**p[key], "sha256":"fake-change"}
        with self.assertRaisesRegex(ValueError,"OFFICIAL_ORIGINAL_SHA_CLASS"):
            self.check(p,True)
    def test_08_candidate70_rejects_original_class_change(self):
        p = dict(self.files); p[c.NEW_ROUTE] = dict(self.extra)
        key = next(iter(self.hashes))
        p[key] = {**p[key], "class":"LocalScript"}
        with self.assertRaisesRegex(ValueError,"OFFICIAL_ORIGINAL_SHA_CLASS"):
            self.check(p,True)
    def test_09_tampered_original_place_rejected(self):
        (self.root / c.REAL69_PLACE).write_bytes(b"tampered-original")
        with self.assertRaisesRegex(ValueError,"OFFICIAL_PLACE_IDENTITY"):
            self.check(dict(self.files),False)
    def test_10_tampered_canonical_receipt_rejected(self):
        self.receipt["canonical_build"] = False
        self.write_receipt()
        with self.assertRaisesRegex(ValueError,"OFFICIAL_SOURCE_RECEIPT_PROVENANCE"):
            self.check(dict(self.files),False)
    def test_11_wrong_official_head_rejected(self):
        self.receipt["build_head"]="0"*40
        self.write_receipt()
        with self.assertRaisesRegex(ValueError,"OFFICIAL_SOURCE_RECEIPT_PROVENANCE"):
            self.check(dict(self.files),False)
    def test_12_fake_scene_owner_rejected(self):
        target = self.root / self.files[self.lss]["path"]
        target.write_text('local NAME="forged_scene"', encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"OFFICIAL_LSS_DOCK_OR_FLOOR_DRIFT"):
            self.check(dict(self.files),False)

if __name__ == "__main__":
    unittest.main()
