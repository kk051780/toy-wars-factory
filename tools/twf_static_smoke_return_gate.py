"""Fail-closed typed return-value contract for the EXISTING static Roblox Cloud smoke.

Only compares UNTRUSTED, caller-provided JSON/objects to a reviewed pinned script.
No network, credentials, task start, attestation, environment setup, or authority.
Must not turn simulated output into a real Roblox/Studio/phone PASS.
"""
from __future__ import annotations
import re
import hashlib
import json
from pathlib import Path
from typing import Any

import open_cloud_engine_preflight as cloud

RETURN_KEYS = frozenset({
    'marker', 'source_main_sha', 'topology', 'wave_one', 'wave_nine',
    'server_player_session_verified', 'two_client_verified',
    'mobile_verified', 'publish_authorized',
})
FORBIDDEN_PLAN_FLAGS = (
    'provider_authenticated', 'private_target_authenticated',
    'saved_version_authenticated', 'host_engine_verified',
    'play_verified', 'two_client_verified', 'mobile_verified',
    'may_call_roblox', 'may_write_github', 'may_upload',
    'may_publish', 'may_dispatch', 'may_spend',
)

class ResultHold(ValueError):
    """Stable and non-sensitive rejection reason."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ResultHold(reason)


def _validate_plan(plan: Any) -> dict:
    need(type(plan) is dict and type(plan.get('schema')) is int and plan.get('schema') == 1 and
         plan.get('status') == 'PRIVATE_OPEN_CLOUD_PLAN_NOT_EXECUTED',
         'INVALID_PLAN')
    need(plan.get('repository') == cloud.REPO and
         plan.get('source_main_sha') == cloud.SOURCE_MAIN and
         plan.get('script_sha256') == cloud.SCRIPT_SHA256 and
         plan.get('xml_sha256') == cloud.XML_SHA256 and
         plan.get('zip_sha256') == cloud.ZIP_SHA256 and
         type(plan.get('xml_bytes')) is int and plan['xml_bytes'] == cloud.XML_SIZE and
         type(plan.get('producer_run_id')) is int and
         plan['producer_run_id'] == cloud.PRODUCER_RUN and
         type(plan.get('artifact_id')) is int and
         plan['artifact_id'] == cloud.PRODUCER_ARTIFACT,
         'PINNED_PROVENANCE_MISMATCH')
    need(all(plan.get(k) is False for k in FORBIDDEN_PLAN_FLAGS),
         'UNTRUSTED_PLAN_CANNOT_GRANT_AUTHORITY')
    request = plan.get('request')
    need(type(request) is dict and request.get('method') == 'POST' and
         request.get('api_host') == cloud.API_HOST and
         request.get('content_type') == 'application/json' and
         request.get('credentials_embedded') is False and
         request.get('body_contains_exact_reviewed_script') is True and
         request.get('body_embedded_in_report') is False,
         'INVALID_REQUEST_PLAN')
    try:
        universe = cloud.positive_id(request.get('universe_id'))
        place = cloud.positive_id(request.get('place_id'))
        version = cloud.positive_id(request.get('explicit_version_id'))
    except (cloud.Blocked, ValueError, TypeError):
        raise ResultHold('INVALID_TARGET') from None
    path = (f'/cloud/v2/universes/{universe}/places/{place}/'
            f'versions/{version}/luau-execution-session-tasks')
    need(request.get('path') == path, 'REQUEST_VERSION_SCOPE_MISMATCH')
    # Pin exact bytes of the original reviewed static script, not a claimed
    # digest supplied by the caller. Even a perfect match isn't provider proof.
    script_path = Path(__file__).resolve().with_name(cloud.SCRIPT_NAME)
    try:
        source = cloud.pin_script(script_path)
    except cloud.Blocked:
        raise ResultHold('STATIC_SCRIPT_BYTES_NOT_REVIEWED') from None
    raw = json.dumps({'script': source}, ensure_ascii=False,
                     separators=(',', ':')).encode('utf-8')
    need(request.get('body_sha256') == hashlib.sha256(raw).hexdigest() and
         type(plan.get('script_bytes')) is int and
         plan['script_bytes'] == len(source.encode('utf-8')),
         'REQUEST_BODY_NOT_STATIC_SCRIPT')
    return request


def inspect_untrusted_return(plan: Any, task: Any) -> dict:
    """Strictly match expected *normalized* result table, never provider origin.

    A trusted future host must separately authenticate provider responses, match
    the posted request body to the script pin, and bind task GET/logs to source,
    place version, global intent and original provider task IDs. This function
    intentionally never authorizes those actions.
    """
    request = _validate_plan(plan)
    need(type(task) is dict, 'MALFORMED_TASK')
    universe = request['universe_id']
    place = request['place_id']
    version = request['explicit_version_id']
    task_path = task.get('path')
    prefix = (f'universes/{universe}/places/{place}/versions/{version}/'
              'luau-execution-sessions/')
    pattern = rf'{re.escape(prefix)}{cloud.UUID}/tasks/{cloud.UUID}\Z'
    need(type(task_path) is str and len(task_path) < 300 and
         re.fullmatch(pattern, task_path) is not None,
         'TASK_VERSION_SCOPE_MISMATCH')
    need(type(task.get('state')) is str and task['state'] == 'COMPLETE',
         'TASK_NOT_COMPLETE')
    need(task.get('error') is None, 'TASK_HAS_ERROR')
    output = task.get('output')
    need(type(output) is dict and set(output) == {'results'},
         'OUTPUT_SCHEMA_MISMATCH')
    results = output.get('results')
    need(type(results) is list and len(results) == 1,
         'RESULT_COUNT_MISMATCH')
    row = results[0]
    need(type(row) is dict and set(row) == RETURN_KEYS,
         'RESULT_TABLE_SCHEMA_MISMATCH')
    need(type(row['marker']) is str and row['marker'] == cloud.MARKER and
         type(row['source_main_sha']) is str and
         row['source_main_sha'] == cloud.SOURCE_MAIN and
         type(row['topology']) is str and
         row['topology'] == cloud.EXPECTED_TOPOLOGY,
         'RESULT_IDENTITY_MISMATCH')
    need(type(row['wave_one']) is int and row['wave_one'] == 5 and
         type(row['wave_nine']) is int and row['wave_nine'] == 20,
         'GAME_RULE_ASSERTIONS_MISMATCH')
    need(all(row[k] is False for k in (
        'server_player_session_verified', 'two_client_verified',
        'mobile_verified', 'publish_authorized')),
        'RETURN_OVERCREDIT_REJECTED')
    return {
        'status': 'STATIC_SMOKE_RETURN_CONSISTENT_UNTRUSTED',
        'repository': cloud.REPO,
        'source_main_sha': cloud.SOURCE_MAIN,
        'reviewed_script_sha256': cloud.SCRIPT_SHA256,
        'pinned_xml_sha256': cloud.XML_SHA256,
        'version_id': version,
        'task_path_claim': task_path,
        'all_expected_return_fields_match': True,
        'untrusted_fixture_only': True,
        'github_authenticated': False,
        'roblox_provider_authenticated': False,
        'real_roblox_engine_verified': False,
        'play_mode_verified': False,
        'two_client_verified': False,
        'mobile_verified': False,
        'may_call_roblox': False,
        'may_publish': False,
        'may_merge': False,
        'may_spend': False,
    }


def inspect_untrusted_json(plan: Any, raw_task_json: str) -> dict:
    """Strict JSON parse rejects duplicate keys, NaN/Infinity, oversized data."""
    try:
        task = cloud.parse_json(raw_task_json)
    except cloud.Blocked:
        raise ResultHold('TASK_JSON_MALFORMED_OR_DUPLICATED') from None
    return inspect_untrusted_return(plan, task)