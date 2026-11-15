#!/usr/bin/env python3
"""Exact 86 original Roblox Script/LocalScript/ModuleScript source and class manifest."""
import json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

EXTS={'Script':'.server.luau','LocalScript':'.client.luau','ModuleScript':'.luau'}
def blob(s):
 b=s.encode('utf8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def extract(place,lock,dest):
 root=ET.fromstring(Path(place).read_bytes())
 dest=Path(dest); source_tree=dest/'src';manifest=[]
 def walk(item,parents=()):
  p=item.find('Properties');name=p.findtext("string[@name='Name']") if p is not None else None
  src=p.findtext("string[@name='Source']") if p is not None else None
  here=parents+((name,) if name else ())
  if src is not None:
   assert item.attrib.get('class') in EXTS,(here,item.attrib)
   assert len(here)>=3 and here[0] in ('ServerScriptService','ReplicatedStorage','StarterPlayer'),here
   assert all(x.isidentifier() for x in here),here
   extension=EXTS[item.attrib['class']]
   output=source_tree/Path(*here).with_suffix(extension)
   assert not output.exists(),('DUPLICATE_SOURCE_PATH',str(output))
   output.parent.mkdir(parents=True,exist_ok=True)
   output.write_text(src,encoding='utf8')
   manifest.append({'path':'/'.join(here),'class':item.attrib['class'],'blob':blob(src)})
  for child in item.findall('Item'):walk(child,here)
 for item in root.findall('Item'):walk(item)
 assert len(manifest)==86,len(manifest)
 assert len(set(m['path'] for m in manifest))==86
 locks=json.loads(Path(lock).read_text())
 assert Counter(x['blob'] for x in manifest)==Counter(locks['blobs'].values()),'SOURCE_LOCK_DRIFT'
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 project={'name':'P0DFB030LootLOSPrivate86','tree':{'$className':'DataModel',
   'ReplicatedStorage':{'$className':'ReplicatedStorage','TrapRaidersShared':{'$path':'src/ReplicatedStorage/TrapRaidersShared'}},
   'ServerScriptService':{'$className':'ServerScriptService','TrapRaidersS1':{'$path':'src/ServerScriptService/TrapRaidersS1'}},
   'StarterPlayer':{'$className':'StarterPlayer','StarterPlayerScripts':{'$className':'StarterPlayerScripts','$path':'src/StarterPlayer/StarterPlayerScripts'}}}}
 (dest/'default.project.json').write_text(json.dumps(project,indent=2)+'\n')
 return manifest
if __name__=='__main__':
 got=extract(*sys.argv[1:4]);print('REAL_SOURCE_EXTRACT_'+str(len(got))+'_PASS')
