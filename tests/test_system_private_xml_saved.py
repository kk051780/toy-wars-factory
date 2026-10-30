"""Native-file XML Saved bridge regressions; never calls Roblox or Studio."""
import hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
from contextlib import redirect_stdout,redirect_stderr
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import roblox_private_xml_saved as x
import stage_private_xml_saved as cli

SOURCE_FILES={
    ('ReplicatedStorage','ToyWarsBalance'):'src/ToyWarsBalance.lua',
    ('ServerScriptService','ToyWarsServer'):'src/ToyWarsServer.server.lua',
    ('ServerScriptService','ToyWarsSmokeTest'):'src/ToyWarsSmokeTest.server.lua',
    ('StarterPlayer','StarterPlayerScripts','ToyWarsHUD'):'src/ToyWarsHUD.client.lua',
}

def build_xml(bad=None):
    root=ET.Element('roblox',version='4')
    def make(parent,path):
        cls=x.EXPECTED_TOPOLOGY[path]
        item=ET.SubElement(parent,'Item',{'class':cls,'referent':'RBX'+str(len(root.findall('.//Item'))+1)})
        ps=ET.SubElement(item,'Properties')
        ET.SubElement(ps,'string',{'name':'Name'}).text=path[-1]
        if path in SOURCE_FILES:
            ET.SubElement(ps,'ProtectedString',{'name':'Source'}).text=(ROOT/SOURCE_FILES[path]).read_text(encoding='utf-8')
        for child in [p for p in x.EXPECTED_TOPOLOGY if len(p)==len(path)+1 and p[:-1]==path]:make(item,child)
    for p in [p for p in x.EXPECTED_TOPOLOGY if len(p)==1]:make(root,p)
    if bad:bad(root)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def config(data):
    return x.XmlStageConfig('2020','3030','4040','5050',x.MAIN_BASE,hashlib.sha256(data).hexdigest(),len(data))

def replace_source(root):
    e=root.find(".//Item[@class='Script']/Properties/ProtectedString[@name='Source']")
    e.text=(e.text or '')+'-- tampered'

