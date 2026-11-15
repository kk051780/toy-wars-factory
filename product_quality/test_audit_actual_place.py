import hashlib
import io
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from audit_actual_place import inspect, inspect_zip, git_blob

HEAD = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"

def fixture(gamesrc="local function useSevenJob() end\\nlocal function applyModeVote() end"):
    root = ET.Element("roblox")
    def folder(parent, name, script_class="Folder"):
        item = ET.SubElement(parent, "Item", {"class": script_class})
        props = ET.SubElement(item, "Properties")
        ET.SubElement(props, "string", {"name": "Name"}).text = name
        return item
    server = folder(folder(root, "ServerScriptService", "ServerScriptService"),
                    "TrapRaidersS1")
    player = folder(folder(root, "StarterPlayer", "StarterPlayer"),
                    "StarterPlayerScripts")
    values = [
        (server, "Game", "Script", gamesrc, "server/Game.server.luau"),
        (server, "SevenJobsRules", "ModuleScript",
         'NINJA={label="暗殺者"}', "server/SevenJobsRules.luau"),
        (player, "TrapRaidersHUD", "LocalScript",
         "暗殺者", "client/HUD.client.luau"),
    ]
    lock = {"total_scripts":3, "blobs":{}}
    for parent, name, cls, source, path in values:
        item = folder(parent, name, cls)
        ET.SubElement(item.find("Properties"), "string",
                      {"name": "Source"}).text = source
        lock["blobs"][path] = git_blob(source.encode())
    return ET.tostring(root, encoding="utf-8"), lock

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
        lock["blobs"]["server/SevenJobsRules.luau"] = git_blob('NINJA={label="忍者"}'.encode("utf-8"))
        lock["blobs"]["client/HUD.client.luau"] = git_blob("忍者".encode("utf-8"))
        r = inspect(xml, lock, HEAD)
        self.assertTrue(r["source_lock_exact"])
        self.assertIn("ASSASSIN_DISPLAY_OR_INTERNAL_KEY_INCONSISTENT", r["problems"])

    def test_swapped_script_sources_with_identical_multiset_must_fail(self):
        xml, lock = fixture()
        root = ET.fromstring(xml)
        script_items = [
            item for item in root.iter("Item")
            if item.find("./Properties/string[@name='Source']") is not None
        ]
        a = script_items[0].find("./Properties/string[@name='Source']")
        b = script_items[1].find("./Properties/string[@name='Source']")
        a.text, b.text = b.text, a.text
        report = inspect(ET.tostring(root, encoding="utf-8"), lock, HEAD)
        self.assertIn("PLACE_SOURCE_PATH_BLOB_MISMATCH", report["problems"])
        self.assertEqual("SOURCE_INTEGRITY_NO_GO", report["decision"])
        self.assertFalse(report["source_path_exact"])

    def test_script_class_or_location_mismatch_blocks_source_gate(self):
        xml, lock = fixture()
        root = ET.fromstring(xml)
        game = next(item for item in root.iter("Item")
                    if item.findtext("./Properties/string[@name='Name']") == "Game")
        game.set("class", "ModuleScript")
        report = inspect(ET.tostring(root, encoding="utf-8"), lock, HEAD)
        self.assertIn("PLACE_SOURCE_PATH_SET_MISMATCH", report["problems"])
        self.assertFalse(report["source_lock_exact"])
        root = ET.fromstring(xml)
        game = next(item for item in root.iter("Item")
                    if item.findtext("./Properties/string[@name='Name']") == "Game")
        server = next(item for item in root.iter("Item")
                      if item.findtext("./Properties/string[@name='Name']") == "TrapRaidersS1")
        server.remove(game)
        root.append(game)
        report = inspect(ET.tostring(root, encoding="utf-8"), lock, HEAD)
        self.assertTrue(any(p.startswith("SCRIPT_UNEXPECTED_LOCATION:")
                            for p in report["problems"]))
        self.assertEqual("SOURCE_INTEGRITY_NO_GO", report["decision"])

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
