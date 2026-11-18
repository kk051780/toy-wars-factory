#!/usr/bin/env python3
"""Prove real Real55 original unchanged except one Host; patch is guarded.
This is source/authority validation, NOT a Roblox Studio video acceptance test.
"""
from pathlib import Path
import argparse,hashlib,sys,json
from copy import deepcopy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from compose_real56 import flatten,HOST,CLIENT,patch_host

def check(parent,candidate):
    _,original=flatten(parent)
    _,built=flatten(candidate)
    assert len(original)==55 and len(built)==56
    assert set(built)-set(original)=={CLIENT}
    assert sum(original[k].read_bytes()!=built[k].read_bytes() for k in original)==1
    for route in original:
        if route!=HOST:
            assert original[route].read_bytes()==built[route].read_bytes(),("RED_UNEXPECTED_ORIGINAL_CHANGE",route)
    src=original[HOST].read_text()
    compiled=built[HOST].read_text()
    assert patch_host(src)==compiled,"RED_COMPOSITION_NOT_REAL_SOURCE"
    for symbol in ('gq8ViralEpoch','EGGRUMBLE_ViralSeq','EGG_STEAL','EGG_DELIVER',
                   'CASTLE_DANGER','COMEBACK','VICTORY'):
        assert symbol in compiled,"RED_EVENT_MISSING_"+symbol
    assert compiled.count('gq8CaptureHint(')==5,"RED_UNKNOWN_EXTRA_HINT" # function + four event hooks
    assert len(compiled)>len(src) and compiled.count('local function startSession(mode:string)')==1
    # All accepted theft/delivery cues occur after a protected successful rules mutation.
    assert compiled.index('if ok and taker and (taker.heldEggs or 0)>before')<compiled.index('gq8CaptureHint(p,session,"EGG_STEAL")')
    assert compiled.index('if (c.depositedEggs or 0)>before then')<compiled.index('gq8CaptureHint(p,session,"EGG_DELIVER")')
    client=built[CLIENT].read_text()
    for check in ('local armed = false','StartVideoCaptureAsync','PromptSaveCapturesToGallery',
                  'StopVideoCapture','EGGRUMBLE_ViralSeq','RunService:IsStudio()'):
        assert check in client, "RED_CLIENT_CONSENT_"+check
    for bad in ('FireServer(', 'RemoteEvent', 'DataStoreService', 'MarketplaceService',
                'HttpService', 'TeleportService', 'UploadCaptureAsync(', 'PromptShareCapture(',
                'https://','http://'):
        assert bad not in client,"RED_USER_DATA_OR_GAME_AUTHORITY_"+bad
    for bad in ('new RemoteEvent','FireServer(','DataStoreService','MarketplaceService'):
        assert bad not in compiled[len(src):],"RED_NEW_GAME_AUTHORITY_"+bad
    # Fail closed if another Chat modified an owned anchor.
    mutants=[
        src.replace('local function startSession(mode:string)','local function startSession_v2(mode:string)',1),
        src.replace('session.world.Name=mode.."_Arena";session.world.Parent=folder','-- removed',1),
        src.replace('if c.alive and c.heldEggs>0 then','if c.alive and false then',1),
        src.replace('pcall(function() Rules.takeEggs(session.rules,tostring(p.UserId),1,entry.id) end)','-- removed',1),
        src.replace('if session.rules.winner~=nil then','if session.rules.winner==nil then',1),
    ]
    for i,bad in enumerate(mutants):
        assert bad!=src,"RED_UNAVAILABLE_MUTATION_"+str(i)
        try:patch_host(bad)
        except ValueError:pass
        else:raise AssertionError("RED_ACCEPTED_CHANGED_OWNER_ANCHOR_"+str(i))
    receipt=json.loads((candidate.parent/'GQ8_VIRAL56_RECEIPT.json').read_text())
    assert receipt['candidate']==56 and receipt['unchanged_original_source_count']==54
    assert receipt['new_remote_owners']==0 and receipt['new_store_owners']==0
    for record in receipt['sources']:
        route=tuple(record['route'].split('/'))
        b=built[route].read_bytes()
        assert hashlib.sha256(b).hexdigest()==record['sha256'] and len(b)==record['bytes']
    print('GQ8_VIRAL_REAL56_TRUE_EGG_CASTLE_WIN_54_SOURCE_EXACT_AND_MUTANT_PASS')

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    a=p.parse_args()
    check(a.parent,a.candidate)
