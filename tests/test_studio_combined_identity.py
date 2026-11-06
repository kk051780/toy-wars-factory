"""A14 combined 4-toy + outcome XML pins for existing Studio host, QA only.

Original PR149 security gates remain unchanged other than exact artifact/source pins.
This DOES NOT execute Roblox Studio or attest a reviewer/host.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("studio_host_gate",ROOT/"tools/studio_host_gate.py")
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
exp=importlib.util.spec_from_file_location("export_accepted_rbxlx",ROOT/"tools/export_accepted_rbxlx.py")
export=importlib.util.module_from_spec(exp);exp.loader.exec_module(export)
OLD_XML_SHA="1c9bdc3dc478fe72e51870e478aa15392c47875618b86262aa7dd605e4026b33"
MAIN_SHA="e5deff4d5681bca4823a3da0f848e01bc089ae6e"
COMBINED_SHA="8fb7bc522a995fbac6ca0c42ad7c61cc14a9814b"

class IsolatedCombinedStudioIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml,cls.receipt=export.build_place(ROOT)
    def test_exact_provider_artifact_pins_not_old_main(self):
        self.assertEqual(gate.ARTIFACT_ID,13478848965)
        self.assertEqual(gate.BUILDER_RUN_ID,42166605719)
        self.assertEqual(gate.EXACT_ARTIFACT_ZIP,
          "9c8110e5a6b9e3d3f7e82bcb541be02775fd66bc2576181c81b0394af5df9bb5")
        self.assertEqual(gate.EXACT_QA_SOURCE_SHA,COMBINED_SHA)
        self.assertNotEqual(gate.EXACT_QA_SOURCE_SHA,MAIN_SHA)
        self.assertNotEqual(gate.EXACT_PLACE_SHA256,OLD_XML_SHA)
    def test_real_combined_xml_exactly_matches_source_pins(self):
        self.assertEqual(len(self.xml),62635)
        self.assertEqual(hashlib.sha256(self.xml).hexdigest(),gate.EXACT_PLACE_SHA256)
        self.assertEqual(gate.validate_file(self.xml)["unmerged_qa_source_sha"],COMBINED_SHA)
        self.assertFalse(gate.validate_file(self.xml)["engine_verified"])
    def test_curebo_and_outcome_present_in_exact_embedded_sources(self):
        tree=ET.fromstring(self.xml)
        snippets={}
        for item in tree.findall(".//Item"):
            name=item.find("./Properties/string[@name='Name']")
            text=item.find("./Properties/ProtectedString[@name='Source']")
            if name is not None and text is not None:
                snippets[name.text]=text.text
        self.assertEqual(set(snippets),{"ToyWarsServer","ToyWarsHUD","ToyWarsSmokeTest","ToyWarsBalance"})
        self.assertIn('B.PLAYABLE_IDS = {"pon", "guardon", "tankuru", "curebo"}',snippets["ToyWarsBalance"])
        self.assertIn('state.roundOutcome.Value="VICTORY"',snippets["ToyWarsServer"])
        self.assertIn("ToyPageNavigation",snippets["ToyWarsHUD"])
        self.assertIn("RoundResultBanner",snippets["ToyWarsHUD"])
    def test_original_main_xml_is_rejected_even_if_renamed(self):
        self.assertNotEqual(gate.EXACT_PLACE_SHA256,OLD_XML_SHA)
        with self.assertRaises(gate.StudioProbeBlocked):
            gate.validate_file(b'<?xml version="1.0"?><roblox version="4"></roblox>')
    def test_changed_combined_xml_is_rejected(self):
        with self.assertRaises(gate.StudioProbeBlocked):
            gate.validate_file(self.xml+b"\n")
        tampered=self.xml.replace(b"curebo",b"curbbo",1)
        self.assertNotEqual(tampered,self.xml)
        with self.assertRaises(gate.StudioProbeBlocked):
            gate.validate_file(tampered)
    def test_probe_pin_is_exact_unchanged_from_protected_pr149(self):
        probe=(ROOT/"tools/twf_local_place_probe.luau").read_bytes()
        self.assertEqual(hashlib.sha256(probe).hexdigest(),gate.PROBE_SCRIPT_SHA256)
        self.assertIn(b"TWF_STUDIO_LOCAL_PLACE_STRUCTURE_OK_V1",probe)
    def test_studio_host_stays_opt_in_and_never_claims_engine(self):
        self.assertEqual(gate.main([]),0)
        answer=gate.validate_file(self.xml)
        self.assertFalse(answer["engine_verified"])
        self.assertFalse(gate.parse_studio_output(
            "",gate.PASS_MARKER,"",exit_code=0)["mobile_verified"])
    def test_untrusted_xml_name_does_not_pass_host_command_line(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            fake_studio=base/"RobloxStudioBeta.exe";fake_studio.write_bytes(b"TEST_ONLY")
            fake_probe=base/"twf_local_place_probe.luau"
            fake_probe.write_bytes((ROOT/"tools/twf_local_place_probe.luau").read_bytes())
            wrong=base/"other_file.rbxlx";wrong.write_bytes(self.xml)
            with self.assertRaises(gate.StudioProbeBlocked):
                gate.build_args(fake_studio,wrong,fake_probe,base/"studio.txt")
if __name__=="__main__":unittest.main()
