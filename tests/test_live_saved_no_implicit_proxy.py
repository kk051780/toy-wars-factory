"""Fail-closed regression for future approved Roblox API-key host. No network calls."""
from __future__ import annotations
import os, sys, unittest, urllib.request
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import roblox_private_xml_saved as x

class ProxyIsolationTests(unittest.TestCase):
    def config(self):
        return x.XmlStageConfig(
            test_universe_id='12345', test_place_id='67890',
            production_universe_id='98765', production_place_id='54321',
            source_main_sha=x.MAIN_BASE, rbxlx_sha256='f'*64,
            rbxlx_bytes=54753, reviewed_workflow_sha='e'*40)

    def host_env(self, cfg):
        return dict(GITHUB_ACTIONS='true',
            GITHUB_REPOSITORY=x.REPOSITORY,GITHUB_REF='refs/heads/main',
            GITHUB_SHA=cfg.reviewed_workflow_sha,GITHUB_EVENT_NAME='workflow_dispatch',
            TWF_ACCEPTED_GAME_SOURCE_SHA=cfg.source_main_sha,
            TWF_REVIEWED_MAIN_SHA=cfg.reviewed_workflow_sha,
            TWF_PRIVATE_STAGE_APPROVED='true', TWF_PROTECTED_ENVIRONMENT='roblox-private-test',
            TWF_TEST_UNIVERSE_ID=cfg.test_universe_id,
            TWF_TEST_PLACE_ID=cfg.test_place_id,
            TWF_PROD_UNIVERSE_ID=cfg.production_universe_id,
            TWF_PROD_PLACE_ID=cfg.production_place_id)

    def make(self, proxies):
        cfg=self.config()
        with patch.dict(os.environ,proxies,clear=True):
            return x.LiveSavedXmlTransport(cfg,api_key='TEST_ONLY_NOT_SECRET_12345',environment=self.host_env(cfg))

    def test_https_proxy_env_does_not_route_token_via_implicit_proxy(self):
        transport=self.make({'HTTPS_PROXY':'http://proxy.invalid:8080'})
        configured=[h.proxies for h in transport._opener.handlers
                    if isinstance(h,urllib.request.ProxyHandler)]
        self.assertFalse(any(p.get('https') for p in configured), configured)

    def test_lowercase_https_proxy_env_is_ignored(self):
        transport=self.make({'https_proxy':'http://proxy.invalid:8080'})
        configured=[h.proxies for h in transport._opener.handlers
                    if isinstance(h,urllib.request.ProxyHandler)]
        self.assertFalse(any(p.get('https') for p in configured), configured)

    def test_https_proxy_and_http_proxy_env_are_ignored(self):
        transport=self.make({'HTTPS_PROXY':'http://proxy.invalid:8080',
                             'HTTP_PROXY':'http://proxy.invalid:8000'})
        configured=[h.proxies for h in transport._opener.handlers
                    if isinstance(h,urllib.request.ProxyHandler)]
        self.assertFalse(any(p.get('https') or p.get('http') for p in configured),configured)

    def test_no_redirect_guard_is_still_present(self):
        transport=self.make({'HTTPS_PROXY':'http://proxy.invalid:8080'})
        self.assertTrue(any(isinstance(h,x.NoRedirect) for h in transport._opener.handlers))
        handler=next(h for h in transport._opener.handlers if isinstance(h,x.NoRedirect))
        self.assertIsNone(handler.redirect_request(None,None,307,None,None,None))

if __name__=='__main__': unittest.main()
