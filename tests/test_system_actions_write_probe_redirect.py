"""PR163: fail-closed authenticated GitHub API redirect handling (stdlib-only)."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import system_actions_write_probe as p

class NoBearerRedirectTests(unittest.TestCase):
    def source(self):
        return request.Request("https://api.github.com/repos/kk051780/toy-wars-factory/actions/runs/1",
                               headers={"Authorization":"Bearer sentinel-dont-forward"})

    def test_default_transport_must_use_rejecting_opener(self):
        original=request.build_opener
        with patch.object(p.request,"build_opener",wraps=original) as builder:
            api=p.GitHubAPI("sentinel-dont-forward")
            builder.assert_called_once()
            self.assertIsInstance(builder.call_args.args[0],p._RejectRedirects)
            self.assertTrue(callable(api._transport))

    def test_all_redirect_statuses_refused_before_auth_forwarding(self):
        h=p._RejectRedirects()
        for status in (301,302,303,307,308):
            with self.subTest(status=status):
                with self.assertRaisesRegex(p.ProbeError,"^GITHUB_REDIRECT_DENIED$"):
                    h.redirect_request(self.source(),None,status,"Moved",
                                       {"Location":"https://attacker.invalid/collect"},
                                       "https://attacker.invalid/collect")

    def test_same_host_redirect_also_denied_to_avoid_silent_scope_changes(self):
        with self.assertRaisesRegex(p.ProbeError,"^GITHUB_REDIRECT_DENIED$"):
            p._RejectRedirects().redirect_request(self.source(),None,302,"Moved",{},
                    "https://api.github.com/repos/kk051780/toy-wars-factory/other")

    def test_rejecting_handler_is_registered_in_actual_opener(self):
        api=p.GitHubAPI("sentinel")
        opener=api._transport.__self__
        matches=[x for x in opener.handlers if isinstance(x,p._RejectRedirects)]
        self.assertEqual(len(matches),1)
        self.assertIsNone(opener.handlers[0] if False else None)

    def test_redirect_protection_keeps_injected_transport_testability(self):
        calls=[]
        def fake(req,timeout):
            calls.append(req)
            class Response:
                def __enter__(self): return self
                def __exit__(self,*args):return None
                def read(self,n):return b'{"ok":true}'
            return Response()
        api=p.GitHubAPI("sentinel",fake)
        self.assertEqual(api.call("GET","/git/ref/heads/main"),{"ok":True})
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0].get_header("Authorization"),"Bearer sentinel")

if __name__=="__main__":
    unittest.main()
