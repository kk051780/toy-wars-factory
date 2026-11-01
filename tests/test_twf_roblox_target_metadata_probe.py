"""Offline mock-backed tests. Success NEVER certifies actual Roblox origin."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import twf_roblox_target_metadata_probe as mod

KEY = 'scope-read-only-test-key-1234'

class Response:
    status = 200
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    def __init__(self, url, body=None, status=200, ctype=None):
        self.url = url
        self.status = status
        if ctype is not None:
            self.headers = {'Content-Type': ctype}
        self.body = body if body is not None else json.dumps({'path': url.split('/cloud/v2/')[1]}).encode()
    def geturl(self): return self.url
    def read(self, count): return self.body[:count]
    def __enter__(self): return self
    def __exit__(self, *args): return False

class Opener:
    def __init__(self, transforms=None):
        self.calls = []
        self.transforms = transforms or {}
    def open(self, request, timeout):
        self.calls.append((request, timeout))
        path = request.full_url.split('/cloud/v2/')[1]
        transform = self.transforms.get(len(self.calls), lambda u: Response(u))
        return transform(request.full_url)

def target(**kwargs):
    return mod.Target('100', '200', **kwargs)

class ReadOnlyMetadataTests(unittest.TestCase):
    def test_two_gets_with_canonical_scope(self):
        transport = Opener()
        result = mod.inspect_existing_target(target(), KEY, opener=transport)
        self.assertEqual(result['http_get_count'], 2)
        self.assertEqual(result['http_post_count'], 0)
        self.assertEqual(result['universe_path'], 'universes/100')
        self.assertEqual(result['place_path'], 'universes/100/places/200')
        self.assertTrue(all(c[0].get_method() == 'GET' and c[1] == 8 for c in transport.calls))
        self.assertTrue(all(c[0].full_url.startswith('https://apis.roblox.com/cloud/v2/') for c in transport.calls))
        self.assertEqual(result['automatic_retries'], 0)
        for flag in ('provider_authenticated','owner_authenticated','nonpublic_status_verified',
                     'saved_version_verified','roblox_engine_verified','may_upload',
                     'may_execute','may_publish','may_merge','api_key_returned','raw_body_returned'):
            self.assertIs(result[flag], False, flag)
        self.assertNotIn(KEY, str(result))

    def test_wrong_universe_rejected_before_second_get(self):
        transport = Opener({1: lambda u: Response(u, b'{"path":"universes/999"}')})
        with self.assertRaisesRegex(mod.TargetHold, 'RESOURCE_IDENTITY_MISMATCH'):
            mod.inspect_existing_target(target(), KEY, opener=transport)
        self.assertEqual(len(transport.calls), 1)

    def test_wrong_place_rejected(self):
        transport = Opener({2: lambda u: Response(u, b'{"path":"universes/100/places/999"}')})
        with self.assertRaisesRegex(mod.TargetHold, 'RESOURCE_IDENTITY_MISMATCH'):
            mod.inspect_existing_target(target(), KEY, opener=transport)
        self.assertEqual(len(transport.calls), 2)

    def test_invalid_target_ids_are_rejected_without_calls(self):
        for u, p in (('0','200'),('001','200'),('a','200'),('100','200/extra'),
                     (100,'200'),('100',''),('100',' 200')):
            with self.subTest(ids=(u,p)), self.assertRaises(mod.TargetHold):
                mod.inspect_existing_target(mod.Target(u,p), KEY, opener=Opener())

    def test_no_production_can_be_declared_without_fake_ids(self):
        self.assertEqual(target().paths(), ('universes/100','universes/100/places/200'))

    def test_partial_production_reference_denied(self):
        with self.assertRaisesRegex(mod.TargetHold, 'INVALID_PRODUCTION_REFERENCE'):
            target(production_universe_id='300').paths()

    def test_production_collision_denied_even_one_id(self):
        for prod in ({'production_universe_id':'100','production_place_id':'400'},
                     {'production_universe_id':'300','production_place_id':'200'}):
            with self.subTest(prod=prod),self.assertRaisesRegex(mod.TargetHold,'PRODUCTION_TARGET_COLLISION'):
                target(**prod).paths()

    def test_distinct_prod_reference_allowed_without_claiming_privacy(self):
        res = mod.inspect_existing_target(target(production_universe_id='300',production_place_id='400'),KEY,opener=Opener())
        self.assertFalse(res['nonpublic_status_verified'])

    def test_api_key_missing_or_control_char_denied(self):
        for key in ('', 'short', KEY+'\r', KEY+'\n', KEY+'\x00', 123):
            with self.subTest(key=str(key)[:4]),self.assertRaisesRegex(mod.TargetHold,'BAD_SCOPED_API_KEY'):
                mod.inspect_existing_target(target(),key,opener=Opener())

    def test_error_from_transport_is_redacted_and_not_retried(self):
        opener=Opener({1:lambda u: (_ for _ in ()).throw(RuntimeError('SECRET-TOKEN-DONT-LOG'))})
        with self.assertRaises(mod.TargetHold) as err:
            mod.inspect_existing_target(target(),KEY,opener=opener)
        self.assertEqual(str(err.exception),'GET_FAILED_NO_RETRY')
        self.assertEqual(len(opener.calls),1)

    def test_duplicate_json_field_rejected(self):
        opener=Opener({1:lambda u:Response(u,b'{"path":"universes/100","path":"universes/100"}')})
        with self.assertRaisesRegex(mod.TargetHold,'DUPLICATE_JSON_FIELD'):
            mod.inspect_existing_target(target(),KEY,opener=opener)

    def test_nonfinite_json_rejected(self):
        opener=Opener({1:lambda u:Response(u,b'{"path":"universes/100","x":NaN}')})
        with self.assertRaisesRegex(mod.TargetHold,'NONFINITE_JSON_VALUE'):
            mod.inspect_existing_target(target(),KEY,opener=opener)

    def test_overlarge_response_rejected(self):
        opener=Opener({1:lambda u:Response(u,b'X'*65537)})
        with self.assertRaisesRegex(mod.TargetHold,'UNSAFE_METADATA_RESPONSE'):
            mod.inspect_existing_target(target(),KEY,opener=opener)

    def test_wrong_status_and_no_second_get(self):
        for status in (201,301,401,403,429,500):
            opener=Opener({1:lambda u: Response(u,status=status)})
            with self.subTest(status=status), self.assertRaisesRegex(mod.TargetHold,'UNEXPECTED_STATUS'):
                mod.inspect_existing_target(target(),KEY,opener=opener)
            self.assertEqual(len(opener.calls),1)

    def test_wrong_content_type_rejected(self):
        opener=Opener({1:lambda u:Response(u,ctype='text/html')})
        with self.assertRaisesRegex(mod.TargetHold,'UNEXPECTED_CONTENT_TYPE'):
            mod.inspect_existing_target(target(),KEY,opener=opener)

    def test_redirected_url_rejected(self):
        opener=Opener({1:lambda u:Response('https://evil.invalid/redirect', b'{"path":"universes/100"}')})
        with self.assertRaisesRegex(mod.TargetHold,'UNEXPECTED_REDIRECT'):
            mod.inspect_existing_target(target(),KEY,opener=opener)

    def test_array_response_rejected(self):
        opener=Opener({1:lambda u:Response(u,b'[1,2]')})
        with self.assertRaisesRegex(mod.TargetHold,'METADATA_NOT_OBJECT'):
            mod.inspect_existing_target(target(),KEY,opener=opener)

    def test_no_redirect_and_no_proxy_handlers(self):
        with patch.object(mod.urllib.request,'build_opener',return_value=object()) as builder:
            mod.no_proxy_opener()
            types=tuple(type(x).__name__ for x in builder.call_args.args)
        self.assertIn('ProxyHandler', types)
        self.assertIn('NoRedirect', types)
        self.assertIn('HTTPSHandler', types)

if __name__=='__main__': unittest.main()
