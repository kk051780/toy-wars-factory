"""No-network consistency adapter for official-looking Roblox GET task + logs payloads.

This parser is NOT provider authentication. A trusted host must independently bind
an original create ACK, authenticated HTTPS, immutable private Saved version,
scoped key, original POST digest, global CAS intent and task ownership.
Never infer engine PASS from JSON fixtures. No network, credentials or writes.
"""
import re
from pathlib import Path
import open_cloud_engine_preflight as cloud
import twf_static_smoke_return_gate as gate

class ReceiptHold(ValueError):
    """Fail-closed reason without exposing private provider output."""

def must(ok, reason):
    if not ok:
        raise ReceiptHold(reason)

def _safe_decode(payload):
    try:
        return cloud.parse_json(payload)
    except cloud.Blocked:
        raise ReceiptHold('UNTRUSTED_JSON_INVALID') from None

def inspect_untrusted_get_and_logs(plan, raw_task_json, raw_logs_json):
    """Validate RAW provider-*shaped* GET task and logs, WITHOUT provider origin proof.

    Response only reports counts and booleans; never exposes raw log messages.
    """
    task = _safe_decode(raw_task_json)
    try:
        checked = gate.inspect_untrusted_return(plan, task)
    except gate.ResultHold:
        raise ReceiptHold('STATIC_RETURN_REJECTED') from None
    try:
        expected_script = cloud.pin_script(
            Path(__file__).resolve().with_name(cloud.SCRIPT_NAME))
    except cloud.Blocked:
        raise ReceiptHold('SCRIPT_NOT_REVIEWED') from None
    must(type(task.get('script')) is str and task['script'] == expected_script,
         'TASK_SCRIPT_ECHO_MISMATCH')
    must(type(task.get('timeout')) is str and task['timeout'] == cloud.TASK_TIMEOUT,
         'TASK_TIMEOUT_ECHO_MISMATCH')
    logs = _safe_decode(raw_logs_json)
    must(type(logs) is dict and
         set(logs) == {'luauExecutionSessionTaskLogs', 'nextPageToken'},
         'LOG_RESPONSE_SCHEMA_MISMATCH')
    must(type(logs['nextPageToken']) is str and logs['nextPageToken'] == '',
         'LOGS_PAGINATION_NOT_COMPLETE')
    records=logs['luauExecutionSessionTaskLogs']
    must(type(records) is list and len(records)<=16,'LOG_RECORDS_INVALID')
    prefix=checked['task_path_claim']+'/logs/'
    total=0
    for i,record in enumerate(records,1):
        must(type(record) is dict and set(record) in (
             {'path','messages'}, {'path','messages','structuredMessages'}),
             'LOG_RECORD_SCHEMA_MISMATCH')
        must(type(record['path']) is str and record['path'] == prefix+str(i),
             'LOG_TASK_SCOPE_MISMATCH')
        messages=record['messages']
        must(type(messages) is list and len(messages)<=100,
             'LOG_MESSAGES_INVALID')
        must(all(type(m) is str and len(m)<=2048 for m in messages),
             'LOG_MESSAGE_UNBOUNDED')
        total+=len(messages)
        if 'structuredMessages' in record:
            rows=record['structuredMessages']
            must(type(rows) is list and len(rows)<=100,'STRUCTURED_LOG_INVALID')
            for row in rows:
                must(type(row) is dict and set(row)=={'message','createTime','messageType'} and
                     type(row['message']) is str and len(row['message'])<=2048 and
                     type(row['createTime']) is str and 15<=len(row['createTime'])<=40 and
                     re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+Z',row['createTime']) is not None and
                     type(row['messageType']) is str and 1<=len(row['messageType'])<=32,
                     'STRUCTURED_LOG_INVALID')
    return {
        'status':'UNTRUSTED_OPEN_CLOUD_GET_LOGS_CONSISTENT',
        'task_path_claim':checked['task_path_claim'],
        'source_main_sha':checked['source_main_sha'],
        'reviewed_script_sha256':checked['reviewed_script_sha256'],
        'version_id':checked['version_id'],
        'log_record_count':len(records),
        'flat_message_count':total,
        'log_content_returned':False,
        'raw_provider_payload_stored':False,
        'origin_authenticated':False,
        'provider_authenticated':False,
        'create_ack_bound':False,
        'original_post_body_authenticated':False,
        'private_saved_version_authenticated':False,
        'engine_verified':False,'play_mode_verified':False,'mobile_verified':False,
        'may_post':False,'may_publish':False,'may_merge':False,'may_spend':False,
    }
