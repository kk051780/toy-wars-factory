"""Synthetic negative/structural tests. No real Roblox Studio, Windows host, or GitHub CI proof."""
from __future__ import annotations
import copy
import hashlib
import io
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'p0b_engine_receipt'))
import validate_receipt as v

SID='7f1e88b4-9809-426b-8a94-f8b82c994ed0'
TEST_PLACE='TOY_WARS_FACTORY_PR209_4TOY_TEST_ONLY.rbxlx'

def make_png():
    def chunk(tag, payload):
        return struct.pack('>I',len(payload))+tag+payload+struct.pack('>I',zlib.crc32(tag+payload)&0xffffffff)
    return v.PNG + chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0)) + chunk(b'IDAT',zlib.compress(b'\x00\x42\x77\x11')) + chunk(b'IEND',b'')

def make_xml():
    root=ET.Element('roblox',version='4')
    def add(parent,name,kind,idx,source=None):
        item=ET.SubElement(parent,'Item',{'class':kind,'referent':f'RBX{idx:032X}'})
        ps=ET.SubElement(item,'Properties')
        ET.SubElement(ps,'string',name='Name').text=name
        if source is not None:
            ET.SubElement(ps,'ProtectedString',name='Source').text=source
        return item
    ws=add(root,'Workspace','Workspace',1)
    rep=add(root,'ReplicatedStorage','ReplicatedStorage',2)
    add(rep,'ToyWarsBalance','ModuleScript',3,'-- BALANCE MOCK\n')
    add(rep,'ToyWarsSelectUnit','RemoteEvent',4)
    server=add(root,'ServerScriptService','ServerScriptService',5)
    add(server,'ToyWarsServer','Script',6,'-- SERVER MOCK\n')
    add(server,'ToyWarsSmokeTest','Script',7,'-- SMOKE MOCK\n')
    starter=add(root,'StarterPlayer','StarterPlayer',8)
    scripts=add(starter,'StarterPlayerScripts','StarterPlayerScripts',9)
    add(scripts,'ToyWarsHUD','LocalScript',10,'-- HUD MOCK\n')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def synthetic_pins():
    lookup={'ToyWarsBalance':('-- BALANCE MOCK\n','ModuleScript'),
            'ToyWarsServer':('-- SERVER MOCK\n','Script'),
            'ToyWarsSmokeTest':('-- SMOKE MOCK\n','Script'),
            'ToyWarsHUD':('-- HUD MOCK\n','LocalScript')}
    return {k:(kind,v._gitblob(code.encode())) for k,(code,kind) in lookup.items()}

def make_trace():
    return json.dumps({'events':[
        {'action':'state','mode':'Edit','tool':'Roblox_Studio.get_studio_state','studio_id':SID,'at_utc':'2026-11-09T00:00:00Z'},
        {'action':'play','success':True,'tool':'Roblox_Studio.start_stop_play','studio_id':SID,'at_utc':'2026-11-09T00:00:30Z'},
        {'action':'state','mode':'Play','tool':'Roblox_Studio.get_studio_state','studio_id':SID,'at_utc':'2026-11-09T00:01:00Z'},
        {'action':'stop','success':True,'tool':'Roblox_Studio.start_stop_play','studio_id':SID,'at_utc':'2026-11-09T00:01:30Z'},
        {'action':'state','mode':'Edit','tool':'Roblox_Studio.get_studio_state','studio_id':SID,'at_utc':'2026-11-09T00:02:00Z'},
    ]}).encode()

