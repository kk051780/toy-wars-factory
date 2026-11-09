"""PR163 original-source regression: privileged GitHub token transport must ignore env proxies.

No real token or HTTP request is used. The source author must run in hosted CI.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_actions_write_probe import GitHubAPI, ProbeError


class GitHubWriteProxyTransportTests(unittest.TestCase):
    def opener(self):
        client = GitHubAPI("DUMMY_TEST_TOKEN_NO_NETWORK")
        opener = getattr(client._transport, "__self__", None)
        self.assertIsInstance(opener, request.OpenerDirector)
        return opener

    def test_uppercase_and_lowercase_https_proxy_are_not_inherited(self):
        with patch.dict(os.environ, {"HTTPS_PROXY": "http://127.0.0.1:18761",
                                     "https_proxy": "http://127.0.0.1:18761"}):
            opener = self.opener()
            self.assertFalse([h for h in opener.handlers
                              if isinstance(h, request.ProxyHandler)],
                             "Do not route bearer-bearing GitHub API via environment proxy")

    def test_all_proxy_is_not_inherited(self):
        with patch.dict(os.environ, {"HTTPS_PROXY": "http://127.0.0.1:18762",
                                     "https_proxy": "http://127.0.0.1:18762",
                                     "ALL_PROXY": "http://127.0.0.1:18762",
                                     "all_proxy": "http://127.0.0.1:18762"}):
            opener = self.opener()
            self.assertFalse([h for h in opener.handlers
                              if isinstance(h, request.ProxyHandler)],
                             "Do not route bearer-bearing GitHub API via ALL_PROXY")

    def test_https_redirects_remain_denied(self):
        opener = self.opener()
        handlers = [h for h in opener.handlers
                    if isinstance(h, request.HTTPRedirectHandler)]
        self.assertEqual(len(handlers), 1)
        req = request.Request("https://api.github.com/repos/kk051780/toy-wars-factory/actions/runs/1",
                              headers={"Authorization": "Bearer DUMMY_TEST_TOKEN_NO_NETWORK"})
        with self.assertRaisesRegex(ProbeError, "^GITHUB_REDIRECT_DENIED$"):
            handlers[0].redirect_request(req, None, 302, "synthetic",
                                         {"location": "https://example.invalid/"},
                                         "https://example.invalid/")

    def test_explicit_injected_transport_is_unchanged(self):
        sentinel = lambda req, timeout=12: None
        client = GitHubAPI("DUMMY_TEST_TOKEN_NO_NETWORK", transport=sentinel)
        self.assertIs(client._transport, sentinel)


if __name__ == "__main__":
    unittest.main()
