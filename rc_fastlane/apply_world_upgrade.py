#!/usr/bin/env python3
"""Optional 66->67 Studio battlefield scenery overlay; A PREP only, no official RC writes."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'features/p0_world_upgrade/CastleWorldUpgrade.server.luau'
PIN='602e828fbd2a00c1b5a350e7e6bc69a6dbc9a158'
FEATURE='P0D_CASTLE_WORLD_3ROUTE_V1'
DEST='server/CastleWorldUpgrade.server.luau'

def blob(data:bytes)->str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def sources(dist:Path)->dict[str,bytes]:
    return {p.relative_to(dist/'src').as_posix():p.read_bytes() for p in sorted((dist/'src').rglob('*.luau'))}
def apply(dist:Path, enabled:bool)->bool:
    if not enabled:
        print('P0D_CASTLE_WORLD_OFF_EXACT_NO_MUTATION')
        return False
    code=SOURCE.read_bytes()
    assert blob(code)==PIN,'WORLD_SOURCE_DRIFT'
    lua=code.decode('utf8')
    for needle in ('if not RunService:IsStudio() then return end',
                   'INVASION_ROUTE_', 'name.."_3D_FORTRESS"',
                   'P0D_CASTLE_WORLD_UPGRADE','GrassArena','ARENA_BOUNDARY_N',
                   'ARENA_BOUNDARY_S','RIVER_BRIDGE_', 'egg/score/HP authoritative'):
        assert needle in lua, ('SOURCE_REQUIRED',needle)
    assert lua.count('battlement(castle,')==1
    assert lua.count('gatehouse(castle,')==1
    for forbidden in ('Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                      'FireServer(', 'GetDataStore(', 'UpdateAsync(',
                      'TakeDamage(', 'MarketplaceService'):
        assert forbidden not in lua,forbidden
    before=sources(dist)
    assert len(before)==66,('NEEDS_OFFICIAL66',len(before))
    assert DEST not in before
    assert 'server/Game.server.luau' in before and 'server/MapBuilder.luau' in before
    lp=dist/'SOURCE_LOCK.json';fp=dist/'RC_FEATURE_LOCK.json'
    lock=json.loads(lp.read_text('utf8'));feature=json.loads(fp.read_text('utf8'))
    orig={p:blob(b) for p,b in sorted(before.items())}
    assert lock['total_scripts']==66 and lock['blobs']==orig
    assert feature['total_sources']==66 and feature['source_gitblobs']==orig
    assert FEATURE not in feature['feature_flags']
    cfg=json.loads((dist/'default.project.json').read_text('utf8'))
    assert cfg['tree']['ServerScriptService']['TrapRaidersS1']['$path']=='src/server'
    # No project edits required: Rojo maps the whole existing server directory.
    after={**before,DEST:code}
    hashes={p:blob(b) for p,b in sorted(after.items())}
    assert len(after)==67 and all(before[p]==after[p] for p in before)
    lock['total_scripts']=67
    lock['blobs']=hashes
    lock['rc_castle_world_upgrade']={
        'id':FEATURE,'added':DEST,'original66_byte_identical':True,
        'Game_Remote_Store_unchanged':True,'studio_solo':'NOT_TESTED',
        'two_client':'NOT_TESTED','FUN':'NOT_TESTED',
        'rollback':'omit overlay to preserve exact canonical66',
        'notes':'Scenery changes Arena size/boundary only in Studio; full physics and path acceptance pending'
    }
    feature['total_sources']=67
    feature['source_gitblobs']=hashes
    feature['feature_flags'][FEATURE]=True
    (dist/'src'/DEST).write_bytes(code)
    lp.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8')
    fp.write_text(json.dumps(feature,ensure_ascii=False,indent=2)+'\n','utf8')
    assert sources(dist)==after
    print('P0D_CASTLE_WORLD_67_ONE_EXTRA_SERVER_ORIGINAL66_EXACT')
    return True
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--dist',required=True,type=Path)
    p.add_argument('--enabled',required=True,choices=('true','false'))
    a=p.parse_args();apply(a.dist,a.enabled=='true')
