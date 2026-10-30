"""Source-exact XML candidate is exported via the EXISTING Actions .qa/auto artifact.

These tests do not execute the Roblox engine; XML format and bytes only.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import export_accepted_rbxlx as x

class XmlArtifacts(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        (self.root / 'src').mkdir()
        for _,_,_,rel,_ in x.EXPECTED:
            (self.root/rel).write_bytes((ROOT/rel).read_bytes())
        self.out = self.root / '.qa' / 'auto'

    def test_source_pins_match_actual_four_game_lua_blobs(self):
        files=x.read_accepted_sources(self.root)
        self.assertEqual(len(files),4)
        self.assertEqual(sum(map(len,files.values())),52781)

    def test_generated_document_is_deterministic(self):
        a,ar=x.build_place(self.root)
        b,br=x.build_place(self.root)
        self.assertEqual(a,b)
        self.assertEqual(ar,br)
        self.assertEqual(ar['rbxlx_sha256'],hashlib.sha256(a).hexdigest())

    def test_exact_ten_instances_and_single_remote(self):
        xml,_=x.build_place(self.root)
        root=ET.fromstring(xml)
        self.assertEqual(root.tag,'roblox')
        self.assertEqual(root.attrib.get('version'),'4')
        classes=[y.attrib.get('class') for y in root.findall('.//Item')]
        self.assertEqual(len(classes),10)
        self.assertEqual(classes.count('RemoteEvent'),1)
        self.assertEqual(classes.count('ModuleScript'),1)
        self.assertEqual(classes.count('Script'),2)
        self.assertEqual(classes.count('LocalScript'),1)

    def test_all_four_sources_roundtrip_exactly(self):
        xml,_=x.build_place(self.root)
        doc=ET.fromstring(xml)
        embedded={}
        for item in doc.findall('.//Item'):
            name=item.find('./Properties/string[@name="Name"]')
            code=item.find('./Properties/ProtectedString[@name="Source"]')
            if code is not None:
                embedded[name.text]=code.text.encode('utf8')
        for _, name, _, rel, _ in x.EXPECTED:
            self.assertEqual(embedded[name],(self.root/rel).read_bytes())

    def test_scripts_have_unique_referents(self):
        a,_=x.build_place(self.root)
        ids=[e.get('referent') for e in ET.fromstring(a).findall('.//Item')]
        self.assertEqual(len(set(ids)),10)
        self.assertTrue(all(i.startswith('RBX') for i in ids))

    def test_no_hidden_network_or_credentials(self):
        a,record=x.build_place(self.root)
        self.assertNotIn(b'<script',a.lower())
        self.assertFalse(record['roblox_upload_attested'])
        self.assertFalse(record['roblox_engine_verified'])
        self.assertFalse(record['studio_open_verified'])
        self.assertFalse(record['public_publish_authorized'])
        self.assertFalse(record['git_action_run_authenticated'])

    def test_server_source_tamper_fails(self):
        p=self.root/'src/ToyWarsServer.server.lua'
        p.write_bytes(p.read_bytes()+b'\n-- tamper')
        with self.assertRaises(x.ExportBlocked):x.build_place(self.root)

    def test_hud_source_tamper_fails(self):
        p=self.root/'src/ToyWarsHUD.client.lua'
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(x.ExportBlocked):x.build_place(self.root)

    def test_balance_source_tamper_fails(self):
        p=self.root/'src/ToyWarsBalance.lua'
        p.write_bytes(b'')
        with self.assertRaises(x.ExportBlocked):x.build_place(self.root)

    def test_smoke_source_tamper_fails(self):
        p=self.root/'src/ToyWarsSmokeTest.server.lua'
        p.write_bytes(p.read_bytes().replace(b'local',b'Local',1))
        with self.assertRaises(x.ExportBlocked):x.build_place(self.root)

    def test_source_missing_fails(self):
        (self.root/'src/ToyWarsBalance.lua').unlink()
        with self.assertRaises(x.ExportBlocked):x.build_place(self.root)

    def test_source_symlink_fails(self):
        p=self.root/'src/ToyWarsHUD.client.lua';p.unlink()
        p.symlink_to(ROOT/'src/ToyWarsHUD.client.lua')
        with self.assertRaises(x.ExportBlocked):x.build_place(self.root)

    def test_invalid_source_utf8_fails(self):
        p=self.root/'src/ToyWarsHUD.client.lua';p.write_bytes(b'\xff')
        with self.assertRaises(x.ExportBlocked):x.build_place(self.root)

    def test_receipt_manifest_keys_are_exact_and_untrusted(self):
        _,r=x.build_place(self.root)
        self.assertEqual(r['repository'],x.REPO)
        self.assertEqual(r['accepted_game_source_main_sha'],x.ACCEPTED_MAIN)
        self.assertEqual(set(r['sources']),{row[3] for row in x.EXPECTED})
        self.assertEqual(r['status'],'UNVERIFIED_PR_BUILD_SOURCE_PINNED_XML_ONLY')

    def test_saved_output_is_hash_and_byte_exact(self):
        rec=x.export(self.root,self.out)
        binary=(self.out/x.XML_NAME).read_bytes()
        saved=json.loads((self.out/x.RECEIPT_NAME).read_text())
        self.assertEqual(rec,saved)
        self.assertEqual(rec['rbxlx_bytes'],len(binary))
        self.assertEqual(rec['rbxlx_sha256'],hashlib.sha256(binary).hexdigest())

    def test_output_cannot_be_overwritten(self):
        x.export(self.root,self.out)
        with self.assertRaises(x.ExportBlocked):x.export(self.root,self.out)

    def test_existing_xml_prevents_partial_export(self):
        self.out.mkdir(parents=True)
        (self.out/x.XML_NAME).write_text('do not replace')
        with self.assertRaises(x.ExportBlocked):x.export(self.root,self.out)
        self.assertEqual((self.out/x.XML_NAME).read_text(),'do not replace')
        self.assertFalse((self.out/x.RECEIPT_NAME).exists())

    def test_existing_receipt_prevents_partial_export(self):
        self.out.mkdir(parents=True)
        (self.out/x.RECEIPT_NAME).write_text('do not replace')
        with self.assertRaises(x.ExportBlocked):x.export(self.root,self.out)
        self.assertFalse((self.out/x.XML_NAME).exists())

    def test_other_output_directory_refused(self):
        with self.assertRaises(x.ExportBlocked):x.export(self.root,self.root/'data')

    def test_symlinked_qa_directory_refused(self):
        external=self.root/'external';external.mkdir()
        (self.root/'.qa').symlink_to(external,target_is_directory=True)
        with self.assertRaises(x.ExportBlocked):x.export(self.root,self.out)

    def test_no_modify_source_during_export(self):
        before={rel:hashlib.sha256((self.root/rel).read_bytes()).hexdigest() for _,_,_,rel,_ in x.EXPECTED}
        x.export(self.root,self.out)
        after={rel:hashlib.sha256((self.root/rel).read_bytes()).hexdigest() for _,_,_,rel,_ in x.EXPECTED}
        self.assertEqual(before,after)

    def test_only_exact_repo_pr_or_main_push_can_emit_ci_artifact(self):
        valid={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':x.REPO,
               'GITHUB_EVENT_NAME':'pull_request','GITHUB_REF':'refs/pull/146/merge'}
        self.assertTrue(x.actions_export_allowed(valid))
        self.assertTrue(x.actions_export_allowed({**valid,'GITHUB_EVENT_NAME':'push','GITHUB_REF':'refs/heads/main'}))
        for k,v in [('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/feature'),
                    ('GITHUB_EVENT_NAME','schedule'),('GITHUB_ACTIONS','false')]:
            with self.subTest(k=k):
                self.assertFalse(x.actions_export_allowed({**valid,k:v}))

    def test_zz_existing_actions_will_upload_real_xml_evidence(self):
        """Export into existing .qa/auto artifact on Actions, no workflow edit.

        Explicitly untrusted for PRs; official receiver must verify run and data.
        """
        if x.actions_export_allowed(dict(os.environ)):
            output=ROOT/'.qa'/'auto'
            if (output/x.XML_NAME).exists():
                self.fail('existing XML artifact cannot be overwritten')
            record=x.export(ROOT,output)
        else:
            record=x.export(self.root,self.out)
        self.assertFalse(record['studio_open_verified'])
        self.assertFalse(record['roblox_upload_attested'])

if __name__=='__main__':unittest.main()
