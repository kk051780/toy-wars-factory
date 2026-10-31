"""Token-safe redirect regression for PR153; no actual GitHub network requests."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import HTTPRedirectHandler, Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from system_runner_identity_probe import _NoRedirect, _SAFE_OPEN, NotVerified, github_get

API = 'https://api.github.com/repos/kk051780/toy-wars-factory/branches/main'
FAKE = 'TEST_ONLY_NOT_REAL_SECRET'

def fake_request():
    return Request(API, headers={'Authorization': 'Bearer '+FAKE})

class RedirectSafety(unittest.TestCase):
    def test_confirm_python_default_would_forward_token(self):
        req = HTTPRedirectHandler().redirect_request(fake_request(), None, 302, 'Found', {}, 'https://other.example.test/collect')
        self.assertEqual(req.get_header('Authorization'), 'Bearer '+FAKE)

    def test_no_redirect_for_all_3xx(self):
        for code in (300, 301, 302, 303, 304, 305, 307, 308):
            with self.subTest(code=code), self.assertRaisesRegex(NotVerified, '^REDIRECT_REFUSED$'):
                _NoRedirect().redirect_request(fake_request(), None, code, 'Moved', {}, 'https://other.example.test/collect')

    def test_no_redirect_same_host(self):
        with self.assertRaisesRegex(NotVerified, '^REDIRECT_REFUSED$'):
            _NoRedirect().redirect_request(fake_request(), None, 301, 'Moved', {}, API+'?new=1')

    def test_no_redirect_downgrade(self):
        with self.assertRaisesRegex(NotVerified, '^REDIRECT_REFUSED$'):
            _NoRedirect().redirect_request(fake_request(), None, 302, 'Moved', {}, 'http://other.example.test/')

    def test_no_token_or_url_echo(self):
        try:
            _NoRedirect().redirect_request(fake_request(), None, 302, 'Moved', {}, 'https://other.example.test/'+FAKE)
        except NotVerified as e:
            self.assertEqual(str(e), 'REDIRECT_REFUSED')
            self.assertNotIn(FAKE, str(e))
            self.assertNotIn('other.example', str(e))
        else:
            self.fail('Expected fail-closed redirect exception')

    def test_secure_opener_has_single_redirect_handler(self):
        handlers = [h for h in _SAFE_OPEN.__self__.handlers if isinstance(h, HTTPRedirectHandler)]
        self.assertEqual(len(handlers), 1)
        self.assertIsInstance(handlers[0], _NoRedirect)

    def test_secure_opener_retains_tls_validation_handler(self):
        names = {type(h).__name__ for h in _SAFE_OPEN.__self__.handlers}
        self.assertIn('HTTPSHandler', names)
        self.assertIn('HTTPErrorProcessor', names)

    def test_actual_helper_converts_redirect_to_fixed_failure(self):
        with patch('system_runner_identity_probe._SAFE_OPEN', side_effect=NotVerified('REDIRECT_REFUSED')):
            with self.assertRaisesRegex(NotVerified, '^GET_UNAVAILABLE$'):
                github_get('/repos/kk051780/toy-wars-factory/branches/main', FAKE)

    def test_no_open_url_on_bad_scope(self):
        with patch('system_runner_identity_probe._SAFE_OPEN') as mocked:
            with self.assertRaisesRegex(NotVerified, '^UNSCOPED_GET$'):
                github_get('/repos/other/repo/branches/main', FAKE)
            mocked.assert_not_called()

    def test_missing_token_avoids_network(self):
        with patch('system_runner_identity_probe._SAFE_OPEN') as mocked:
            with self.assertRaisesRegex(NotVerified, '^MISSING_TOKEN$'):
                github_get('/repos/kk051780/toy-wars-factory/branches/main', '')
            mocked.assert_not_called()

if __name__ == '__main__':
    unittest.main()
