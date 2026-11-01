"""Compose GET-only transport with existing PR175 no-network typed contract.

No POST, no token logging, no retries, no authorization or engine proof.
A caller's create ACK, plan and responses are not provider-authenticated by this.
"""
from __future__ import annotations
import json
from twf_roblox_get_only_probe import probe_existing_task, ProbeHold


def get_existing_task_checked(target, api_key, plan, raw_create_ack, *, opener=None):
    """Use EXACT existing PR175 contract adapter after at most two GETs.

    Future approved host must independently authenticate original POST ACK and
    prove approved nonpublic place, version, key scope and global intent CAS.
    """
    if type(plan) is not dict or type(raw_create_ack) is not str:
        raise ProbeHold('BRIDGE_INPUT_INVALID')
    # Import is runtime-only so the standalone candidate can still be tested
    # with its original 26 regressions before PR175 source integration.
    try:
        import twf_open_cloud_get_log_adapter as gate
    except ImportError:
        raise ProbeHold('REVIEWED_CONTRACT_NOT_INSTALLED') from None

    def check(task, logs, task_path):
        try:
            original = json.dumps(task, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            log_json = json.dumps(logs, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            result = gate.inspect_untrusted_create_get_and_logs(
                plan, raw_create_ack, original, log_json)
            if type(result) is not dict or result.get('task_path_claim') != task_path:
                raise ProbeHold('LOCAL_CONTRACT_REJECTED')
            return result
        except Exception:
            # Never expose raw logs, original ACK content or API-key-adjacent errors.
            raise ProbeHold('LOCAL_CONTRACT_REJECTED') from None

    return probe_existing_task(target, api_key, opener=opener, contract_checker=check)
