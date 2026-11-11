#!/usr/bin/env python3
"""Deterministically compile this packet's canonical plain JSON into an optional Luau catalog.
No image model, Roblox API or network required. Never edits gameplay files.
"""
import argparse, json, math, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/'data/characters.json'
DST=ROOT/'luau/ShowcaseCatalog.luau'
IDS={'TRCA-SP-027':('大地の共鳴','MAGIC','MYTHIC','歯車の赤峡谷'), 'TRCA-VE-090':('時帰りの砂船','VEHICLE','LEGENDARY','砂時計の迷宮')}
SHAPES={'Block','Ball','Wedge','Cylinder'}

def valid(data):
    if data['game_id']!='TRAP_RAIDERS' or data['work_id']!='p0d-siege-v19' or set(data['characters'])!=set(IDS):
        raise ValueError('wrong game/IDs')
    for ident,c in data['characters'].items():
        if tuple(c[k] for k in ('displayName','class','rarity','world'))!=IDS[ident]:
            raise ValueError('identity mismatch')
        if not 6<=len(c['parts'])<=32:
            raise ValueError('parts budget')
        names=set()
        for p in c['parts']:
            name=p['name']
            if not name.isascii() or not name.replace('_','').isalnum() or name in names:
                raise ValueError('invalid/duplicate part name')
            names.add(name)
            if p['shape'] not in SHAPES or type(p['farDetail']) is not bool: raise ValueError('shape/LOD')
            for k,n in [('position',3),('size',3),('rgb',3),('rotation',3)]:
                if len(p[k])!=n: raise ValueError('vector')
                for x in p[k]:
                    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):raise ValueError('non-finite numeric')
            if any(not 0.05<=x<=8 for x in p['size']): raise ValueError('bad size')
            if any(abs(x)>15 for x in p['position']): raise ValueError('bad position')
            if any(not isinstance(x,int) or x<0 or x>255 for x in p['rgb']): raise ValueError('bad RGB')

def num(v):
    if isinstance(v,int):return str(v)
    return format(v,'.7g')
def array(v):return '{'+', '.join(num(x) for x in v)+'}'
def quote(s):return json.dumps(s,ensure_ascii=False)
def render(data):
    valid(data)
    lines=['--!strict','-- Generated from ../data/characters.json; edit JSON, then run generator.','-- Decorative Roblox primitives. No gameplay authority or external assets.','return {']
    for ident in sorted(data['characters']):
        ch=data['characters'][ident]
        lines.append('    ['+quote(ident)+'] = {')
        for key in ('displayName','class','rarity','world','concept'):
            lines.append('        '+key+' = '+quote(ch[key])+',')
        lines.append('        parts = {')
        for p in ch['parts']:
            lines.append('            {name='+quote(p['name'])+', shape='+quote(p['shape'])+', position='+array(p['position'])+', size='+array(p['size'])+', rgb='+array(p['rgb'])+', farDetail='+str(p['farDetail']).lower()+', rotation='+array(p['rotation'])+'},')
        lines+=['        },','    },']
    lines+=['}','']
    return '\n'.join(lines)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    content=render(json.loads(SRC.read_text(encoding='utf-8')))
    if args.check:
        if not DST.exists() or DST.read_text(encoding='utf-8')!=content:raise SystemExit('Catalog mismatch')
        print('CATALOG_EXACT_SOURCE_MATCH')
    else:
        DST.write_text(content,encoding='utf-8')
        print('WROTE '+str(DST))
if __name__=='__main__':main()
