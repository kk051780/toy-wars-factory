#!/usr/bin/env python3
"""Build one verified private67 FB007 candidate FROM actual assembled official66.

Runs only in A-PREP GitHub workflow. Never writes official RC/main.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,shutil,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import apply_fb007_lobby as overlay

def treehash(root:Path)->str:
    sha=hashlib.sha256()
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        sha.update(str(p.relative_to(root)).encode()+b'\0')
        sha.update(p.read_bytes())
    return sha.hexdigest()

def build(original:Path,private:Path,output:Path,compiler:Path,rojo:Path):
    assert original.is_dir() and (original/'SOURCE_LOCK.json').exists()
    assert compiler.is_file() and rojo.is_file()
    assert not private.exists() and not output.exists()
    assert len(overlay.sources(original))==66
    original_sha=treehash(original)
    shutil.copytree(original,private)
    assert treehash(private)==original_sha
    assert overlay.apply(private,False) is False
    assert treehash(private)==original_sha,"FB007_OFF_NOT_BYTE_EXACT"
    overlay.apply(private,True)
    actual=overlay.sources(private)
    assert len(actual)==67
    old=overlay.sources(original)
    assert {p for p in old if old[p]!=actual[p]}=={overlay.GAME,overlay.V4}
    assert set(actual)-set(old)=={overlay.DEST}
    assert all(old[p]==actual[p] for p in old if p not in (overlay.GAME,overlay.V4))
    lock=json.loads((private/'SOURCE_LOCK.json').read_text('utf8'))
    feature=json.loads((private/'RC_FEATURE_LOCK.json').read_text('utf8'))
    assert feature['feature_flags'][overlay.FEATURE] is True
    pins={p:overlay.blob(v) for p,v in actual.items()}
    assert lock['total_scripts']==feature['total_sources']==67
    assert lock['blobs']==feature['source_gitblobs']==pins
    game=actual[overlay.GAME].decode('utf8')
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert 'LobbyIsland.build(map.model)' in game
    assert 'match.phase=="LOBBY" and carry[player]==nil' in game
    assert 'LobbyIsland.inLobby(position)' in game
    for file in sorted((private/'src').rglob('*.luau')):
        result=subprocess.run([str(compiler),str(file)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        assert result.returncode==0,("LUAU_COMPILER_ERROR",file,result.stderr.decode("utf8","replace")[:1500])
    output.mkdir(parents=True)
    place=output/'FB007_PRIVATE67.rbxlx'
    subprocess.run([str(rojo),'build',str(private/'default.project.json'),'-o',str(place)],check=True)
    raw=collections.Counter(value.decode('utf8') for value in actual.values())
    included=collections.Counter()
    titles=collections.Counter()
    for item in ET.fromstring(place.read_bytes()).iter('Item'):
        if item.get('class') not in ('Script','LocalScript','ModuleScript'):
            continue
        source=item.find("./Properties/string[@name='Source']")
        if source is None:continue
        included[source.text or '']+=1
        name=item.find("./Properties/string[@name='Name']")
        if name is not None:
            titles[(item.get('class'),name.text)]+=1
    assert included==raw,("ROJO_BINARY_SOURCE_MISMATCH",len(included),len(raw))
    assert titles[('Script','Game')]==1,"DUPLICATE_GAME"
    assert titles[('ModuleScript','LobbyDojoIsland')]==1,"MISSING_LOBBY"
    assert titles[('Script','V4TrainingBridge')]==1,"MISSING_V4_TRAINING"
    payload=output/'FB007_PRIVATE67_PAYLOAD.zip'
    with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.write(place,place.name)
    report={
       'schema':'P0D_FB007_PRIVATE67_SOURCE_EXACT_V1',
       'source_count':len(actual),'original_scripts_preserved':64,
       'modified_scripts':sorted([overlay.GAME,overlay.V4]),
       'new_scripts':[overlay.DEST],
       'original_rc66_tree_sha256':original_sha,
       'private_candidate_commit':'GITHUB_ACTIONS_PR_HEAD_OR_MERGE_REF',
       'luau_compiled_source_count':len(actual),
       'rojo_source_exact':True,
       'game_remote_owner_count':titles[('Script','Game')],
       'studio_2client':'NOT_TESTED','android':'NOT_TESTED','owner_fun':'NOT_TESTED',
       'official_rc_adopted':False,
       'place_bytes':place.stat().st_size,
       'place_sha256':hashlib.sha256(place.read_bytes()).hexdigest(),
       'zip_payload_bytes':payload.stat().st_size,
    }
    (output/'FB007_PRIVATE67_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print('FB007_ACTUAL_RC66_TO_PRIVATE67_LUAU_ROJO_SOURCE_EXACT_PASS',json.dumps(report))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--original',required=True,type=Path)
    p.add_argument('--private',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--luau-compile',required=True,type=Path)
    p.add_argument('--rojo',required=True,type=Path)
    a=p.parse_args()
    build(a.original,a.private,a.output,a.luau_compile,a.rojo)
