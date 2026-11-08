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
        files=x.read_pinned_sources(self.root)
        self.assertEqual(len(files),4)
        self.assertEqual(sum(map(len,files.values())),76921)

    def test_generated_document_is_deterministic(self):
        a,ar=x.build_place(self.root)
        b,br=x.build_place(self.root)
        self.assertEqual(a,b)
        self.assertEqual(ar,br)
        self.assertEqual(ar['rbxlx_sha256'],hashlib.sha256(a).hexdigest())
        self.assertNotEqual(ar['rbxlx_sha256'],'eb090d086e0a65341bae6cc84691cd0135f274dd41b07fdebc334d7255fc04cb')
        self.assertGreater(ar['rbxlx_bytes'], 67659)
        self.assertEqual(ar['rbxlx_bytes'], len(a))

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

    def test_current_combined_gameplay_is_embedded_in_actual_xml(self):
        binary, receipt=x.build_place(self.root)
        self.assertEqual(receipt['unmerged_source_branch_head_sha'],
                         'fbbb1d0b31f63e1fa22b63a8ce7a1739521b0c1e')
        self.assertEqual(receipt['sources']['src/ToyWarsServer.server.lua']['git_blob_sha1'],
                         '181b0ef3a5aedafef4490decdbbe167d769e9932')
        doc=ET.fromstring(binary)
        embedded={}
        for item in doc.findall('.//Item'):
            name=item.find('./Properties/string[@name="Name"]')
            code=item.find('./Properties/ProtectedString[@name="Source"]')
            if name is not None and code is not None:
                embedded[name.text]=code.text
        self.assertEqual(set(embedded), {'ToyWarsServer','ToyWarsHUD','ToyWarsBalance','ToyWarsSmokeTest'})
        self.assertIn('if escort then',embedded['ToyWarsServer'])
        self.assertIn('e.repairFlashUntil=now+0.45',embedded['ToyWarsServer'])
        self.assertIn('state.roundOutcome.Value="LOSS"',embedded['ToyWarsServer'])
        self.assertIn('state.roundOutcome.Value="VICTORY"',embedded['ToyWarsServer'])
        self.assertIn('state.baseHP.Value=100',embedded['ToyWarsServer'])
        self.assertIn('ToyPageNavigation',embedded['ToyWarsHUD'])
        self.assertIn('RoundResultBanner',embedded['ToyWarsHUD'])
        self.assertIn('BossWaveWarning',embedded['ToyWarsHUD'])
        self.assertIn('curebo',embedded['ToyWarsBalance'])

    def test_wave_50_junk_scaling_is_present_in_embedded_game_xml(self):
        binary, receipt=x.build_place(self.root)
        self.assertEqual(receipt['sources']['src/ToyWarsBalance.lua']['git_blob_sha1'],
                         '64175b1cda7e4d5e4623d7b28bb80fdc3d64c3b8')
        self.assertEqual(receipt['sources']['src/ToyWarsServer.server.lua']['git_blob_sha1'],
                         '181b0ef3a5aedafef4490decdbbe167d769e9932')
        doc=ET.fromstring(binary)
        source={}
        for item in doc.findall('.//Item'):
            name=item.find('./Properties/string[@name="Name"]')
            code=item.find('./Properties/ProtectedString[@name="Source"]')
            if name is not None and code is not None:
                source[name.text]=code.text
        self.assertIn('function B.junkThreat(wave)',source['ToyWarsBalance'])
        self.assertIn('local threat=B.junkThreat(state.wave.Value)',source['ToyWarsServer'])
        self.assertIn('e.damage or data.damage',source['ToyWarsServer'])
        self.assertIn('state.roundOutcome.Value="VICTORY"',source['ToyWarsServer'])
        self.assertIn('RoundResultBanner',source['ToyWarsHUD'])
        self.assertFalse(receipt['roblox_engine_verified'])
        self.assertFalse(receipt['source_merge_verified'])

    def test_tenth_wave_captain_is_in_embedded_3d_server_source(self):
        xml, manifest=x.build_place(self.root)
        self.assertEqual(manifest['unmerged_source_branch_head_sha'],
                         'fbbb1d0b31f63e1fa22b63a8ce7a1739521b0c1e')
        self.assertEqual(manifest['sources']['src/ToyWarsBalance.lua']['git_blob_sha1'],
                         '64175b1cda7e4d5e4623d7b28bb80fdc3d64c3b8')
        self.assertEqual(manifest['sources']['src/ToyWarsServer.server.lua']['git_blob_sha1'],
                         '181b0ef3a5aedafef4490decdbbe167d769e9932')
        doc=ET.fromstring(xml)
        embedded={}
        for node in doc.findall('.//Item'):
            name=node.find('./Properties/string[@name="Name"]')
            code=node.find('./Properties/ProtectedString[@name="Source"]')
            if name is not None and code is not None:
                embedded[name.text]=code.text
        self.assertIn('function B.junkBoss(wave)', embedded['ToyWarsBalance'])
        self.assertIn('m.Name="JUNK_CAPTAIN"', embedded['ToyWarsServer'])
        self.assertIn('"BossCrown"', embedded['ToyWarsServer'])
        self.assertIn('"BossBeacon"', embedded['ToyWarsServer'])
        self.assertIn('local captain=B.junkBoss(state.wave.Value)', embedded['ToyWarsServer'])
        self.assertIn('e.reward or B.UNITS[e.id].reward', embedded['ToyWarsServer'])
        self.assertIn('state.baseHP.Value-(e.boss and 28 or 12)', embedded['ToyWarsServer'])
        self.assertFalse(manifest['roblox_engine_verified'])

    def test_pon_courier_is_in_source_pinned_export_not_just_in_hud(self):
        xml, receipt = x.build_place(self.root)
        self.assertEqual(receipt['sources']['src/ToyWarsBalance.lua']['git_blob_sha1'],
                         '64175b1cda7e4d5e4623d7b28bb80fdc3d64c3b8')
        self.assertEqual(receipt['sources']['src/ToyWarsServer.server.lua']['git_blob_sha1'],
                         '181b0ef3a5aedafef4490decdbbe167d769e9932')
        doc = ET.fromstring(xml)
        embedded = {}
        for item in doc.findall('.//Item'):
            name = item.find('./Properties/string[@name="Name"]')
            code = item.find('./Properties/ProtectedString[@name="Source"]')
            if name is not None and code is not None:
                embedded[name.text] = code.text
        self.assertIn('function B.deliveryReward(id)', embedded['ToyWarsBalance'])
        self.assertIn('B.deliveryReward(e.id)', embedded['ToyWarsServer'])
        self.assertIn('COURIER +', embedded['ToyWarsHUD'])
        self.assertFalse(receipt['roblox_engine_verified'])
        self.assertFalse(receipt['source_merge_verified'])

    def test_boss_warning_is_in_pinned_hud_with_authoritative_wave_refresh(self):
        binary, manifest=x.build_place(self.root)
        self.assertEqual(manifest['unmerged_source_branch_head_sha'],
                         'fbbb1d0b31f63e1fa22b63a8ce7a1739521b0c1e')
        self.assertEqual(manifest['sources']['src/ToyWarsHUD.client.lua']['git_blob_sha1'],
                         'c48743468682b2f9808520cc5db8d435410cb11b')
        doc=ET.fromstring(binary)
        hud=next(item.find('./Properties/ProtectedString[@name="Source"]').text
                 for item in doc.findall('.//Item')
                 if (item.find('./Properties/string[@name="Name"]') is not None
                     and item.find('./Properties/string[@name="Name"]').text == 'ToyWarsHUD'))
        self.assertIn('BossWaveWarning',hud)
        self.assertIn('B.junkBoss(current)',hud)
        self.assertIn('for _,v in ipairs(observed) do v.Changed:Connect(refresh) end',hud)
        self.assertIn('bossWarning.Visible',hud)
        self.assertFalse(manifest['roblox_engine_verified'])
        self.assertFalse(manifest['source_merge_verified'])

    def test_factory_speed_is_in_signed_source_pinned_xml_candidate(self):
        binary, manifest=x.build_place(self.root)
        self.assertEqual(manifest['unmerged_source_branch_head_sha'],
                         'fbbb1d0b31f63e1fa22b63a8ce7a1739521b0c1e')
        self.assertEqual(manifest['sources']['src/ToyWarsBalance.lua']['git_blob_sha1'],
                         '64175b1cda7e4d5e4623d7b28bb80fdc3d64c3b8')
        self.assertEqual(manifest['sources']['src/ToyWarsServer.server.lua']['git_blob_sha1'],
                         '181b0ef3a5aedafef4490decdbbe167d769e9932')
        doc=ET.fromstring(binary)
        embedded={}
        for node in doc.findall('.//Item'):
            name=node.find('./Properties/string[@name="Name"]')
            code=node.find('./Properties/ProtectedString[@name="Source"]')
            if name is not None and code is not None:
                embedded[name.text]=code.text
        self.assertIn('function B.productionInterval(level)',embedded['ToyWarsBalance'])
        self.assertIn('printerLabel.Text=string.format(',embedded['ToyWarsServer'])
        self.assertIn('state.productionTimer=state.productionTimer+interval',embedded['ToyWarsServer'])
        self.assertIn('local function guardonInterception(state, enemy, target, distance)',embedded['ToyWarsServer'])
        self.assertIn('local function tankuruCaptainInRange(state, artillery, range)',embedded['ToyWarsServer'])
        self.assertIn('muzzleFlashUntil=(state.combatTime or 0)+0.18',embedded['ToyWarsServer'])
        self.assertIn('STUDIO_PREVIEW_UNSAVED',embedded['ToyWarsServer'])
        self.assertIn('StudioPreviewNotice',embedded['ToyWarsHUD'])
        self.assertIn('refreshPrinterProgress(state)',embedded['ToyWarsServer'])
        self.assertIn('ToyPrinterProgress',embedded['ToyWarsServer'])
        self.assertIn('modelPart(m,"MuzzleFlash"',embedded['ToyWarsServer'])
        self.assertIn('target,dist=guardonInterception(state,e,target,dist)',embedded['ToyWarsServer'])
        self.assertIn('JUNK_CAPTAIN',embedded['ToyWarsServer'])
        self.assertIn('RoundResultBanner',embedded['ToyWarsHUD'])
        self.assertIn('BossWaveWarning',embedded['ToyWarsHUD'])
        self.assertFalse(manifest['roblox_engine_verified'])
        self.assertFalse(manifest['source_merge_verified'])

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
        self.assertEqual(r['unmerged_source_branch_head_sha'],x.PINNED_QA_HEAD)
        self.assertEqual(set(r['sources']),{row[3] for row in x.EXPECTED})
        self.assertEqual(r['status'],'UNVERIFIED_QA_BRANCH_SOURCE_PINNED_XML_ONLY')

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

    def test_only_pinned_combined_qa_branch_push_emits_artifact(self):
        valid={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':x.REPO,
               'GITHUB_EVENT_NAME':'push',
               'GITHUB_REF':'refs/heads/bootstrap/twf-factory-throughput-20261107'}
        self.assertTrue(x.actions_export_allowed(valid))
        for k,v in [('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/main'),
                    ('GITHUB_REF','refs/heads/feature/other'),('GITHUB_EVENT_NAME','pull_request'),
                    ('GITHUB_EVENT_NAME','schedule'),('GITHUB_ACTIONS','false')]:
            with self.subTest(k=k):
                self.assertFalse(x.actions_export_allowed({**valid,k:v}))

    def test_racing_xml_created_after_preflight_is_not_deleted(self):
        from unittest.mock import patch
        xml=self.out/x.XML_NAME
        real_open=Path.open
        def racing(path,mode='r',*args,**kwargs):
            if path==xml and mode=='xb':
                xml.write_bytes(b'FOREIGN_XML_RACE_WINNER')
                raise FileExistsError('another writer created XML')
            return real_open(path,mode,*args,**kwargs)
        with patch.object(Path,'open',autospec=True,side_effect=racing):
            with self.assertRaises(x.ExportBlocked):x.export(self.root,self.out)
        self.assertEqual(xml.read_bytes(),b'FOREIGN_XML_RACE_WINNER')
        self.assertFalse((self.out/x.RECEIPT_NAME).exists())

    def test_racing_receipt_created_after_xml_is_not_deleted(self):
        from unittest.mock import patch
        receipt=self.out/x.RECEIPT_NAME
        real_open=Path.open
        def racing(path,mode='r',*args,**kwargs):
            if path==receipt and mode=='xb':
                receipt.write_bytes(b'FOREIGN_RECEIPT_RACE_WINNER')
                raise FileExistsError('another writer created receipt')
            return real_open(path,mode,*args,**kwargs)
        with patch.object(Path,'open',autospec=True,side_effect=racing):
            with self.assertRaises(x.ExportBlocked):x.export(self.root,self.out)
        self.assertEqual(receipt.read_bytes(),b'FOREIGN_RECEIPT_RACE_WINNER')
        self.assertTrue((self.out/x.XML_NAME).exists())
        with self.assertRaises(x.ExportBlocked):x.export(self.root,self.out)

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
