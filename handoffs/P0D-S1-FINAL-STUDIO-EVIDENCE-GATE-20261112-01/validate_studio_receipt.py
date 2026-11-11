#!/usr/bin/env python3
"""Fail-closed local evidence gate for owner-directed TRAP RAIDERS final Roblox Studio QA.

This code verifies receipt shape, immutable source/build pins and *local evidence bytes*.
It cannot authenticate the person who collected logs or independently prove a Roblox
engine actually ran. Never use its PASS as permission to publish a Roblox experience.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

SCHEMA = 'P0D_FINAL_STUDIO_RECEIPT_V1'
GAME = 'TRAP_RAIDERS'
WORK = 'p0d-siege-v19'
RELEASE = 'P0D-S1-KIDS-RC01'
RC_SHA = '5dc6c958ea5549b1e859d6d250e6179e731181fb'
RC_MANIFEST_SHA256 = '81cd35eb89593f6e84ccbc3d9dca1cadda4a06edfee488afc7375eaee6864311'
ROJO_RBXLX_SHA256 = 'f5c0b56cc7d3bbc2d92190dd95cb94f4dfa490f7949f2440655799c5893684a7'
SOURCE_TREE_SHA = '01aede07b64973a32ba02647c10a9e8b8f8c3285'
REQUIRED = (
    'BACKUP_NEWEST_PC_PLACE', 'RC_SOURCE_MANIFEST_IMPORT', 'STUDIO_PLAY_START',
    'TWO_CLIENT_JOIN', 'RED_BLUE_TEAM_ASSIGN', 'MOVE_JUMP_SPAWN',
    'OPPONENT_EGG_PICKUP', 'OWN_EGG_AT_HOME_SCORE_GUARD', 'EGG_DELIVERY_SCORE',
    'CASTLE_SERVER_HP_DAMAGE', 'MELEE_RANGE_LOS_COOLDOWN',
    'REMOTE_SPOOF_AND_SEQ_REPLAY_REJECT', 'DEATH_EGG_DROP', 'DISCONNECT_RECOVERY',
    'VICTORY_DEFEAT_REASON', 'AUTO_REMATCH_STATE_RESET',
    'MOBILE_LANDSCAPE_HUD', 'MOBILE_ATTACK_INTERACTION',
    'FIRST_MINUTE_INSTRUCTIONS', 'DEVICE_FPS_CAPTURE',
    'PLACE_SAVE_REOPEN', 'STUDIO_NORMAL_EXIT', 'NO_LIVE_PUBLISH',
)
BOSS = ('D07_WARNING_BOTH_TEAMS', 'D07_REAL_HUMANOID_DAMAGE_ONCE', 'D07_CLEANUP_NO_LEAK')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
OWNER_DECISION = re.compile(r'^https://github\.com/kk051780/toy-wars-factory/issues/220#issuecomment-[0-9]+$')


def _expect(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def validate(receipt: object, evidence_root: Path) -> dict:
    errors: list[str] = []
    verified_paths: set[str] = set()
    if not isinstance(receipt, dict):
        return {'status':'BLOCKED', 'errors':['RECEIPT_NOT_OBJECT'], 'passed_scenarios':0, 'required_scenarios':len(REQUIRED)+len(BOSS)}
    required_pins = {
        'schema': SCHEMA, 'game_id': GAME, 'work_id': WORK,
        'release_id': RELEASE, 'rc_commit': RC_SHA,
        'rc_manifest_sha256': RC_MANIFEST_SHA256,
        'source_tree_sha': SOURCE_TREE_SHA, 'rbxlx_sha256': ROJO_RBXLX_SHA256,
    }
    for name, value in required_pins.items():
        _expect(receipt.get(name) == value, 'PIN_MISMATCH_'+name.upper(), errors)
    _expect(receipt.get('evidence_kind') == 'ACTUAL_ROBLOX_STUDIO', 'NOT_REAL_STUDIO_EVIDENCE_CLAIM', errors)
    _expect(receipt.get('game_published') is False, 'PUBLISH_MUST_REMAIN_FALSE', errors)
    _expect(receipt.get('owner_release_approved') is False, 'RELEASE_APPROVAL_CANNOT_BE_INFERRED', errors)

    backup = receipt.get('pc_backup')
    if not isinstance(backup, dict):
        errors.append('PC_BACKUP_MISSING')
    else:
        _expect(bool(HEX64.fullmatch(str(backup.get('original_place_sha256','')))), 'PC_PLACE_SHA_MISSING', errors)
        _expect(bool(HEX64.fullmatch(str(backup.get('checkpoint_sha256','')))), 'CHECKPOINT_SHA_MISSING', errors)
        _expect(backup.get('preserved_separately') is True, 'PC_BACKUP_NOT_PRESERVED', errors)
    env = receipt.get('studio_session')
    if not isinstance(env, dict):
        errors.append('STUDIO_SESSION_MISSING')
    else:
        clients = env.get('client_session_ids')
        _expect(isinstance(clients, list) and len(clients)>=2 and all(isinstance(x,str) and x.strip() for x in clients) and len(clients)==len(set(clients)) if isinstance(clients,list) else False, 'TWO_DISTINCT_CLIENT_SESSIONS_REQUIRED', errors)
        _expect(env.get('normal_exit') is True, 'STUDIO_NORMAL_EXIT_UNCONFIRMED', errors)
        _expect(env.get('studio_pid_gone') is True, 'STUDIO_PID_EXIT_UNCONFIRMED', errors)
        _expect(env.get('saved_place_reopened') is True, 'PLACE_REOPEN_UNCONFIRMED', errors)
        fps = env.get('measured_min_fps')
        _expect(type(fps) in (int,float) and fps > 0 and fps <= 500, 'MEASURED_FPS_REQUIRED', errors)
        _expect(isinstance(env.get('mobile_device_or_emulator'),str) and bool(env.get('mobile_device_or_emulator','').strip()), 'MOBILE_TEST_DEVICE_REQUIRED', errors)

    mode = receipt.get('boss_mode')
    if mode not in ('OFF', 'ON'):
        errors.append('BOSS_MODE_REQUIRED')
        mode = 'ON'
    if mode == 'OFF':
        # The current RC has D07/D08 toggles OFF. No silent de-scope: a future
        # explicit OWNER decision must first be reviewed by the human integrator.
        _expect(receipt.get('boss_defer_owner_approved') is True, 'BOSS_DEFER_OWNER_CONSENT_REQUIRED', errors)
        _expect(isinstance(receipt.get('boss_defer_owner_issue_url'),str) and bool(OWNER_DECISION.fullmatch(receipt.get('boss_defer_owner_issue_url',''))), 'BOSS_DEFER_OWNER_DECISION_LINK_REQUIRED', errors)
        # A local receipt cannot authenticate an Issue comment as an actual OWNER
        # instruction. Until #220 verifies and updates the acceptance policy,
        # this required boss is NOT silently omitted from the first release.
        errors.append('BOSS_DISABLED_ENGINE_GATE_UNRESOLVED_HUMAN_REVIEW_REQUIRED')
    else:
        _expect(receipt.get('boss_defer_owner_approved') is False, 'BOSS_ON_CANNOT_CLAIM_DEFER', errors)

    cases = receipt.get('scenarios')
    if not isinstance(cases, list):
        errors.append('SCENARIOS_MISSING')
        cases=[]
    by_id={}
    for n,row in enumerate(cases):
        if not isinstance(row,dict):
            errors.append('SCENARIO_ROW_NOT_OBJECT_'+str(n))
            continue
        sid=row.get('id')
        if not isinstance(sid,str) or not sid:
            errors.append('SCENARIO_ID_INVALID_'+str(n))
            continue
        if sid in by_id:
            errors.append('SCENARIO_DUPLICATE_'+sid)
            continue
        by_id[sid]=row
        if sid not in REQUIRED+BOSS:
            errors.append('UNRECOGNIZED_SCENARIO_'+sid)
    expected=set(REQUIRED) | (set(BOSS) if mode=='ON' else set())
    passed=0
    for sid in sorted(expected):
        row=by_id.get(sid)
        if row is None:
            errors.append('NOT_TESTED_'+sid)
            continue
        status=row.get('status')
        if status != 'PASS':
            errors.append(('FAIL_' if status == 'FAIL' else 'NOT_TESTED_')+sid)
            continue
        evidence=row.get('evidence')
        if not isinstance(evidence,list) or not evidence:
            errors.append('EVIDENCE_MISSING_'+sid)
            continue
        case_ok=True
        for e in evidence:
            if not isinstance(e,dict):
                errors.append('EVIDENCE_ROW_INVALID_'+sid)
                case_ok=False
                continue
            rel=e.get('path')
            if not isinstance(rel,str) or not rel or '\\' in rel:
                errors.append('EVIDENCE_PATH_INVALID_'+sid)
                case_ok=False
                continue
            pos=PurePosixPath(rel)
            if pos.is_absolute() or '..' in pos.parts or '.' in pos.parts or len(pos.parts)<2:
                errors.append('EVIDENCE_PATH_TRAVERSAL_'+sid)
                case_ok=False
                continue
            check_file=evidence_root.joinpath(*pos.parts)
            # Reject not only a symlink file but also a symlink parent folder.
            if any((evidence_root.joinpath(*pos.parts[:i])).is_symlink() for i in range(1,len(pos.parts)+1)) or not check_file.is_file():
                errors.append('EVIDENCE_FILE_MISSING_OR_SYMLINK_'+sid)
                case_ok=False
                continue
            actual=check_file.read_bytes()
            if not actual or type(e.get('size')) is not int or len(actual)!=e.get('size') or not isinstance(e.get('sha256'),str) or not HEX64.fullmatch(e.get('sha256')) or hashlib.sha256(actual).hexdigest()!=e.get('sha256'):
                errors.append('EVIDENCE_HASH_OR_SIZE_MISMATCH_'+sid)
                case_ok=False
                continue
            verified_paths.add(rel)
        if case_ok:
            passed+=1
    if mode=='OFF':
        for sid in BOSS:
            row=by_id.get(sid)
            if row and row.get('status')=='PASS':
                errors.append('BOSS_OFF_CANNOT_HAVE_PASS_'+sid)
    return {
        'schema': 'P0D_FINAL_STUDIO_EVIDENCE_GATE_RESULT_V1',
        'status': 'STUDIO_EVIDENCE_GATE_PASS' if not errors else 'BLOCKED',
        'passed_scenarios': passed,
        'required_scenarios': len(expected),
        'verified_evidence_files': len(verified_paths),
        'errors': errors,
        'rc_commit': RC_SHA,
        'scope': 'offline_receipt_and_local_hash_validation_ONLY__NOT_AN_ENGINE_ATTESTATION',
        'roblox_publishing_permitted': False,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt',type=Path)
    parser.add_argument('--evidence-root',type=Path,required=True)
    args=parser.parse_args()
    try:
        receipt=json.loads(args.receipt.read_text(encoding='utf-8'))
        result=validate(receipt,args.evidence_root)
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        result={'status':'BLOCKED','errors':['CANNOT_READ_RECEIPT: '+type(exc).__name__]}
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if result['status']=='STUDIO_EVIDENCE_GATE_PASS' else 2


if __name__=='__main__':
    sys.exit(main())