class ActualCurrentGameXml(unittest.TestCase):
    def setUp(self):
        self.data=build_xml()
        self.cfg=config(self.data)
    def test_current_four_sources_match_fixed_main_pins(self):
        for path,filename in SOURCE_FILES.items():
            with self.subTest(path=path):
                text=(ROOT/filename).read_bytes()
                self.assertEqual(hashlib.sha256(text).hexdigest(),x.SOURCE_PINS[path][1])
    def test_valid_xml_is_untrusted_not_engine(self):
        o=x.check_rbxlx_bytes(self.data,self.cfg)
        self.assertEqual(o['instance_count'],10)
        self.assertEqual(len(o['source_sha256']),4)
        self.assertEqual(o['format'],'RBXLX_XML')
        self.assertFalse(o['roblox_upload_attested'])
        self.assertFalse(o['roblox_engine_verified'])
    def test_xml_source_tamper_rejected_even_with_updated_whole_file_hash(self):
        data=build_xml(replace_source)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_missing_source_rejected(self):
        def modify(root):root.find(".//Item[@class='Script']/Properties/ProtectedString[@name='Source']").text=None
        data=build_xml(modify)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_extra_script_item_rejected(self):
        def modify(root):
            holder=root.find(".//Item[@class='ServerScriptService']")
            i=ET.SubElement(holder,'Item',{'class':'Script'})
            p=ET.SubElement(i,'Properties');ET.SubElement(p,'string',{'name':'Name'}).text='Unknown'
        data=build_xml(modify)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_hidden_nested_item_rejected(self):
        def modify(root):
            holder=root.find(".//Item[@class='ServerScriptService']")
            hidden=ET.SubElement(holder,'UnknownWrapper')
            ET.SubElement(hidden,'Item',{'class':'Script'})
        data=build_xml(modify)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_unknown_root_payload_rejected(self):
        def modify(root):
            hidden=ET.SubElement(root,'UnknownWrapper')
            ET.SubElement(hidden,'Item',{'class':'Script'})
        data=build_xml(modify)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_missing_remote_event_rejected(self):
        def modify(root):
            holder=root.find(".//Item[@class='ReplicatedStorage']")
            holder.remove(holder.find("./Item[@class='RemoteEvent']"))
        data=build_xml(modify)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_duplicate_instance_rejected(self):
        def modify(root):
            holder=root.find(".//Item[@class='ReplicatedStorage']")
            remote=holder.find("./Item[@class='RemoteEvent']")
            holder.append(ET.fromstring(ET.tostring(remote)))
        data=build_xml(modify)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_wrong_class_rejected(self):
        def modify(root):root.find(".//Item[@class='ModuleScript']").set('class','Script')
        data=build_xml(modify)
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_whole_artifact_digest_rejected(self):
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(self.data,config(self.data+b'A'))
    def test_xml_dtd_entity_rejected(self):
        data=b'<!DOCTYPE roblox [<!ENTITY x "bad">]>'+self.data
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(data,config(data))
    def test_false_main_sha_rejected(self):
        from dataclasses import replace
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(self.data,replace(self.cfg,source_main_sha='b'*40))
    def test_bool_size_rejected(self):
        from dataclasses import replace
        with self.assertRaises(x.XmlStageError):x.check_rbxlx_bytes(self.data,replace(self.cfg,rbxlx_bytes=True))
    def test_regular_file_and_symlink_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'place.rbxlx';p.write_bytes(self.data)
            self.assertEqual(x.check_rbxlx_file(p,self.cfg),self.data)
            link=Path(temp)/'link.rbxlx';link.symlink_to(p)
            with self.assertRaises(x.XmlStageError):x.check_rbxlx_file(link,self.cfg)
    def test_wrong_extension_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'place.rbxl';p.write_bytes(self.data)
            with self.assertRaises(x.XmlStageError):x.check_rbxlx_file(p,self.cfg)

class SavedOnlyXmlPropertySecurity(unittest.TestCase):
    """Only the exact minimal XML emitted by PR147 is admitted for test Saved staging."""

    def check(self, edit):
        payload = build_xml(edit)
        with self.assertRaises(x.XmlStageError):
            x.check_rbxlx_bytes(payload, config(payload))

    def test_original_ten_instance_xml_remains_valid(self):
        self.assertEqual(x.check_rbxlx_bytes(build_xml(), config(build_xml()))['instance_count'], 10)

    def test_reject_script_disabled_property(self):
        def edit(root):
            script = root.find(".//Item[@class='Script']")
            ET.SubElement(script.find('Properties'), 'bool', {'name':'Enabled'}).text = 'false'
        self.check(edit)

    def test_reject_script_run_context_override(self):
        def edit(root):
            script = root.find(".//Item[@class='Script']")
            ET.SubElement(script.find('Properties'), 'token', {'name':'RunContext'}).text = '2'
        self.check(edit)

    def test_reject_remote_event_extra_source(self):
        def edit(root):
            event = root.find(".//Item[@class='RemoteEvent']")
            ET.SubElement(event.find('Properties'), 'ProtectedString', {'name':'Source'}).text = 'print(1)'
        self.check(edit)

    def test_reject_workspace_extra_property(self):
        def edit(root):
            workspace = root.find("./Item[@class='Workspace']")
            ET.SubElement(workspace.find('Properties'), 'bool', {'name':'StreamingEnabled'}).text = 'true'
        self.check(edit)

    def test_reject_script_source_downgrade_to_string(self):
        def edit(root):
            source = root.find(".//Item[@class='Script']/Properties/ProtectedString[@name='Source']")
            source.tag = 'string'
        self.check(edit)

    def test_reject_duplicate_roblox_referent(self):
        def edit(root):
            a = root.find("./Item[@class='Workspace']")
            b = root.find("./Item[@class='ReplicatedStorage']")
            b.set('referent', a.get('referent'))
        self.check(edit)

    def test_reject_missing_roblox_referent(self):
        def edit(root):
            root.find(".//Item[@class='RemoteEvent']").attrib.pop('referent')
        self.check(edit)

    def test_reject_empty_roblox_referent(self):
        def edit(root):
            root.find(".//Item[@class='RemoteEvent']").set('referent','')
        self.check(edit)

    def test_reject_surprise_roblox_item_attribute(self):
        def edit(root):
            root.find(".//Item[@class='Script']").set('RunContext', 'client')
        self.check(edit)

