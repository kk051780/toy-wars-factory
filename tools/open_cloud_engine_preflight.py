#!/usr/bin/env python3
"""NO-NETWORK / NO-WRITE planning for a PRIVATE Roblox Open Cloud Luau engine test.

Never sends a request, reads an API key, accepts an implicit latest place version,
proves that a place was uploaded, or certifies provider origin from caller JSON.
The specific nonpublic test target must be independently reviewed first.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

REPO = 'kk051780/toy-wars-factory'
SOURCE_MAIN = 'e5deff4d5681bca4823a3da0f848e01bc089ae6e'
PRODUCER_RUN = 41137070161
PRODUCER_ARTIFACT = 13015999142
ZIP_SHA256 = '2f662dad3e0fd81d71aaa52f34fcf1be56406cf6aecc5637b30f6de8bdac3b7b'
XML_SHA256 = '1c9bdc3dc478fe72e51870e478aa15392c47875618b86262aa7dd605e4026b33'
XML_SIZE = 54753
SCRIPT_SHA256 = 'fc343ede29c2466b0962689b183b5320d81122a807d65ad7f82e942a9268759d'
SCRIPT_NAME = 'twf_open_cloud_smoke.luau'
# Bound script runtime; this does not assert end-to-end task wall time.
TASK_TIMEOUT = '30s'
MARKER = 'TWF_OC_ENGINE_STRUCTURE_V1'
EXPECTED_TOPOLOGY = '6_expected_game_objects'
API_HOST = 'https://apis.roblox.com'
STRICT_ID = re.compile(r'[1-9][0-9]{0,18}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
UUID = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
MAX_RESPONSE = 128_000

class Blocked(ValueError):
    """Fixed reason, deliberately no credential or private raw API content."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise Blocked(reason)


def positive_id(x: object) -> int:
    # Strings are the usual safe transport for large Roblox IDs; bool never counts as int.
    if type(x) is int:
        need(0 < x < 10**19, 'INVALID_ID')
        return x
    need(type(x) is str and STRICT_ID.fullmatch(x) is not None, 'INVALID_ID')
    return int(x)


def pin_script(path: Path) -> str:
    path = Path(path)
    need(path.name == SCRIPT_NAME and path.is_file() and not path.is_symlink(), 'SCRIPT_NOT_REVIEWED')
    try:
        raw = path.read_bytes()
    except OSError:
        raise Blocked('SCRIPT_NOT_REVIEWED') from None
    need(0 < len(raw) <= 8192 and hashlib.sha256(raw).hexdigest() == SCRIPT_SHA256,
         'SCRIPT_NOT_REVIEWED')
    try:
        return raw.decode('utf-8', 'strict')
    except UnicodeError:
        raise Blocked('SCRIPT_NOT_REVIEWED') from None


def readiness(*, repository: object, source_main: object, producer_run: object,
              artifact_id: object, zip_sha256: object, xml_sha256: object,
              xml_bytes: object, universe_id: object, place_id: object,
              version_id: object, private_target_reviewed: object,
              saved_version_evidence_checked: object, script_path: Path) -> dict:
    """Prepare an immutable request *plan*, never submit it; inputs untrusted."""
    need(repository == REPO, 'FOREIGN_REPO')
    need(source_main == SOURCE_MAIN and type(source_main) is str, 'STALE_SOURCE_MAIN')
    need(type(producer_run) is int and producer_run == PRODUCER_RUN and
         type(artifact_id) is int and artifact_id == PRODUCER_ARTIFACT,
         'WRONG_ARTIFACT_PROVENANCE')
    need(type(zip_sha256) is str and zip_sha256 == ZIP_SHA256 and
         type(xml_sha256) is str and xml_sha256 == XML_SHA256 and
         type(xml_bytes) is int and xml_bytes == XML_SIZE,
         'WRONG_XML_DIGEST')
    universe, place, version = (positive_id(universe_id),positive_id(place_id),positive_id(version_id))
    # An explicit human-provided yes is insufficient real proof, but missing review blocks planning.
    need(private_target_reviewed is True, 'PRIVATE_TEST_TARGET_REVIEW_REQUIRED')
    need(saved_version_evidence_checked is True, 'EXACT_SAVED_VERSION_PROOF_REQUIRED')
    script=pin_script(script_path)
    api_path = (f'/cloud/v2/universes/{universe}/places/{place}'
                f'/versions/{version}/luau-execution-session-tasks')
    body = json.dumps({'script':script,'timeout':TASK_TIMEOUT}, ensure_ascii=False, separators=(',',':')).encode('utf-8')
    return {
        'schema':1,
        'status':'PRIVATE_OPEN_CLOUD_PLAN_NOT_EXECUTED',
        'repository':REPO,
        'source_main_sha':SOURCE_MAIN,
        'artifact_id':PRODUCER_ARTIFACT,
        'producer_run_id':PRODUCER_RUN,
        'zip_sha256':ZIP_SHA256,
        'xml_sha256':XML_SHA256,
        'xml_bytes':XML_SIZE,
        'script_sha256':SCRIPT_SHA256,
        'script_bytes':len(script.encode('utf-8')),
        'request':{
            'method':'POST',
            'api_host':API_HOST,
            'path':api_path,
            'body_sha256':hashlib.sha256(body).hexdigest(),
            'timeout':TASK_TIMEOUT,
            'content_type':'application/json',
            'body_contains_exact_reviewed_script':True,
            'credentials_embedded':False,
            'body_embedded_in_report':False,
            'explicit_version_id':version,
            'universe_id':universe,
            'place_id':place,
        },
        'next_legal_step':'EXTERNAL_AUTHORIZED_PRIVATE_PLACE_GATE_AND_INDEPENDENT_REVIEW',
        'provider_authenticated':False,
        'private_target_authenticated':False,
        'saved_version_authenticated':False,
        'host_engine_verified':False,
        'play_verified':False,
        'two_client_verified':False,
        'mobile_verified':False,
        'may_call_roblox':False,
        'may_write_github':False,
        'may_upload':False,
        'may_publish':False,
        'may_dispatch':False,
        'may_spend':False,
    }


