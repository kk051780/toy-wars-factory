#!/usr/bin/env python3
"""Extract real 86 Studio source bodies into Rojo hierarchy, not a simulated fixture."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
from collections import Counter
import sys
EXTS={'Script':'.server.luau','LocalScript':'.client.luau','ModuleScript':'.luau'}
def blob(s):
 b=s.encode('utf8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def extract(place,lock,dest):
 root=ET.fromstring(Path(place).read_bytes());dest=Path(dest)
 expected=json.loads(Path(lock).read_text())['scripts'];manifest=[]
 def walk(item,base=()):
  p=item.find('Properties')
  name=p.findtext("string[@name='Name']") if p is not None else None
  source=next((c.text or '' for c in p if c.get('name')=='Source'),None) if p is not None else None
  here=base+((name,) if name else ())
  if source is not None:
   cls=item.attrib['class'];key='/'.join(here)
   assert cls in EXTS and len(here)>=3 and here[0] in ('ReplicatedStorage','ServerScriptService','StarterPlayer'),key
   assert all(n.isidentifier() for n in here),key
   assert expected[key]=={'class':cls,'blob':blob(source)},key
   output=dest/'src'/Path(*here).with_suffix(EXTS[cls]);output.parent.mkdir(parents=True,exist_ok=True)
   assert not output.exists(),key
   output.write_text(source,encoding='utf-8')
   manifest.append({'path':key,'class':cls,'blob':blob(source)})
  for c in item.findall('Item'):walk(c,here)
 for child in root.findall('Item'):walk(child)
 assert len(manifest)==len(expected)==86
 assert set(x['path'] for x in manifest)==set(expected)
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 project={'name':'P0DFB032RealRC89','tree':{'$className':'DataModel',
 'ReplicatedStorage':{'$className':'ReplicatedStorage','TrapRaidersShared':{'$path':'src/ReplicatedStorage/TrapRaidersShared'}},
 'ServerScriptService':{'$className':'ServerScriptService','TrapRaidersS1':{'$path':'src/ServerScriptService/TrapRaidersS1'}},
 'StarterPlayer':{'$className':'StarterPlayer','StarterPlayerScripts':{'$className':'StarterPlayerScripts','$path':'src/StarterPlayer/StarterPlayerScripts'}}}}
 (dest/'default.project.json').write_text(json.dumps(project,indent=2)+'\n')
 return manifest
if __name__=='__main__':print('REAL_SOURCE_'+str(len(extract(*sys.argv[1:4])))+'_PASS')