def sample():
    artifacts={'place_xml':make_xml(),'screenshot':make_png(),
        'console':b'11:13:00.000 TWF_QA_SUMMARY v1.2 pass=9 fail=0\n',
        'mcp_trace':make_trace()}
    doc={
        'schema':'p0b-engine-receipt/v2','repo':v.REPO,'pr':209,'head_sha':v.HEAD,
        'work_id':'P0B_R7_SYNTHETIC_TEST_20261109','fixture_only':False,
        'place':{'place_id':0,'game_id':0,'is_original':False,'is_published':False,
                 'local_backup_verified':True,'local_filename':TEST_PLACE},
        'mcp':{'studio_count':1,'studio_id':SID,'studio_id_before':SID,'studio_id_after':SID,
               'mode_before':'Edit','mode_play':'Play','mode_after':'Edit',
               'play_success':True,'stop_success':True,'time_before_utc':'2026-11-09T00:00:00Z',
               'time_play_utc':'2026-11-09T00:01:00Z','time_after_utc':'2026-11-09T00:02:00Z'},
        'qa':{'summary_line':v.SMOKE,'unsaved_warning_visible':True,'curebo_page2_visible':True,'wave_observed':9},
        'effects':{'git_source_writes':0,'studio_saves':0,'roblox_publishes':0,
                   'api_service_setting_changes':0,'datastore_observation':'NOT_MEASURED'},
        'evidence':{name+'_sha256':hashlib.sha256(content).hexdigest() for name,content in artifacts.items()},
    }
    return doc,artifacts

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.doc,self.art = sample()
        self.pinpatch=patch.dict(v.SOURCE_BLOBS, synthetic_pins(), clear=True)
        self.pinpatch.start()
        self.addCleanup(self.pinpatch.stop)
    def verdict(self):
        return v.check(self.doc,self.art,expected_head=v.HEAD)
    def rejected(self,reason):
        result=self.verdict()
        self.assertEqual(result['status'],'REJECTED',result)
        self.assertIn(reason,result['failures'])
    def test_synthetic_full_bytes_match_but_never_attested(self):
        result=self.verdict()
        self.assertEqual(result['status'],'ARTIFACT_BYTES_MATCH_UNATTESTED',result)
        for field in ('host_attested','owner_authorized','engine_verified',
                      'datastore_write_zero_verified','may_execute_commands','may_merge_or_publish'):
            self.assertIs(result[field],False)
    def test_fixture_cannot_pass(self):
        self.doc['fixture_only']=True
        self.rejected('fixture_only_or_unknown')
    def test_none_fixture_flag_cannot_pass(self):
        self.doc.pop('fixture_only')
        self.rejected('fixture_only_or_unknown')
    def test_fake_console_sha_rejected(self):
        self.doc['evidence']['console_sha256']='a'*64
        self.rejected('actual_bytes_hash_mismatch_console')
    def test_mangled_png_bytes_rejected(self):
        self.art['screenshot']+=b'X'
        self.doc['evidence']['screenshot_sha256']=hashlib.sha256(self.art['screenshot']).hexdigest()
        self.rejected('png_bytes_invalid')
    def test_fake_screenshot_hash_rejected(self):
        self.doc['evidence']['screenshot_sha256']='b'*64
        self.rejected('actual_bytes_hash_mismatch_screenshot')
    def test_replaced_xml_bytes_rejected(self):
        self.art['place_xml']=self.art['place_xml'].replace(b'-- HUD MOCK',b'-- BAD MOCK')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('source_git_blob_mismatch_ToyWarsHUD')
    def test_wrong_xml_blob_pins_do_not_pass(self):
        self.pinpatch.stop()
        self.assertIn('source_git_blob_mismatch_ToyWarsServer',v.verify_xml_bytes(self.art['place_xml']))
        self.pinpatch.start()
    def test_receipt_fake_place_hash(self):
        self.doc['evidence']['place_xml_sha256']='f'*64
        self.rejected('actual_bytes_hash_mismatch_place_xml')
    def test_console_summary_missing_after_hash_recalculation(self):
        self.art['console']=b'11:13:00.000 TWF_QA_SUMMARY v1.2 pass=8 fail=1\n'
        self.doc['evidence']['console_sha256']=hashlib.sha256(self.art['console']).hexdigest()
        self.rejected('smoke_missing_in_actual_console')
    def test_mcp_trace_wrong_studio(self):
        trace=json.loads(self.art['mcp_trace'])
        trace['events'][2]['studio_id']='11111111-1111-1111-1111-111111111111'
        self.art['mcp_trace']=json.dumps(trace).encode()
        self.doc['evidence']['mcp_trace_sha256']=hashlib.sha256(self.art['mcp_trace']).hexdigest()
        self.rejected('mcp_trace_identity_or_tool_mismatch')
    def test_mcp_trace_stop_error(self):
        trace=json.loads(self.art['mcp_trace'])
        trace['events'][3]['success']=False
        self.art['mcp_trace']=json.dumps(trace).encode()
        self.doc['evidence']['mcp_trace_sha256']=hashlib.sha256(self.art['mcp_trace']).hexdigest()
        self.rejected('mcp_trace_play_stop_failed')
    def test_mcp_trace_event_order_invalid(self):
        trace=json.loads(self.art['mcp_trace'])
        trace['events'][4]['at_utc']='2026-11-08T00:00:00Z'
        self.art['mcp_trace']=json.dumps(trace).encode()
        self.doc['evidence']['mcp_trace_sha256']=hashlib.sha256(self.art['mcp_trace']).hexdigest()
        self.rejected('mcp_trace_bad_timeline')
    def test_mcp_trace_timestamp_receipt_mismatch(self):
        self.doc['mcp']['time_after_utc']='2026-11-09T00:04:00Z'
        self.rejected('mcp_receipt_timestamp_mismatch')
    def test_mcp_trace_extra_event_rejected(self):
        trace=json.loads(self.art['mcp_trace'])
        trace['events'].append(trace['events'][4])
        self.art['mcp_trace']=json.dumps(trace).encode()
        self.doc['evidence']['mcp_trace_sha256']=hashlib.sha256(self.art['mcp_trace']).hexdigest()
        self.rejected('mcp_trace_event_count_invalid')
    def test_ambiguous_studio_count(self):
        self.doc['mcp']['studio_count']=2
        self.rejected('ambiguous_studios')
    def test_stale_head(self):
        self.doc['head_sha']='0'*40
        self.rejected('head_mismatch')
    def test_current_pr_head_can_differ_from_source_pin_when_verified_externally(self):
        new_head='d8b5540b125d5db439e7e1584b67fff838c5e137'
        self.doc['head_sha']=new_head
        result=v.check(self.doc,self.art,expected_head=new_head)
        self.assertEqual(result['status'],'ARTIFACT_BYTES_MATCH_UNATTESTED')
        self.assertFalse(result['engine_verified'])
    def test_current_pr_head_must_match_external_pinned_value(self):
        self.doc['head_sha']='d8b5540b125d5db439e7e1584b67fff838c5e137'
        self.assertIn('head_mismatch',v.check(self.doc,self.art,expected_head=v.HEAD)['failures'])
    def test_invalid_external_head_rejected(self):
        self.doc['head_sha']='G'*40
        self.assertIn('head_mismatch',v.check(self.doc,self.art,expected_head='G'*40)['failures'])
    def test_unverified_expected_head_cannot_be_omitted(self):
        with self.assertRaises(TypeError):
            v.check(self.doc,self.art)
    def test_different_expected_head_arg(self):
        r=v.check(self.doc,self.art,expected_head='0'*40)
        self.assertIn('head_mismatch',r['failures'])
    def test_published_place(self):
        self.doc['place']['place_id']=12345
        self.rejected('nonlocal_or_unknown_place_id')
    def test_original_place(self):
        self.doc['place']['is_original']=True
        self.rejected('isolation_not_declared')
    def test_no_backup(self):
        self.doc['place']['local_backup_verified']=False
        self.rejected('isolation_not_declared')
    def test_instrumented_zero_claim_not_certified(self):
        self.doc['effects']['datastore_observation']='INSTRUMENTED_ZERO'
        self.rejected('datastore_zero_not_attested')
    def test_unapproved_studio_save(self):
        self.doc['effects']['studio_saves']=1
        self.rejected('unexpected_effect_studio_saves')
    def test_api_changed(self):
        self.doc['effects']['api_service_setting_changes']=1
        self.rejected('unexpected_effect_api_service_setting_changes')
    def test_missing_file_bytes(self):
        self.art.pop('console')
        self.rejected('missing_or_oversize_artifact_console')
    def test_invalid_source_class(self):
        self.art['place_xml']=self.art['place_xml'].replace(b'class="LocalScript"',b'class="Script"')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_unexpected_class_ToyWarsHUD')
    def test_wrong_filename(self):
        self.doc['place']['local_filename']='../TOY_WARS_FACTORY_PR209_4TOY_TEST_ONLY.rbxlx'
        self.rejected('place_filename_invalid')
    def test_stray_xml_root_element_rejected(self):
        root=ET.fromstring(self.art['place_xml'])
        ET.SubElement(root,'Meta',{'run':'not-pinned'})
        self.art['place_xml']=ET.tostring(root,encoding='utf-8')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_root_extra_field_or_element')
    def test_script_disabled_property_rejected(self):
        root=ET.fromstring(self.art['place_xml'])
        for item in root.findall('.//Item'):
            n=item.find('./Properties/string[@name="Name"]')
            if n is not None and n.text == 'ToyWarsSmokeTest':
                ET.SubElement(item.find('./Properties'),'bool',{'name':'Disabled'}).text='true'
        self.art['place_xml']=ET.tostring(root,encoding='utf-8')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_unexpected_property')
    def test_hud_wrong_parent_rejected(self):
        root=ET.fromstring(self.art['place_xml'])
        starter=root.find('./Item[@class="StarterPlayer"]')
        scripts=starter.find('./Item[@class="StarterPlayerScripts"]')
        hud=scripts.find('./Item[@class="LocalScript"]')
        scripts.remove(hud)
        starter.append(hud)
        self.art['place_xml']=ET.tostring(root,encoding='utf-8')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_parent_location_invalid')
    def test_referent_wrong_format_rejected(self):
        root=ET.fromstring(self.art['place_xml'])
        root.find('./Item').set('referent','RBXnotreal')
        self.art['place_xml']=ET.tostring(root,encoding='utf-8')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_item_attributes_invalid')
    def test_unknown_script_property_name_rejected(self):
        root=ET.fromstring(self.art['place_xml'])
        hud=root.find('.//Item[@class="LocalScript"]')
        ET.SubElement(hud.find('./Properties'),'string',{'name':'LinkedSource'}).text='other'
        self.art['place_xml']=ET.tostring(root,encoding='utf-8')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_unexpected_property')
    def test_name_property_nested_element_rejected_even_with_matching_digest(self):
        root=ET.fromstring(self.art['place_xml'])
        item=root.find('./Item[@class="Workspace"]')
        field=item.find('./Properties/string[@name="Name"]')
        ET.SubElement(field,'UnexpectedNested',{'name':'UnsafeConfig'}).text='enabled'
        self.art['place_xml']=ET.tostring(root,encoding='utf-8')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_unexpected_nested_property_element')
    def test_source_property_nested_element_rejected_with_same_source_blob(self):
        root=ET.fromstring(self.art['place_xml'])
        item=root.find('.//Item[@class="LocalScript"]')
        field=item.find('./Properties/ProtectedString[@name="Source"]')
        original_blob=v._gitblob(field.text.encode('utf-8'))
        ET.SubElement(field,'UnexpectedNested').text='hidden'
        self.assertEqual(v._gitblob(field.text.encode('utf-8')), original_blob)
        self.art['place_xml']=ET.tostring(root,encoding='utf-8')
        self.doc['evidence']['place_xml_sha256']=hashlib.sha256(self.art['place_xml']).hexdigest()
        self.rejected('xml_unexpected_nested_property_element')
    def test_png_crc_flip_rejected(self):
        data=bytearray(self.art['screenshot']);data[-8]^=1
        self.art['screenshot']=bytes(data)
        self.doc['evidence']['screenshot_sha256']=hashlib.sha256(self.art['screenshot']).hexdigest()
        self.rejected('png_bytes_invalid')
    def test_cli_synthetic_files_in_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/TEST_PLACE).write_bytes(self.art['place_xml'])
            (folder/'log.txt').write_bytes(self.art['console'])
            (folder/'screen.png').write_bytes(self.art['screenshot'])
            (folder/'mcp.json').write_bytes(self.art['mcp_trace'])
            (folder/'receipt.json').write_text(json.dumps(self.doc),encoding='utf8')
            argv=['validate_receipt.py',str(folder/'receipt.json'),'--console',str(folder/'log.txt'),
                  '--screenshot',str(folder/'screen.png'),'--place-xml',str(folder/TEST_PLACE),
                  '--mcp-trace',str(folder/'mcp.json'),'--expected-head',v.HEAD]
            with patch('sys.argv',argv),patch('sys.stdout',new_callable=io.StringIO) as std:
                self.assertEqual(v.main(),0)
            result=json.loads(std.getvalue())
            self.assertEqual(result['status'],'ARTIFACT_BYTES_MATCH_UNATTESTED')
    def test_cli_fixture_flag_must_fail(self):
        self.doc['fixture_only']=True
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/TEST_PLACE).write_bytes(self.art['place_xml'])
            (folder/'log.txt').write_bytes(self.art['console'])
            (folder/'screen.png').write_bytes(self.art['screenshot'])
            (folder/'mcp.json').write_bytes(self.art['mcp_trace'])
            (folder/'receipt.json').write_text(json.dumps(self.doc),encoding='utf8')
            argv=['validate_receipt.py',str(folder/'receipt.json'),'--console',str(folder/'log.txt'),
                  '--screenshot',str(folder/'screen.png'),'--place-xml',str(folder/TEST_PLACE),
                  '--mcp-trace',str(folder/'mcp.json'),'--expected-head',v.HEAD]
            with patch('sys.argv',argv),patch('sys.stdout',new_callable=io.StringIO) as std:
                self.assertEqual(v.main(),1)
            self.assertIn('fixture_only_or_unknown',std.getvalue())
    def test_unreadable_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            path=folder/'receipt.json'
            path.write_text('{',encoding='utf8')
            argv=['validate_receipt.py',str(path),'--console',str(path),
                  '--screenshot',str(path),'--place-xml',str(path),'--mcp-trace',str(path),'--expected-head',v.HEAD]
            with patch('sys.argv',argv),patch('sys.stdout',new_callable=io.StringIO) as std:
                self.assertEqual(v.main(),1)
            self.assertIn('files_unreadable_or_invalid',std.getvalue())

if __name__=='__main__':unittest.main()
