#!/usr/bin/env python3
"""FB032: source-exact PR479 StagePickupLoot LOS onto real PR481 RC88."""
from pathlib import Path
from lxml import etree
import hashlib, json, sys

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def blob(s):
    b=s.encode('utf8');return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def inventory(tree):
    result={}
    def walk(item,parent=()):
        p=item.find('Properties');name=p.findtext('string[@name="Name"]') if p is not None else None
        src=next((x for x in p if x.get('name')=='Source'),None) if p is not None else None
        here=parent+((name,) if name else ())
        if src is not None:
            key='/'.join(here)
            assert key not in result and len(here)>=3 and item.get('class') in ('Script','LocalScript','ModuleScript')
            result[key]=(item.get('class'),src)
        for c in item.findall('Item'):walk(c,here)
    for item in tree.getroot().findall('Item'):walk(item)
    assert len(result)==86,len(result)
    return result

def build(rc88,importer,out):
    rc88,importer,out=map(Path,(rc88,importer,out))
    assert digest(rc88)=='e207a79b777d3b0814ec9580bc9f7ffaffeb07581d6b1010ac89b2846c2accd8','RC88_PARENT_SHA'
    assert digest(importer)=='d67f9f68912cb67de0e184844d57649fbe50e5b70ab30cffbe3ee320e6a15cd8','PR479_SOURCE_SHA'
    assert not out.exists() and out!=rc88 and out!=importer
    parser=etree.XMLParser(resolve_entities=False,no_network=True,load_dtd=False)
    t=etree.parse(str(rc88),parser);u=etree.parse(str(importer),parser)
    a,b=inventory(t),inventory(u)
    assert set(a)==set(b) and all(a[k][0]==b[k][0] for k in a),'SCRIPT_HIERARCHY'
    k='ServerScriptService/TrapRaidersS1/StagePickupLoot'
    assert a[k][0]==b[k][0]=='ModuleScript'
    assert blob(a[k][1].text or '')=='3fb954f4bcc9d5728b55cc284e6519c304bd61c2'
    assert blob(b[k][1].text or '')=='450ba944550c3bc44ce04dc9b91da943090598d9'
    s=b[k][1].text or ''
    for contract in ('unobstructed(player,root.Position,','unobstructed(player,origin,projected,nil)','params.RespectCanCollide=true'):
        assert contract in s,contract
    before={k:blob(v[1].text or '') for k,v in a.items()}
    a[k][1].text=s
    assert [n for n in a if before[n]!=blob(a[n][1].text or '')]==[k]
    t.write(str(out),encoding='utf-8',xml_declaration=False,pretty_print=True)
    z=inventory(etree.parse(str(out),parser))
    assert all((z[n][0],blob(z[n][1].text or ''))==(a[n][0],blob(a[n][1].text or '')) for n in a)
    answer={'output_sha256':digest(out),'output_bytes':out.stat().st_size,'sources':86,'changed':[k], 'unchanged':85,'official_rc_write':False,'studio':'NOT_RUN','android':'NOT_RUN','owner_accepted':False}
    assert answer['output_sha256']=='088f06d11c543c6d62fbc70359adad9a49dc2c12a8b9ca6835fed1adb79e4d2d'
    assert answer['output_bytes']==847911
    return answer

if __name__=='__main__':
    assert len(sys.argv)==4
    print(json.dumps(build(*sys.argv[1:]),indent=2))
