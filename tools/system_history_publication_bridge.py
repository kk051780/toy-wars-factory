"""Advisory-only C-history publication reconciliation contract.

Use only after a future authenticated host has fetched the COMPLETE main/open-PR
snapshot and original Git objects. Inputs here are caller supplied and can be
fabricated; this module DOES NOT authenticate GitHub, reserve IDs, or grant writes.
It never modifies state or sends network requests. It is a candidate for PR157.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import re
import uuid

_SHA = re.compile(r'[0-9a-f]{40}\Z')
_CID = re.compile(r'C[0-9]{5}\Z')
_PATH = re.compile(r'history/(C[0-9]{5})_[A-Za-z0-9_-]{1,120}\.json\Z')
_WORK = re.compile(r'[A-Za-z0-9_-]{8,100}\Z')
_BRANCH = re.compile(r'(?:auto/twf-game-repair-[0-9a-f-]+|auto/twf-system-review-[0-9a-f-]+|controller/[A-Za-z0-9_/-]+)\Z')
_MAX = 10000


def _uuid(value):
    if type(value) is not str:
        return False
    try:
        return str(uuid.UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


def reconcile_publications(coordinator, occupied_ids, claims):
    base = {'schema': 1, 'authority': 'UNTRUSTED_ADVISORY', 'may_claim': False,
            'may_write': False, 'may_merge': False, 'may_retry': False,
            'cas_performed': False, 'github_authenticated': False,
            'provider_attested': False}
    def decide(code, **fields):
        return dict(base, status=code, **fields)
    if (type(coordinator) is not dict or type(coordinator.get('schema')) is not int
            or coordinator['schema'] != 1 or type(coordinator.get('epoch')) is not int
            or coordinator['epoch'] < 0):
        return decide('BLOCK_BAD_COORDINATOR')
    ledger = coordinator.get('history_id_reservations')
    if ledger is None:
        return decide('WAIT_VERIFIED_BOOTSTRAP')
    if (type(ledger) is not dict or set(ledger) != {'schema','high_watermark','entries'}
            or type(ledger['schema']) is not int or ledger['schema'] != 1
            or type(ledger['high_watermark']) is not int
            or not 1 <= ledger['high_watermark'] <= 99999
            or type(ledger['entries']) is not list or len(ledger['entries']) > _MAX):
        return decide('BLOCK_INVALID_LEDGER')
    reserve = {}
    for record in ledger['entries']:
        if (type(record) is not dict or set(record) != {'id','owner_id','epoch','work_branch','work_id','main_sha'}
                or type(record['id']) is not str or not _CID.fullmatch(record['id'])
                or record['id'] == 'C00000'
                or not _uuid(record['owner_id'])
                or type(record['epoch']) is not int or not 1 <= record['epoch'] <= coordinator['epoch']
                or type(record['work_branch']) is not str or not _BRANCH.fullmatch(record['work_branch'])
                or type(record['work_id']) is not str or not _WORK.fullmatch(record['work_id'])
                or type(record['main_sha']) is not str or not _SHA.fullmatch(record['main_sha'])
                or int(record['id'][1:]) > ledger['high_watermark']):
            return decide('BLOCK_INVALID_LEDGER')
        if record['id'] in reserve:
            return decide('BLOCK_DUPLICATE_LEDGER')
        reserve[record['id']] = record
    if (type(occupied_ids) is not list or len(occupied_ids) > _MAX
            or any(type(x) is not str or not _CID.fullmatch(x) or x == 'C00000' for x in occupied_ids)):
        return decide('BLOCK_BAD_OCCUPIED_IDS')
    if type(claims) is not list or len(claims) > _MAX:
        return decide('BLOCK_BAD_SNAPSHOT')
    original = Counter(occupied_ids)
    seen = Counter()
    valid_consumed = []
    for claim in claims:
        if (type(claim) is not dict
                or set(claim) != {'id','path','source_branch','source_main_sha','blob_sha','body'}
                or type(claim['id']) is not str or not _CID.fullmatch(claim['id'])
                or type(claim['path']) is not str
                or type(claim['body']) is not str
                or type(claim['source_branch']) is not str or not _BRANCH.fullmatch(claim['source_branch'])
                or type(claim['source_main_sha']) is not str or not _SHA.fullmatch(claim['source_main_sha'])
                or type(claim['blob_sha']) is not str or not _SHA.fullmatch(claim['blob_sha'])):
            return decide('BLOCK_BAD_SNAPSHOT')
        cid = claim['id']
        seen[cid] += 1
        if cid not in original or seen[cid] > original[cid]:
            return decide('BLOCK_INCOMPLETE_CLAIM_SNAPSHOT')
        if cid in reserve and (seen[cid] > 1 or original[cid] > 1):
            return decide('BLOCK_RESERVED_ID_DUPLICATED')
        try:
            raw = claim['body'].encode('utf-8', 'strict')
            if len(raw) > 262144:
                return decide('BLOCK_BAD_SNAPSHOT')
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        except UnicodeError:
            return decide('BLOCK_BAD_SNAPSHOT')
        if claim['blob_sha'] != blob:
            return decide('BLOCK_BLOB_MISMATCH')
        name = _PATH.fullmatch(claim['path'])
        if name is None or name.group(1) != cid:
            return decide('BLOCK_PATH_OR_ID_MISMATCH')
        def reject_dup(pairs):
            out = {}
            for k, v in pairs:
                if k in out:
                    raise ValueError('duplicate json key')
                out[k] = v
            return out
        try:
            body = json.loads(claim['body'], object_pairs_hook=reject_dup,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        except (ValueError, RecursionError):
            return decide('BLOCK_INVALID_HISTORY_BODY')
        if type(body) is not dict or body.get('id') != cid:
            return decide('BLOCK_PATH_OR_ID_MISMATCH')
        if cid in reserve:
            r = reserve[cid]
            coord = body.get('coordination')
            if (type(coord) is not dict or coord.get('branch') != 'twf-repair-coordinator'
                    or coord.get('owner_run_id') != r['owner_id']
                    or type(body.get('work_id')) is not str
                    or body['work_id'] != r['work_id']
                    or type(coord.get('epoch')) is not int or coord['epoch'] != r['epoch']
                    or type(coord.get('claim_commit')) is not str or not _SHA.fullmatch(coord['claim_commit'])
                    or claim['source_branch'] != r['work_branch']
                    or claim['source_main_sha'] != r['main_sha']
                    or (body.get('base_main_sha') != r['main_sha']
                        and body.get('main_base') != r['main_sha'])):
                return decide('BLOCK_PROVENANCE_MISMATCH')
            valid_consumed.append(cid)
    for cid in reserve:
        if original[cid] != seen[cid]:
            return decide('BLOCK_INCOMPLETE_CLAIM_SNAPSHOT')
    # A caller can fake a complete external snapshot; NEVER grant permissions.
    remaining = [cid for cid in occupied_ids if cid not in reserve]
    return decide('MATCHED_CONSUMPTION_CANDIDATE_ONLY' if valid_consumed else
                  'NO_CONSUMED_RESERVATIONS_CANDIDATE_ONLY',
                  matched_ids=sorted(valid_consumed),
                  still_reserved_ids=sorted(cid for cid in reserve if cid not in valid_consumed),
                  remaining_occupied_ids=remaining,
                  trust_requirements=['authenticated complete main and all open PR source inventory',
                                      'original Git blob verification',
                                      'original provider actor and lease verification',
                                      'independent protected source and policy review',
                                      'single-parent expected-SHA coordinator CAS with exact postwrite readback'])