def parse_json(payload: str) -> object:
    need(type(payload) is str, 'INVALID_RESPONSE')
    try:
        need(len(payload.encode('utf-8')) <= MAX_RESPONSE, 'INVALID_RESPONSE')
    except UnicodeError:
        raise Blocked('INVALID_RESPONSE') from None
    def strict_pairs(pairs):
        out={}
        for k,v in pairs:
            need(k not in out, 'DUPLICATE_FIELD')
            out[k]=v
        return out
    try:
        return json.loads(payload,object_pairs_hook=strict_pairs,
                          parse_constant=lambda _:need(False,'INVALID_RESPONSE'))
    except Blocked:
        raise
    except (ValueError,UnicodeError,RecursionError):
        raise Blocked('INVALID_RESPONSE') from None


def inspect_untrusted_task(plan: object, task: object) -> dict:
    """Validate caller-supplied task-shaped JSON; PASS is still NOT provider proof."""
    need(type(plan) is dict and plan.get('status')=='PRIVATE_OPEN_CLOUD_PLAN_NOT_EXECUTED'
         and type(plan.get('request')) is dict, 'INVALID_PLAN')
    req=plan['request']
    need(type(req.get('universe_id')) is int and type(req.get('place_id')) is int
         and type(req.get('explicit_version_id')) is int,
         'INVALID_PLAN')
    need(type(task) is dict, 'MALFORMED_TASK')
    path=task.get('path')
    prefix=(f'universes/{req["universe_id"]}/places/{req["place_id"]}/'
            f'versions/{req["explicit_version_id"]}/luau-execution-sessions/')
    pattern=rf'{re.escape(prefix)}{UUID}/tasks/{UUID}\Z'
    need(type(path) is str and len(path)<300 and re.fullmatch(pattern,path) is not None,
         'TASK_SCOPE_MISMATCH')
    need(task.get('state') in ('COMPLETE','FAILED','CANCELLED','PROCESSING','QUEUED') and
         type(task.get('state')) is str,'UNKNOWN_TASK_STATE')
    status='WAIT_REMOTE_TASK' if task['state'] in ('PROCESSING','QUEUED') else (
        'UNTRUSTED_TASK_FAILED' if task['state']!='COMPLETE' else 'UNTRUSTED_TASK_COMPLETE')
    result={
        'schema':1,'status':status,'task_path':path,'input_origin':'UNTRUSTED_JSON_FIXTURE',
        'script_output_verified':False,'provider_authenticated':False,
        'real_roblox_engine_verified':False,'may_publish':False,'may_dispatch':False,
        'may_spend':False,
    }
    if task['state']=='COMPLETE':
        output=task.get('output')
        need(type(output) is dict and type(output.get('results')) is list,
             'MALFORMED_TASK_OUTPUT')
        # Refuse to treat a matching marker in caller-supplied values as engine attestation.
        results=output['results']
        need(len(results)<=16, 'MALFORMED_TASK_OUTPUT')
        try:
            serialized=json.dumps(results,ensure_ascii=False,allow_nan=False)
            need(len(serialized.encode('utf-8'))<=12000,'MALFORMED_TASK_OUTPUT')
        except (ValueError,TypeError,UnicodeError,RecursionError):
            raise Blocked('MALFORMED_TASK_OUTPUT') from None
        result['claimed_marker_present']=MARKER in serialized
        result['claimed_structure_present']=EXPECTED_TOPOLOGY in serialized
    return result


def cli(argv=None) -> int:
    ap=argparse.ArgumentParser(description='No-network private Roblox headless engine proof preflight')
    ap.add_argument('--plan',action='store_true',help='Only construct a non-executing request specification')
    ap.add_argument('--universe-id')
    ap.add_argument('--place-id')
    ap.add_argument('--version-id')
    ap.add_argument('--script',default=str(Path(__file__).resolve().with_name(SCRIPT_NAME)))
    ap.add_argument('--reviewed-private-target',action='store_true')
    ap.add_argument('--checked-saved-version',action='store_true')
    ns=ap.parse_args(argv)
    if not ns.plan:
        print(json.dumps({'status':'DISABLED_NO_NETWORK_NO_EXECUTION',
                          'roblox_calls':0,'github_writes':0,'engine_verified':False},sort_keys=True))
        return 0
    try:
        report=readiness(
            repository=REPO,source_main=SOURCE_MAIN,producer_run=PRODUCER_RUN,
            artifact_id=PRODUCER_ARTIFACT,zip_sha256=ZIP_SHA256,xml_sha256=XML_SHA256,
            xml_bytes=XML_SIZE,universe_id=ns.universe_id,place_id=ns.place_id,
            version_id=ns.version_id,private_target_reviewed=ns.reviewed_private_target,
            saved_version_evidence_checked=ns.checked_saved_version,
            script_path=Path(ns.script))
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 0
    except Blocked as exc:
        print(json.dumps({'status':'BLOCKED_NO_ROBLOX_REQUEST','reason':str(exc),
                          'roblox_calls':0,'engine_verified':False}),file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(cli())
