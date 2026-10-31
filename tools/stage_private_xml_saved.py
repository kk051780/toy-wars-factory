#!/usr/bin/env python3
"""Opt-in reviewed one-shot XML Saved test-place upload, disabled by default.

The host MUST independently attest protected workflow identity, real GitHub
source/artifact and nonpublic Roblox destination. Environment variables are
syntax checks only. No Roblox API call or token use in default mode.
"""
from __future__ import annotations
import argparse
import json
import os
import sys

from roblox_private_xml_saved import (
    XmlStageConfig, XmlStageError, LiveSavedXmlTransport, check_rbxlx_file,
    check_host_environment, stage_once,
)

def main(argv=None,environ=None):
    p=argparse.ArgumentParser(description='Roblox private XML Saved only; never Published')
    p.add_argument('--live',action='store_true')
    p.add_argument('--xml-file')
    p.add_argument('--expected-bytes',type=int)
    a=p.parse_args(argv)
    if not a.live:
        print(json.dumps({'status':'PLAN_ONLY_NO_NETWORK','network_calls':0,'uploads':0,
                          'public_publish_authorized':False}))
        return 0
    env=dict(os.environ if environ is None else environ)
    try:
        cfg=XmlStageConfig(
            test_universe_id=env.get('TWF_TEST_UNIVERSE_ID',''),
            test_place_id=env.get('TWF_TEST_PLACE_ID',''),
            production_universe_id=env.get('TWF_PROD_UNIVERSE_ID',''),
            production_place_id=env.get('TWF_PROD_PLACE_ID',''),
            source_main_sha=env.get('TWF_ACCEPTED_GAME_SOURCE_SHA',''),
            rbxlx_sha256=env.get('TWF_XML_PLACE_SHA256',''),
            rbxlx_bytes=a.expected_bytes,
            reviewed_workflow_sha=env.get('TWF_REVIEWED_MAIN_SHA',''),
        )
        if not a.xml_file:
            raise XmlStageError('XML file not specified')
        data=check_rbxlx_file(a.xml_file,cfg)
        check_host_environment(cfg,env)
        token=env.get('ROBLOX_TEST_XML_API_KEY','')
        transport=LiveSavedXmlTransport(cfg,api_key=token,environment=env)
        outcome=stage_once(cfg,data,transport)
        print(json.dumps(outcome,sort_keys=True))
        return 0
    except (XmlStageError,OSError,TypeError,ValueError):
        # Do not reveal token, URLs, user-controlled XML or unknown ACK details.
        print(json.dumps({'status':'BLOCKED_OR_UNCERTAIN_XML_SAVED',
                          'publish_calls':0,'provider_authenticated':False}),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
