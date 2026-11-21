#!/usr/bin/env python3
"""Independent post-upload artifact verifier for GQ470 Landing A candidate.

Read the actual downloaded GitHub archive, not a pre-upload source tree.
Verifies complete Place SHA/class/69 source preservation and rejects true tamper.
Does not imply official RC adoption, Roblox Studio runtime, FPS or ART_GO.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from recover_real69_from_place import source_from_place
from compose_landing70 import SOURCE_ROUTE, check_art_source

SHA69 = '443914a672f4f535fe4c6313b0dec524892a0afeb4684a8d935e4eebb1458305'
NAME70 = 'gq470-landing-real70/on70/GQ470_LANDING_REAL70_SOURCE_ONLY.rbxlx'
NAME69 = 'gq470-landing-real70/off69/GQ470_LANDING_OFF69_EXACT_SOURCE.rbxlx'
NAME_PROOF = 'gq470-art17/on/GQ470_REHYDRATED_ART17_SOURCE_PROOF.json'
NAME_QA = 'gq470-landing-real70/GQ470_LANDING_REAL70_ART17_QA.json'
NAME_RECEIPT = 'gq470-landing-real70/receipt.json'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def demand(value: bool, message: str) -> None:
    if not value:
        raise ValueError('GQ470_POSTUPLOAD_RED_' + message)


def validate(root: Path, *, ondata: bytes | None = None, offdata: bytes | None = None,
             proof: dict | None = None, qa: dict | None = None,
             source: bytes | None = None) -> dict:
    ondata = ondata if ondata is not None else (root / NAME70).read_bytes()
    offdata = offdata if offdata is not None else (root / NAME69).read_bytes()
    proof = proof if proof is not None else json.loads((root / NAME_PROOF).read_text())
    qa = qa if qa is not None else json.loads((root / NAME_QA).read_text())
    source = source if source is not None else Path(__file__).with_name('EGGRUMBLE_LandingShadow.client.luau').read_bytes()
    # Pin the author ART17 baseline, but NOT the output hash of a previously
    # authored (different) landing script. Verify this exact newly-built output
    # against its source/receipt AND independently re-extracted Place sources.
    receipt = json.loads((root / NAME_RECEIPT).read_text())
    onsha = sha(ondata)
    demand(len(ondata) > len(offdata) and
           onsha == qa.get('profile', {}).get('on70', {}).get('place_sha256') and
           len(ondata) == qa.get('profile', {}).get('on70', {}).get('place_bytes'),
           'ON70_PLACE_BYTES_OR_HASH')
    demand(len(offdata) == 822713 and sha(offdata) == SHA69, 'OFF69_PLACE_BYTES_OR_HASH')
    demand(len(source) > 0 and sha(source) == receipt.get('new_luau_sha256'),
           'NEW_SOURCE_HASH')
    demand(receipt.get('source_route') == SOURCE_ROUTE and
           receipt.get('source_count_on') == 70 and
           receipt.get('source_count_off') == 69 and
           receipt.get('original_scripts_unchanged_sha256') == 69 and
           receipt.get('official_rc_adopted') is False,
           'RECEIPT_SOURCE_TRUTH')
    check_art_source(source.decode('utf-8'))
    full70 = source_from_place(ondata, 70)
    full69 = source_from_place(offdata, 69)
    demand(set(full70) - set(full69) == {SOURCE_ROUTE}, 'SOURCE_ROUTE_DELTA')
    demand(set(full69).issubset(full70), 'ORIGINAL_ROUTE_LOST')
    demand(all(full70[k] == value for k, value in full69.items()), 'ORIGINAL_SOURCE_OR_CLASS_MUTATION')
    demand(full70[SOURCE_ROUTE] == ('LocalScript', source), 'ADDED_SCRIPT_NOT_EXACT')
    demand(proof.get('place_sha256') == SHA69 and proof.get('source_count') == 69,
           'PARENT_PROOF_IDENTITY')
    demand(proof.get('author_selected17_byte_exact') == 17, 'AUTHOR17_PROOF_MISSING')
    ledger = proof.get('source_digest_by_route')
    demand(isinstance(ledger, dict) and len(ledger) == 69, 'BASELINE_SOURCE_LEDGER')
    demand(all(ledger.get(k) == sha(pair[1]) for k, pair in full69.items()), 'BASELINE_ROUTE_HASH')
    counts = qa.get('profile', {})
    demand(qa.get('formal') is False and qa.get('art_go') is False, 'FALSE_GO_ATTESTATION')
    demand(qa.get('studio') == 'NOT_TESTED' and qa.get('android') == 'NOT_TESTED', 'FALSE_ENGINE_ATTESTATION')
    demand(counts.get('on70', {}).get('place_sha256') == onsha and
           counts.get('off69', {}).get('place_sha256') == SHA69, 'RECEIPT_PLACE_SHA')
    demand(counts['on70'].get('source_and_class_exact') == 70 and
           counts['off69'].get('source_and_class_exact') == 69, 'RECEIPT_CLASS_SOURCE_COUNT')
    return {
        'schema':'GQ470_LANDING_REAL70_POSTUPLOAD_INDEPENDENT_QA',
        'source_only':True, 'not_formal_rc':True, 'art_go':False,
        'source70':len(full70), 'original69_unmodified':len(full69),
        'author17_proof_validated':17,
        'on70_sha256':onsha, 'on70_bytes':len(ondata),
        'off69_sha256':SHA69, 'off69_bytes':len(offdata),
        'artifact_source_and_class_exact':True, 'new_authoritative_scripts':0,
        'studio':'NOT_TESTED','android':'NOT_TESTED','human_art':'NO_GO',
    }


def mutated_inputs_fail_closed(root: Path) -> int:
    base70 = (root / NAME70).read_bytes()
    base69 = (root / NAME69).read_bytes()
    p = json.loads((root / NAME_PROOF).read_text())
    q = json.loads((root / NAME_QA).read_text())
    good = Path(__file__).with_name('EGGRUMBLE_LandingShadow.client.luau').read_bytes()
    assert validate(root)
    variants = [
        {'ondata':base70 + b'\n'},
        {'offdata':base69 + b'\n'},
        {'source':good.replace(b'MAX_VISUAL_PARTS = 3',b'MAX_VISUAL_PARTS = 9')},
        {'source':good + b'\nrem:FireServer(9)\n'},
        {'proof':{**p,'author_selected17_byte_exact':16}},
        {'proof':{**p,'place_sha256':'0'*64}},
        {'proof':{**p,'source_digest_by_route':{}}},
        {'qa':{**q,'formal':True}},
        {'qa':{**q,'art_go':True}},
        {'qa':{**q,'studio':'PASS'}},
        {'qa':{**q,'profile':{**q['profile'],'on70':{**q['profile']['on70'],'source_and_class_exact':69}}}},
        {'qa':{**q,'profile':{**q['profile'],'off69':{**q['profile']['off69'],'place_sha256':'f'*64}}}},
    ]
    for n, kw in enumerate(variants, 1):
        try:
            validate(root, **kw)
        except (ValueError, AssertionError, UnicodeDecodeError):
            continue
        raise AssertionError('mutated artifact incorrectly passed: '+str(n))
    return len(variants)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--downloaded',type=Path,required=True)
    args=parser.parse_args()
    root=args.downloaded
    result=validate(root)
    result['independent_negative_mutants_rejected']=mutated_inputs_fail_closed(root)
    print('GQ470_LANDING_REAL70_INDEPENDENT_DOWNLOADED_ARTIFACT_PASS',json.dumps(result,sort_keys=True))

if __name__=='__main__':
    main()
