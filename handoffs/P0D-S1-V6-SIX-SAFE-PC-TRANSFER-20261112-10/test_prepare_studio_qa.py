#!/usr/bin/env python3
"""Executed local safety tests.  NO Roblox Studio/network/publishing."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import prepare_studio_qa as qa

HERE = Path(__file__).resolve().parent

class TestSafeOwnerTransport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        for f in qa.FILES + [qa.MANIFEST]:
            shutil.copyfile(HERE/f, self.bundle/f)
        self.dest = self.root / "pc_destination"
        self.dest.mkdir()

    def refresh_entry(self, name):
        manifest=json.loads((self.bundle/qa.MANIFEST).read_text(encoding="utf8"))
        contents=(self.bundle/name).read_bytes()
        manifest["files"][name]={"bytes":len(contents),"sha256":hashlib.sha256(contents).hexdigest()}
        (self.bundle/qa.MANIFEST).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")

    def blocked(self, tag, fn):
        with self.assertRaises(qa.Blocked) as caught:
            fn()
        self.assertIn(tag,str(caught.exception))

    def test_01_bundled_real_place_pinned(self):
        self.assertEqual(qa.verify(self.bundle)["status"],"SOURCE_INSPECTION_PASS_NOT_STUDIO")

    def test_02_default_inspect_no_new_file(self):
        original = set(self.root.rglob("*"))
        self.assertEqual(qa.main(["--bundle",str(self.bundle)]),0)
        self.assertEqual(set(self.root.rglob("*")),original)

    def test_03_prepare_explicit_separate_copy(self):
        result=qa.stage(self.bundle,self.dest)
        self.assertEqual(result["status"],"ISOLATED_TEST_COPY_PREPARED_NOT_STUDIO")
        self.assertEqual((Path(result["copy"])/qa.PLACE).read_bytes(),(self.bundle/qa.PLACE).read_bytes())
        self.assertEqual(qa.verify(Path(result["copy"]))["real_roblox_studio"],"NOT_TESTED")

    def test_04_prepare_second_time_refuses_overwrite(self):
        qa.stage(self.bundle,self.dest)
        self.blocked("DESTINATION_ALREADY_EXISTS_REFUSE_OVERWRITE",lambda:qa.stage(self.bundle,self.dest))

    def test_05_bad_game_source_rejected(self):
        with (self.bundle/qa.PLACE).open("r+b") as f:
            f.seek(40); f.write(b"X")
        self.blocked("SOURCE_FILE_DIGEST_MISMATCH",lambda:qa.verify(self.bundle))

    def test_06_tampered_game_even_with_new_manifest_rejected(self):
        raw=(self.bundle/qa.PLACE).read_bytes()
        (self.bundle/qa.PLACE).write_bytes(raw[:100]+b"!"+raw[101:])
        self.refresh_entry(qa.PLACE)
        self.blocked("PLACE_PIN_MISMATCH",lambda:qa.verify(self.bundle))

    def test_07_tampered_audit_with_new_manifest_rejected(self):
        item=json.loads((self.bundle/qa.AUDIT).read_text(encoding="utf8"))
        item["real_mobile"]="PASS"
        (self.bundle/qa.AUDIT).write_text(json.dumps(item,ensure_ascii=False),encoding="utf8")
        self.refresh_entry(qa.AUDIT)
        self.blocked("AUDIT_PROVENANCE_OR_STUDIO_STATUS_INVALID",lambda:qa.verify(self.bundle))

    def test_08_tampered_worksheet_pass_with_updated_manifest_rejected(self):
        name="SCENARIOS_NOT_TESTED.json"
        item=json.loads((self.bundle/name).read_text(encoding="utf8"))
        item["scenarios"][0]["status"]="PASS"
        (self.bundle/name).write_text(json.dumps(item,ensure_ascii=False),encoding="utf8")
        self.refresh_entry(name)
        self.blocked("NOT_TESTED_SCENARIOS_INVALID",lambda:qa.verify(self.bundle))

    def test_09_tampered_readme_rejected(self):
        with (self.bundle/"README.md").open("ab") as f:f.write(b"fake")
        self.blocked("SOURCE_FILE_DIGEST_MISMATCH",lambda:qa.verify(self.bundle))

    def test_10_missing_evidence_file_rejected(self):
        (self.bundle/qa.AUDIT).unlink()
        self.blocked("SOURCE_FILE_MISSING_OR_SYMLINK",lambda:qa.verify(self.bundle))

    def test_11_duplicate_scenario_rejected(self):
        name="SCENARIOS_NOT_TESTED.json"
        item=json.loads((self.bundle/name).read_text(encoding="utf8"))
        item["scenarios"][1]["id"]=item["scenarios"][0]["id"]
        (self.bundle/name).write_text(json.dumps(item,ensure_ascii=False),encoding="utf8")
        self.refresh_entry(name)
        self.blocked("NOT_TESTED_SCENARIOS_INVALID",lambda:qa.verify(self.bundle))

    def test_12_relative_destination_refused(self):
        self.blocked("DESTINATION_MUST_BE_EXISTING_ABSOLUTE_DIRECTORY",lambda:qa.stage(self.bundle,Path("relative_folder")))

    def test_13_missing_destination_refused(self):
        self.blocked("DESTINATION_MUST_BE_EXISTING_ABSOLUTE_DIRECTORY",lambda:qa.stage(self.bundle,self.root/"no_dir"))

    def test_14_no_destination_flag_refused(self):
        self.assertEqual(qa.main(["--bundle",str(self.bundle),"--prepare"]),2)

    @unittest.skipUnless(hasattr(Path,"symlink_to"),"symlinks unsupported")
    def test_15_source_symlink_refused(self):
        name="README.md"
        archive=self.bundle/name
        archive.unlink()
        archive.symlink_to(HERE/name)
        self.blocked("SOURCE_FILE_MISSING_OR_SYMLINK",lambda:qa.verify(self.bundle))

    @unittest.skipUnless(hasattr(Path,"symlink_to"),"symlinks unsupported")
    def test_16_destination_symlink_refused(self):
        symlink=self.root/"dest_alias"
        symlink.symlink_to(self.dest,target_is_directory=True)
        self.blocked("DESTINATION_SYMLINK_FORBIDDEN",lambda:qa.stage(self.bundle,symlink))

    def test_18_exact_six_source_assertions_cannot_be_forged(self):
        a=json.loads((self.bundle/qa.AUDIT).read_text(encoding="utf8"))
        a["independent_CI_source_SHA"]="0"*40
        (self.bundle/qa.AUDIT).write_text(json.dumps(a),encoding="utf8")
        self.refresh_entry(qa.AUDIT)
        self.blocked("SIX_SOURCE_EXACT_PROVENANCE_MISMATCH",lambda:qa.verify(self.bundle))

    def test_19_original_three_safe_place_not_accepted(self):
        with (self.bundle/qa.PLACE).open("r+b") as f:
            f.seek(120); f.write(b"MUTANT_SOURCE")
        self.refresh_entry(qa.PLACE)
        self.blocked("PLACE_PIN_MISMATCH",lambda:qa.verify(self.bundle))

    def test_20_no_omitting_new_qa_scenarios(self):
        name="SCENARIOS_NOT_TESTED.json"
        a=json.loads((self.bundle/name).read_text(encoding="utf8"))
        a["scenarios"]=[x for x in a["scenarios"] if x["id"]!="ARENA_XZ_EGG_RETURN"]
        (self.bundle/name).write_text(json.dumps(a),encoding="utf8")
        self.refresh_entry(name)
        self.blocked("NOT_TESTED_SCENARIOS_INVALID",lambda:qa.verify(self.bundle))

    def test_17_safe_manifest_file_exact_list(self):
        man=json.loads((self.bundle/qa.MANIFEST).read_text(encoding="utf8"))
        self.assertEqual(set(man["files"]),set(qa.FILES))
        self.assertEqual(man["place_sha256"],qa.GAME_SHA)
        self.assertFalse(man["studio_tested"])

if __name__=="__main__":
    unittest.main(verbosity=2)