class SavedOnlyTransport(unittest.TestCase):
    def setUp(self):
        self.data=build_xml();self.cfg=config(self.data)
    def test_xml_saved_endpoint_and_content_type(self):
        req=x.saved_xml_request(self.cfg,self.data)
        self.assertEqual(req.method,'POST')
        self.assertEqual(req.content_type,'application/xml')
        self.assertTrue(req.url.endswith('/versions?versionType=Saved'))
        self.assertNotIn('Published',req.url)
        self.assertNotIn('/5050/',req.url)
    def test_saved_version_true_int_required(self):
        self.assertEqual(x.saved_version({'versionNumber':56}),'56')
        for v in [True,0,-1,'56',1.1,None]:
            with self.subTest(v=v),self.assertRaises(x.XmlStageError):x.saved_version({'versionNumber':v})
    def test_no_extra_version_response_keys(self):
        with self.assertRaises(x.XmlStageError):x.saved_version({'versionNumber':56,'published':True})
    def test_injected_saved_v56_receipt_never_attests(self):
        seen=[]
        def fake(r):seen.append(r);return {'versionNumber':56}
        o=x.stage_once(self.cfg,self.data,fake)
        self.assertEqual(len(seen),1)
        self.assertEqual(o['version'],'56')
        self.assertEqual(o['version_type'],'Saved')
        self.assertFalse(o['roblox_upload_attested'])
        self.assertFalse(o['engine_verified'])
    def test_private_and_production_must_differ(self):
        from dataclasses import replace
        for cfg in [replace(self.cfg,production_universe_id=self.cfg.test_universe_id),replace(self.cfg,production_place_id=self.cfg.test_place_id)]:
            with self.assertRaises(x.XmlStageError):cfg.check()
    def test_environment_attestation_strings_are_required_but_not_proof(self):
        env={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':x.REPOSITORY,'GITHUB_REF':'refs/heads/main',
             'GITHUB_SHA':x.MAIN_BASE,'GITHUB_EVENT_NAME':'workflow_dispatch',
             'TWF_PRIVATE_STAGE_APPROVED':'true','TWF_PROTECTED_ENVIRONMENT':'roblox-private-test',
             'TWF_TEST_UNIVERSE_ID':'2020','TWF_TEST_PLACE_ID':'3030',
             'TWF_PROD_UNIVERSE_ID':'4040','TWF_PROD_PLACE_ID':'5050'}
        x.check_host_environment(self.cfg,env)
        for key in ['GITHUB_SHA','GITHUB_EVENT_NAME','TWF_PRIVATE_STAGE_APPROVED','TWF_PROD_PLACE_ID']:
            mutated=dict(env);mutated[key]='wrong'
            with self.subTest(key=key),self.assertRaises(x.XmlStageError):x.check_host_environment(self.cfg,mutated)
    def test_default_cli_zero_network(self):
        with redirect_stdout(io.StringIO()) as out:
            code=cli.main([],environ={})
        self.assertEqual(code,0)
        self.assertEqual(json.loads(out.getvalue())['network_calls'],0)
    def test_live_cli_missing_private_auth_fail_closed(self):
        with mock.patch.object(cli,'LiveSavedXmlTransport') as sent:
            with redirect_stderr(io.StringIO()) as err:
                code=cli.main(['--live'],environ={})
            self.assertEqual(code,2)
            sent.assert_not_called()
            self.assertEqual(json.loads(err.getvalue())['status'],'BLOCKED_OR_UNCERTAIN_XML_SAVED')
    def test_transport_single_use_and_no_redirect(self):
        env={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':x.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_SHA':x.MAIN_BASE,'GITHUB_EVENT_NAME':'workflow_dispatch',
             'TWF_PRIVATE_STAGE_APPROVED':'true','TWF_PROTECTED_ENVIRONMENT':'roblox-private-test',
             'TWF_TEST_UNIVERSE_ID':'2020','TWF_TEST_PLACE_ID':'3030',
             'TWF_PROD_UNIVERSE_ID':'4040','TWF_PROD_PLACE_ID':'5050'}
        class FakeResponse:
            def __init__(self,url):self.url=url
            def __enter__(self):return self
            def __exit__(self,*a):return None
            def geturl(self):return self.url
            def read(self,n):return b'{"versionNumber":56}'
        opener=mock.Mock()
        opener.open.side_effect=lambda req,timeout:FakeResponse(req.full_url)
        with mock.patch.object(x.urllib.request,'build_opener',return_value=opener):
            t=x.LiveSavedXmlTransport(self.cfg,api_key='fake-test-key-24chars-long',environment=env)
            req=x.saved_xml_request(self.cfg,self.data)
            self.assertEqual(x.saved_version(t(req)),'56')
            with self.assertRaises(x.XmlStageError):t(req)
            self.assertEqual(opener.open.call_count,1)
            sent=opener.open.call_args.args[0]
            self.assertEqual(sent.headers.get('Content-type'),'application/xml')
            self.assertNotIn('Published',sent.full_url)
    def test_changed_payload_denied_before_transport(self):
        env={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':x.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_SHA':x.MAIN_BASE,'GITHUB_EVENT_NAME':'workflow_dispatch',
             'TWF_PRIVATE_STAGE_APPROVED':'true','TWF_PROTECTED_ENVIRONMENT':'roblox-private-test',
             'TWF_TEST_UNIVERSE_ID':'2020','TWF_TEST_PLACE_ID':'3030',
             'TWF_PROD_UNIVERSE_ID':'4040','TWF_PROD_PLACE_ID':'5050'}
        opener=mock.Mock()
        with mock.patch.object(x.urllib.request,'build_opener',return_value=opener):
            t=x.LiveSavedXmlTransport(self.cfg,api_key='fake-test-key-24chars-long',environment=env)
            req=x.saved_xml_request(self.cfg,self.data)
            from dataclasses import replace
            with self.assertRaises(x.XmlStageError):t(replace(req,url=req.url.replace('Saved','Published')))
            opener.open.assert_not_called()
    def test_http_error_not_retried(self):
        env={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':x.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_SHA':x.MAIN_BASE,'GITHUB_EVENT_NAME':'workflow_dispatch',
             'TWF_PRIVATE_STAGE_APPROVED':'true','TWF_PROTECTED_ENVIRONMENT':'roblox-private-test',
             'TWF_TEST_UNIVERSE_ID':'2020','TWF_TEST_PLACE_ID':'3030',
             'TWF_PROD_UNIVERSE_ID':'4040','TWF_PROD_PLACE_ID':'5050'}
        opener=mock.Mock()
        opener.open.side_effect=x.urllib.error.URLError('fake-network-offline')
        with mock.patch.object(x.urllib.request,'build_opener',return_value=opener):
            t=x.LiveSavedXmlTransport(self.cfg,api_key='fake-test-key-24chars-long',environment=env)
            req=x.saved_xml_request(self.cfg,self.data)
            with self.assertRaises(x.XmlStageError):t(req)
            with self.assertRaises(x.XmlStageError):t(req)
            self.assertEqual(opener.open.call_count,1)

if __name__=='__main__':unittest.main()
