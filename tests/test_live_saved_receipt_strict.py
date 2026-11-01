"""A14 Saved-only API response decoding and HTTP trust boundary; NO real network."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import roblox_private_xml_saved as stage
import test_system_private_xml_saved as fixture

class Resp:
    def __init__(self,url,body,status=200,content_type='application/json'):
        self.url=url
        self.body=body
        self.status=status
        self.headers={'Content-Type':content_type}
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def geturl(self):return self.url
    def read(self,n):return self.body[:n]

class SavedResponseSecurity(unittest.TestCase):
    def setUp(self):
        self.body=fixture.build_xml()
        self.cfg=fixture.config(self.body)
        self.env={
            'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':stage.REPOSITORY,
            'GITHUB_REF':'refs/heads/main',
            'GITHUB_SHA':self.cfg.reviewed_workflow_sha,
            'GITHUB_EVENT_NAME':'workflow_dispatch',
            'TWF_ACCEPTED_GAME_SOURCE_SHA':self.cfg.source_main_sha,
            'TWF_REVIEWED_MAIN_SHA':self.cfg.reviewed_workflow_sha,
            'TWF_PRIVATE_STAGE_APPROVED':'true',
            'TWF_PROTECTED_ENVIRONMENT':'roblox-private-test',
            'TWF_TEST_UNIVERSE_ID':self.cfg.test_universe_id,
            'TWF_TEST_PLACE_ID':self.cfg.test_place_id,
            'TWF_PROD_UNIVERSE_ID':self.cfg.production_universe_id,
            'TWF_PROD_PLACE_ID':self.cfg.production_place_id
        }
        self.key='FAKE_TEST_ONLY_NEVER_REAL_API_KEY'
    def go(self,body=b'{"versionNumber":56}',status=200,content_type='application/json'):
        opener=mock.Mock()
        opener.open.side_effect=lambda req,timeout:Resp(req.full_url,body,status,content_type)
        with mock.patch.object(stage.urllib.request,'build_opener',return_value=opener):
            transport=stage.LiveSavedXmlTransport(
                self.cfg,api_key=self.key,environment=self.env)
            request=stage.saved_xml_request(self.cfg,self.body)
            try:
                result=transport(request)
                return result,opener
            except stage.XmlStageError:
                self.assertEqual(opener.open.call_count,1)
                with self.assertRaises(stage.XmlStageError):
                    transport(request) # must never retry after a bad response
                self.assertEqual(opener.open.call_count,1)
                raise
    def test_01_valid_saved_receipt_remains_untrusted(self):
        value,opener=self.go()
        self.assertEqual(stage.saved_version(value),'56')
        self.assertEqual(opener.open.call_count,1)
    def test_02_duplicate_version_number_rejected(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(b'{"versionNumber":55,"versionNumber":56}')
    def test_03_duplicate_unknown_json_field_rejected(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(b'{"versionNumber":56,"meta":{"a":1,"a":2}}')
    def test_04_nonfinite_json_nan_rejected(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(b'{"versionNumber":56,"other":NaN}')
    def test_05_nonfinite_json_infinity_rejected(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(b'{"versionNumber":56,"other":Infinity}')
    def test_06_wrong_response_content_type_rejected(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(content_type='text/html')
    def test_07_non_200_status_rejected_without_retry(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(status=202)
    def test_08_non_bytes_response_rejected(self):
        with self.assertRaises(stage.XmlStageError):
            self.go('{"versionNumber":56}')
    def test_09_newline_in_api_key_rejected_before_network(self):
        opener=mock.Mock()
        with mock.patch.object(stage.urllib.request,'build_opener',return_value=opener):
            with self.assertRaises(stage.XmlStageError):
                stage.LiveSavedXmlTransport(
                    self.cfg,api_key='FAKE_ONLY_INVALID\nTOKEN_12345',environment=self.env)
        opener.open.assert_not_called()
    def test_10_crlf_in_api_key_rejected_before_network(self):
        opener=mock.Mock()
        with mock.patch.object(stage.urllib.request,'build_opener',return_value=opener):
            with self.assertRaises(stage.XmlStageError):
                stage.LiveSavedXmlTransport(
                    self.cfg,api_key='FAKE_ONLY_INVALID\r\nTOKEN_12345',environment=self.env)
        opener.open.assert_not_called()
    def test_11_malformed_json_rejected_without_retry(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(b'{"versionNumber":')
    def test_12_no_extra_publish_endpoint_on_failure(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(b'{"versionNumber":55,"versionNumber":56}')
    def test_13_normal_json_utf8_strict(self):
        with self.assertRaises(stage.XmlStageError):
            self.go(b'{"versionNumber":56,"other":"\xff"}')

if __name__=='__main__':unittest.main()
