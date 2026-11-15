import hashlib
import io
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from audit_actual_place import inspect, inspect_zip, git_blob

HEAD = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"

def fixture(gamesrc="local function useSevenJob() end\nlocal function applyModeVote() end"):
    r = ET.Element("roblox")
    sources = {
        "Game": gamesrc, "SevenJobsRules": 'NINJA={label="暗殺者"}',
        "TrapRaidersHUD": "暗殺者",
    }
    for name, source in sources.items():
        item = ET.SubElement(r, "Item", {"class": "ModuleScript" if name=="SevenJobsRules" else "Script"})
        pr = ET.SubElement(item, "Properties")
        ET.SubElement(pr, "string", {"name":"Name"}).text = name
        ET.SubElement(pr, "string", {"name":"Source"}).text = source
    lock = {"total_scripts":3,"blobs":{n+".luau":git_blob(s.encode()) for n,s in sources.items()}}
    return ET.tostring(r, encoding="utf-8"), lock

class ActualPlaceTests(unittest.TestCase):
    def test_genuine_source_lock_is_required(self):
        xml, lock = fixture()
        result = inspect(xml, lock, HEAD)
        self.assertTrue(result["source_lock_exact"])
        self.assertEqual(3, result["scripts_examined"])
        self.assertFalse(result["gameplay_engine_pass"])
        self.assertEqual("GAMEPLAY_SOURCE_REMEDIATION_REQUIRED", result["decision"])

    def test_mutated_live_code_rejects_stale_source_lock(self):
        xml, lock = fixture()
        changed = xml.replace(b"useSevenJob", b"useFakeRole")
        result = inspect(changed, lock, HEAD)
        self.assertEqual("SOURCE_INTEGRITY_NO_GO", result["decision"])
        self.assertIn("PLACE_SOURCE_GITBLOBS_DO_NOT_MATCH_LOCK", result["problems"])

    def test_invalid_place_and_missing_lock_fail_closed(self):
        self.assertEqual("SOURCE_INTEGRITY_NO_GO", inspect(b"bad-xml",{},HEAD)["decision"])
        xml, lock = fixture()
        self.assertEqual("SOURCE_INTEGRITY_NO_GO", inspect(xml,{},HEAD)["decision"])

    def test_legacy_alias_or_unselected_ready_cannot_be_marked_pass(self):
        xml, lock = fixture()
        result = inspect(xml, lock, HEAD)
        self.assertIn("UNSELECTED_PLAYER_CAN_READY_PRIVATE_JOB_TRIAL",result["problems"])
        self.assertNotIn("ASSASSIN_DISPLAY_OR_INTERNAL_KEY_INCONSISTENT",result["problems"])
        self.assertFalse(result["human_approved"])

    def test_legacy_alias_is_rejected_even_with_updated_source_lock(self):
        xml, lock = fixture()
        xml = xml.replace("暗殺者".encode("utf-8"), "忍者".encode("utf-8"))
        lock["blobs"]["SevenJobsRules.luau"] = git_blob('NINJA={label="忍者"}'.encode("utf-8"))
        lock["blobs"]["TrapRaidersHUD.luau"] = git_blob("忍者".encode("utf-8"))
        r = inspect(xml, lock, HEAD)
        self.assertTrue(r["source_lock_exact"])
        self.assertIn("ASSASSIN_DISPLAY_OR_INTERNAL_KEY_INCONSISTENT", r["problems"])

    def test_zip_input_and_missing_manifest(self):
        xml, lock = fixture()
        with io.BytesIO() as mem:
            with ZipFile(mem,"w") as z:
                z.writestr("Place.rbxlx",xml)
                z.writestr("SOURCE_LOCK.json",json.dumps(lock))
            mem.seek(0)
            path = Path("/tmp/p0d_unit_actual_place.zip")
            path.write_bytes(mem.read())
        try:
            self.assertTrue(inspect_zip(path,HEAD)["source_lock_exact"])
        finally:
            path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
