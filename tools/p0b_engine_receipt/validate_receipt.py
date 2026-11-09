#!/usr/bin/env python3
"""P0-B R7: offline cross-artifact integrity validation, NOT host or engine attestation.

No network, Studio, Codex, credential, GitHub or OS execution actions.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = 'kk051780/toy-wars-factory'
HEAD = 'bd78ae0a3bef6a35d5be5726fdb3a93fc9a46e90'
# Git blob IDs read from tools/export_accepted_rbxlx.py at exact PR #209 HEAD.
SOURCE_BLOBS = {
    'ToyWarsBalance': ('ModuleScript', '64175b1cda7e4d5e4623d7b28bb80fdc3d64c3b8'),
    'ToyWarsServer': ('Script', '181b0ef3a5aedafef4490decdbbe167d769e9932'),
    'ToyWarsSmokeTest': ('Script', 'ccba431909c664909e2680785648d0402fedf3c3'),
    'ToyWarsHUD': ('LocalScript', 'ffd2c9db01f70605e87f25cee3b2c50372202fb8'),
}
EXPECTED_ITEMS = {
    'Workspace': 'Workspace', 'ReplicatedStorage': 'ReplicatedStorage',
    'ToyWarsBalance': 'ModuleScript', 'ToyWarsSelectUnit': 'RemoteEvent',
    'ServerScriptService': 'ServerScriptService', 'ToyWarsServer': 'Script',
    'ToyWarsSmokeTest': 'Script', 'StarterPlayer': 'StarterPlayer',
    'StarterPlayerScripts': 'StarterPlayerScripts', 'ToyWarsHUD': 'LocalScript',
}
MAX_INPUT = {'console': 2_000_000, 'screenshot': 12_000_000,
             'place_xml': 10_000_000, 'mcp_trace': 200_000}
SHA256 = re.compile(r'^[0-9a-f]{64}$')
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
SMOKE = 'TWF_QA_SUMMARY v1.2 pass=9 fail=0'
PNG = b'\x89PNG\r\n\x1a\n'


def _gitblob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def _utc(s):
    if not isinstance(s, str):
        return None
    try:
        v = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    except ValueError:
        return None
    if v.utcoffset() is None:
        return None
    return v.astimezone(dt.timezone.utc)


def verify_xml_bytes(raw: bytes) -> list[str]:
    """Verify byte-exact four-source contents and 10-item layout, not Studio execution."""
    errors = []
    if not isinstance(raw, bytes) or not (0 < len(raw) <= MAX_INPUT['place_xml']):
        return ['xml_size_or_type_invalid']
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        return ['xml_dtd_forbidden']
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return ['xml_parse_failed']
    if root.tag != 'roblox' or root.get('version') != '4':
        errors.append('xml_root_invalid')
    items = root.findall('.//Item')
    if len(items) != 10:
        errors.append('xml_item_count_invalid')
    names = {}
    refs = []
    for item in items:
        n = item.find('./Properties/string[@name="Name"]')
        name = n.text if n is not None else None
        if not name or name in names:
            errors.append('xml_duplicate_or_missing_name')
            continue
        names[name] = item
        if item.get('class') != EXPECTED_ITEMS.get(name):
            errors.append('xml_unexpected_class_' + name[:45])
        refs.append(item.get('referent'))
    if set(names) != set(EXPECTED_ITEMS):
        errors.append('xml_expected_items_missing_or_extra')
    if None in refs or len(set(refs)) != len(items):
        errors.append('xml_referents_invalid')
    for name, (klass, blob) in SOURCE_BLOBS.items():
        item = names.get(name)
        if item is None:
            errors.append('source_missing_' + name)
            continue
        source = item.find('./Properties/ProtectedString[@name="Source"]')
        if item.get('class') != klass or source is None or not source.text:
            errors.append('source_class_or_content_missing_' + name)
            continue
        if _gitblob(source.text.encode('utf-8')) != blob:
            errors.append('source_git_blob_mismatch_' + name)
    # R8.1: whitelist the entire XML object graph, not just the script blobs.
    # A hidden Disabled/LinkedSource/RunContext property must never be accepted
    # as an equivalent source-pinned candidate for isolated Studio testing.
    expected_parent = {
        'Workspace': None, 'ReplicatedStorage': None,
        'ServerScriptService': None, 'StarterPlayer': None,
        'ToyWarsBalance': 'ReplicatedStorage',
        'ToyWarsSelectUnit': 'ReplicatedStorage',
        'ToyWarsServer': 'ServerScriptService',
        'ToyWarsSmokeTest': 'ServerScriptService',
        'StarterPlayerScripts': 'StarterPlayer',
        'ToyWarsHUD': 'StarterPlayerScripts',
    }
    if set(root.attrib) != {'version'} or any(child.tag != 'Item' for child in root):
        errors.append('xml_root_extra_field_or_element')
    parent_of = {child: parent for parent in root.iter()
                 for child in parent if child.tag == 'Item'}
    for name, item in names.items():
        parent = parent_of.get(item)
        actual_parent = None
        if parent is not root:
            if parent is None or parent.tag != 'Item':
                errors.append('xml_parent_location_invalid')
            else:
                pn = parent.find('./Properties/string[@name="Name"]')
                actual_parent = pn.text if pn is not None else None
        if actual_parent != expected_parent.get(name):
            errors.append('xml_parent_location_invalid')
        if set(item.attrib) != {'class', 'referent'} or not re.fullmatch(
                r'RBX[0-9A-F]{32}', item.get('referent', '')):
            errors.append('xml_item_attributes_invalid')
        direct = list(item)
        ps = [child for child in direct if child.tag == 'Properties']
        if len(ps) != 1 or any(child.tag not in ('Properties', 'Item') for child in direct):
            errors.append('xml_unexpected_item_child')
            continue
        if ps[0].attrib:
            errors.append('xml_unexpected_property')
        expected_fields = {('string', 'Name')}
        if name in SOURCE_BLOBS:
            expected_fields.add(('ProtectedString', 'Source'))
        actual_fields = set()
        for field in ps[0]:
            if set(field.attrib) != {'name'}:
                errors.append('xml_unexpected_property')
            actual_fields.add((field.tag, field.get('name')))
        if actual_fields != expected_fields or len(ps[0]) != len(expected_fields):
            errors.append('xml_unexpected_property')
    return list(dict.fromkeys(errors))


def verify_png_bytes(raw: bytes) -> bool:
    """PNG chunk structure and CRC, not image content/GUI proof."""
    if not raw.startswith(PNG) or len(raw) > MAX_INPUT['screenshot']:
        return False
    offset, first, idat, end = 8, True, False, False
    while offset + 12 <= len(raw):
        n = int.from_bytes(raw[offset:offset+4], 'big')
        typ = raw[offset+4:offset+8]
        if n > len(raw) - offset - 12:
            return False
        data = raw[offset+8:offset+8+n]
        checksum = int.from_bytes(raw[offset+8+n:offset+12+n], 'big')
        if (zlib.crc32(typ + data) & 0xffffffff) != checksum:
            return False
        if first:
            if typ != b'IHDR' or n != 13:
                return False
            w, h = struct.unpack('>II', data[:8])
            if not (1 <= w <= 8192 and 1 <= h <= 8192):
                return False
            first = False
        if typ == b'IDAT' and n > 0:
            idat = True
        offset += n + 12
        if typ == b'IEND':
            end = n == 0
            break
    return end and idat and offset == len(raw)


def verify_trace(raw: bytes, sid: str, doc: dict) -> list[str]:
    try:
        trace = json.loads(raw.decode('utf-8', errors='strict'))
    except (UnicodeDecodeError, ValueError):
        return ['mcp_trace_unreadable']
    events = trace.get('events') if isinstance(trace, dict) else None
    if not isinstance(events, list) or len(events) != 5:
        return ['mcp_trace_event_count_invalid']
    expected = [('state','Edit','Roblox_Studio.get_studio_state'),
                ('play',None,'Roblox_Studio.start_stop_play'),
                ('state','Play','Roblox_Studio.get_studio_state'),
                ('stop',None,'Roblox_Studio.start_stop_play'),
                ('state','Edit','Roblox_Studio.get_studio_state')]
    failures = []
    timestamps = []
    for i, (event, kind) in enumerate(zip(events, expected)):
        action, mode, tool = kind
        if not isinstance(event, dict) or event.get('action') != action or event.get('tool') != tool or event.get('studio_id') != sid:
            failures.append('mcp_trace_identity_or_tool_mismatch')
            continue
        if mode is not None and event.get('mode') != mode:
            failures.append('mcp_trace_mode_mismatch')
        if action in ('play','stop') and event.get('success') is not True:
            failures.append('mcp_trace_play_stop_failed')
        timestamps.append(_utc(event.get('at_utc')))
    if len(timestamps) != 5 or any(t is None for t in timestamps) or timestamps != sorted(timestamps):
        failures.append('mcp_trace_bad_timeline')
    else:
        m = doc.get('mcp', {})
        if [_utc(m.get(k)) for k in ('time_before_utc','time_play_utc','time_after_utc')] != [timestamps[0],timestamps[2],timestamps[4]]:
            failures.append('mcp_receipt_timestamp_mismatch')
    return list(dict.fromkeys(failures))


def check(doc, artifacts: dict[str, bytes], expected_head=HEAD):
    """Validate only internal consistency against supplied bytes; never attest origin."""
    failures = []
    def need(ok, reason):
        if not ok:
            failures.append(reason)
    if not isinstance(doc, dict):
        return _result(['document_not_object'])
    need(doc.get('schema') == 'p0b-engine-receipt/v2', 'unknown_schema')
    need(doc.get('repo') == REPO and type(doc.get('pr')) is int and doc.get('pr') == 209, 'wrong_source')
    need(expected_head == HEAD and doc.get('head_sha') == HEAD, 'head_mismatch')
    w = doc.get('work_id')
    need(isinstance(w,str) and bool(re.fullmatch(r'P0B_[A-Z0-9_]{8,100}', w)), 'invalid_work_id')
    need(doc.get('fixture_only') is False, 'fixture_only_or_unknown')
    p = doc.get('place') if isinstance(doc.get('place'),dict) else {}
    for k in ('place_id','game_id'):
        need(type(p.get(k)) is int and p[k] == 0, 'nonlocal_or_unknown_'+k)
    need(p.get('is_original') is False and p.get('is_published') is False and p.get('local_backup_verified') is True, 'isolation_not_declared')
    fname = p.get('local_filename')
    need(isinstance(fname,str) and fname.endswith('.rbxlx') and 'PR209' in fname and '/' not in fname and '\\' not in fname, 'place_filename_invalid')
    m = doc.get('mcp') if isinstance(doc.get('mcp'),dict) else {}
    sid = m.get('studio_id')
    need(type(m.get('studio_count')) is int and m['studio_count'] == 1, 'ambiguous_studios')
    need(isinstance(sid,str) and UUID.fullmatch(sid) is not None, 'studio_uuid_invalid')
    need(bool(sid) and sid == m.get('studio_id_before') == m.get('studio_id_after'), 'studio_id_changed')
    need(m.get('mode_before') == 'Edit' and m.get('mode_play') == 'Play' and m.get('mode_after') == 'Edit', 'mode_sequence_missing')
    need(m.get('play_success') is True and m.get('stop_success') is True, 'play_stop_not_confirmed')
    q = doc.get('qa') if isinstance(doc.get('qa'),dict) else {}
    need(q.get('summary_line') == SMOKE, 'smoke_summary_mismatch')
    need(q.get('unsaved_warning_visible') is True and q.get('curebo_page2_visible') is True, 'ui_claim_missing')
    need(type(q.get('wave_observed')) is int and q.get('wave_observed') >= 1, 'wave_claim_invalid')
    e = doc.get('effects') if isinstance(doc.get('effects'),dict) else {}
    for k in ('git_source_writes','studio_saves','roblox_publishes','api_service_setting_changes'):
        need(type(e.get(k)) is int and e.get(k) == 0, 'unexpected_effect_'+k)
    need(e.get('datastore_observation') == 'NOT_MEASURED', 'datastore_zero_not_attested')

    ev = doc.get('evidence') if isinstance(doc.get('evidence'),dict) else {}
    for name in MAX_INPUT:
        blob = artifacts.get(name) if isinstance(artifacts,dict) else None
        need(isinstance(blob,bytes) and 0 < len(blob) <= MAX_INPUT[name], 'missing_or_oversize_artifact_'+name)
        recorded = ev.get(name+'_sha256')
        need(isinstance(recorded,str) and SHA256.fullmatch(recorded) is not None, 'invalid_digest_'+name)
        if isinstance(blob,bytes) and 0 < len(blob) <= MAX_INPUT[name] and isinstance(recorded,str):
            need(hashlib.sha256(blob).hexdigest() == recorded, 'actual_bytes_hash_mismatch_'+name)
    if isinstance(artifacts,dict):
        xml = artifacts.get('place_xml')
        if isinstance(xml,bytes):
            failures.extend(verify_xml_bytes(xml))
        screenshot = artifacts.get('screenshot')
        if isinstance(screenshot,bytes):
            need(verify_png_bytes(screenshot), 'png_bytes_invalid')
        console = artifacts.get('console')
        if isinstance(console,bytes):
            try:
                log = console.decode('utf-8',errors='strict')
                need(any(line.strip().endswith(SMOKE) for line in log.splitlines()), 'smoke_missing_in_actual_console')
            except UnicodeDecodeError:
                failures.append('console_utf8_invalid')
        trace = artifacts.get('mcp_trace')
        if isinstance(trace,bytes):
            failures.extend(verify_trace(trace,sid,doc))
    return _result(failures)


def _result(failures):
    return {'status':'REJECTED' if failures else 'ARTIFACT_BYTES_MATCH_UNATTESTED',
            'failures':list(dict.fromkeys(failures)), 'host_attested':False,
            'owner_authorized':False, 'engine_verified':False,
            'datastore_write_zero_verified':False,
            'may_execute_commands':False,'may_merge_or_publish':False,
            'interpretation':'Offline byte/schema/source-pin checks only, not trusted MCP origin or real Play evidence.'}


def _read_limited(path: Path, cap: int):
    with path.open('rb') as f:
        raw = f.read(cap + 1)
    if not raw or len(raw) > cap:
        raise ValueError('missing_or_oversize_file')
    return raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('receipt_json',type=Path)
    for name in MAX_INPUT:
        parser.add_argument('--'+name.replace('_','-'), type=Path, required=True)
    parser.add_argument('--expected-head',default=HEAD)
    args = parser.parse_args()
    try:
        doc = json.loads(_read_limited(args.receipt_json, 100_000).decode('utf-8',errors='strict'))
        blobs = {name: _read_limited(getattr(args,name),cap) for name,cap in MAX_INPUT.items()}
        if isinstance(doc,dict) and isinstance(doc.get('place'),dict):
            if args.place_xml.name != doc['place'].get('local_filename'):
                result = _result(['place_filename_does_not_match_actual_file'])
            else:
                result = check(doc,blobs,args.expected_head)
        else:
            result = check(doc,blobs,args.expected_head)
    except (OSError,UnicodeError,ValueError,TypeError) as ex:
        result = _result(['files_unreadable_or_invalid'])
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status'] == 'ARTIFACT_BYTES_MATCH_UNATTESTED' else 1

if __name__=='__main__':
    sys.exit(main())
