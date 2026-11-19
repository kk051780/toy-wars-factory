#!/usr/bin/env python3
"""Fail-closed REAL65 late-Host listener fix (no new runtime owner/route).

LSS and Realm wait at most 20s for Host's lobby. If Host creates it later
both scripts return permanently. Subscribe first, then check existing lobby.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

LSS = "ServerScriptService/EGGRUMBLE_LandSeaSkyTraversal"
REALM = "ServerScriptService/EGGRUMBLE_RealmBattleCore"
LSS_TAIL = '''local lobby=Workspace:WaitForChild(LOBBY,20)
if not lobby then
 warn("[EGGRUMBLE-LSS] Original V3 Host absent; no scene created")
 return
end
for _,world in ipairs(lobby:GetChildren()) do watchWorld(world) end
lobby.ChildAdded:Connect(watchWorld)'''
REALM_HEAD = '''local lobby=Workspace:WaitForChild(LOBBY_NAME,20)
if not lobby then warn("[GQ8-REALM] V3 Host absent; no realm created");return end
local function watchWorld(world)'''
REALM_TAIL = '''for _,w in ipairs(lobby:GetChildren()) do watchWorld(w) end
lobby.ChildAdded:Connect(watchWorld)'''

def subscription(var: str, child: str) -> str:
    return f'''-- REAL65_LATE_HOST_WATCH_V1: keep the unique existing realm/traversal owner.
-- Subscribe before find: a lobby arriving after 20s is never silently lost.
local watchedLobbies={{}}
local function attachCanonicalLobby(current)
  if not current or current.Parent~=Workspace or not current:IsA("Folder")
    or current.Name~={var} or watchedLobbies[current] then return end
  watchedLobbies[current]=true
  current.ChildAdded:Connect(watchWorld)
  for _,{child} in ipairs(current:GetChildren()) do watchWorld({child}) end
  current.Destroying:Connect(function() watchedLobbies[current]=nil end)
end
Workspace.ChildAdded:Connect(function(inst)
  if inst.Name=={var} then attachCanonicalLobby(inst) end
end)
local currentLobby=Workspace:FindFirstChild({var})
if currentLobby then attachCanonicalLobby(currentLobby) end'''

def apply(route: str, text: str) -> str:
    if 'REAL65_LATE_HOST_WATCH_V1' in text:
        raise ValueError('RED_DOUBLE_PATCH_'+route)
    if route == LSS:
        old=LSS_TAIL
        new=subscription('LOBBY','world')
        if text.count(old)!=1 or not text.rstrip().endswith(old):
            raise ValueError('RED_LSS_ORIGINAL_FOOTER_DRIFT')
        out=text.replace(old,new,1)
    elif route == REALM:
        if text.count(REALM_HEAD)!=1 or text.count(REALM_TAIL)!=1 or not text.rstrip().endswith(REALM_TAIL):
            raise ValueError('RED_REALM_ORIGINAL_FOOTER_DRIFT')
        out=text.replace(REALM_HEAD,'local function watchWorld(world)',1).replace(
            REALM_TAIL,subscription('LOBBY_NAME','w'),1)
    else:
        raise ValueError('RED_UNKNOWN_ROUTE')
    if out.count('Workspace.ChildAdded:Connect(function(inst)')!=1 or 'WaitForChild(LOBBY,20)' in out or 'WaitForChild(LOBBY_NAME,20)' in out:
        raise ValueError('RED_LATE_HOST_WATCH_NOT_INSTALLED')
    if out.count('current.ChildAdded:Connect(watchWorld)')!=1 or out.count('current:GetChildren()')!=1:
        raise ValueError('RED_WATCHER_DUPLICATION_OR_MISSING')
    return out

def check_fixture() -> None:
    a='local function watchWorld(world)\nend\n'+LSS_TAIL
    b=REALM_HEAD+'\nend\n'+REALM_TAIL
    for key,orig in ((LSS,a),(REALM,b)):
        out=apply(key,orig)
        assert 'Workspace.ChildAdded:Connect(function(inst)' in out
        assert out.index('Workspace.ChildAdded:Connect(function(inst)') < out.index('Workspace:FindFirstChild(')
        for mutant in (orig.replace('WaitForChild','FindFirstChild',1),orig+'\nlocal a=1'):
            try: apply(key,mutant)
            except ValueError: pass
            else: raise AssertionError('RED_MUTANT_ACCEPTED_'+key)
        try: apply(key,out)
        except ValueError: pass
        else: raise AssertionError('RED_DOUBLE_PATCH_ACCEPTED')
    print('REAL65_LATE_HOST_WATCH_SELFTEST_PASS')

def run(project_path: Path, receipt_path: Path):
    project=json.loads(project_path.read_text(encoding='utf8'))
    receipt=json.loads(receipt_path.read_text(encoding='utf8'))
    sources=receipt['sources']
    if project['name']!='EGGRUMBLE_REAL65_PRIVATE_STUDIO' or len(sources)!=65 or receipt['original_real63_byte_unchanged']!=57:
        raise ValueError('RED_REAL65_SOURCE_CONTRACT_DRIFT')
    routes={x['route']:x for x in sources}
    changed=[]
    expected_patched={
        'ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview',
        'ServerScriptService/EGGRUMBLE_SevenRoleCombat',
        'ServerScriptService/EGGRUMBLE_InvulRuntime',
        'ServerScriptService/GQ805_LobbyGuildShop',
        'ServerScriptService/GQ8_LobbySocialPlaza',
        REALM,
    }
    if set(receipt['patched_existing_routes'])!=expected_patched:
        raise ValueError('RED_PREVIOUS_PATCHED_ROUTES_DRIFT')
    for route in (LSS,REALM):
        node=project['tree']
        for segment in route.split('/'):
            node=node[segment]
        file=project_path.parent/node['$path']
        src=file.read_bytes()
        record=routes[route]
        if (record['class']!='Script' or record['sha256']!=hashlib.sha256(src).hexdigest()
            or record['bytes']!=len(src)):
            raise ValueError('RED_REAL65_SOURCE_SHA_OR_CLASS_'+route)
        replaced=apply(route,src.decode('utf8')).encode('utf8')
        file.write_bytes(replaced)
        record['sha256']=hashlib.sha256(replaced).hexdigest()
        record['bytes']=len(replaced)
        changed.append(route)
    receipt['patched_existing_routes'].append(LSS)
    receipt['original_real63_byte_unchanged']=56
    receipt['late_host_world_watch']={
        'feature_id':'GQ8_REAL65_LATE_HOST_REALM_LSS_WATCH_20261119',
        'routes':changed,
        'source_count':65,
        'host_or_remote_duplicates':0,
        'event_subscription_before_lookup':True,
        'no_20s_permanent_disarm':True,
        'studio':'NOT_TESTED',
        'rollback':'OFF63_EXACT_OFFICIAL.rbxlx unchanged'}
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf8')
    print('REAL65_LATE_HOST_WATCH_2_EXISTING_SCRIPTS_PATCHED_SOURCE65_OFF63_UNTOUCHED')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--project',type=Path)
    p.add_argument('--receipt',type=Path)
    args=p.parse_args()
    if args.self_test: check_fixture()
    else:
        if not args.project or not args.receipt:p.error('project and receipt required')
        run(args.project,args.receipt)
