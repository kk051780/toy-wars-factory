#!/usr/bin/env python3
"""Compile standalone original D18 showroom JSON into a Luau table; no network/Roblox execution."""
import argparse, copy, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/showcase_models.json'
TARGET=ROOT/'luau/ShowcaseCatalog.luau'
IDENTITIES={
'TRCA-SP-081':('黄金の種まき','MAGIC','LEGENDARY','黄金麦の丘'),
'TRCA-VE-036':('永久晶観測台','VEHICLE','MYTHIC','氷鏡の宮'),
'TRCA-ZO-108':('七鈴の大隊長','ZOMBIE','LEGENDARY','暁鐘の王城')}
CUES={'TRCA-SP-081':{'WoodenHandPalm','SingleGoldenSeed','WheatRayLeft','WheatRayCenter','WheatRayRight'},
'TRCA-VE-036':{'SledFloor','MatteIceMirror','TallCrystal','OctMirrorEdge1','OctMirrorEdge8'},
'TRCA-ZO-108':{'WhiteReturnRoster'} | {f'ReturnBell{i}' for i in range(1,8)}}

def validate(data):
    if data.get('game_id')!='TRAP_RAIDERS' or data.get('work_id')!='p0d-siege-v19':raise ValueError('game/work mismatch')
    if set(data.get('characters',{}))!=set(IDENTITIES):raise ValueError('unexpected ID')
    for ident, ch in data['characters'].items():
        if tuple(ch[k] for k in ('name','category','rarity','world')) != IDENTITIES[ident]:raise ValueError('canonical identity drift')
        parts=ch['parts']
        if not 5<=len(parts)<=24:raise ValueError('parts budget')
        names=[p['name'] for p in parts]
        if len(names)!=len(set(names)) or any(not x.isascii() or not x.replace('_','').isalnum() for x in names):raise ValueError('part name')
        if not CUES[ident].issubset(names):raise ValueError('lost silhouette')
        for p in parts:
            if p['shape'] not in ('Block','Ball','Wedge') or type(p['far']) is not bool:raise ValueError('invalid shape/far')
            for fld in ('pos','size','rgb'):
                if len(p[fld])!=3:raise ValueError('invalid vector')
                if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in p[fld]):raise ValueError('invalid number')
            if any(v<.03 or v>7 for v in p['size']):raise ValueError('unsafe dimensions')
            if any(abs(v)>12 for v in p['pos']):raise ValueError('unsafe position')
            if any(type(v) is not int or v<0 or v>255 for v in p['rgb']):raise ValueError('unsafe RGB')
            if isinstance(p['zrot'],bool) or not isinstance(p['zrot'],(int,float)) or not math.isfinite(p['zrot']) or abs(p['zrot'])>360:raise ValueError('unsafe rotation')

def q(s):return json.dumps(s,ensure_ascii=False)
def n(v):return str(v) if isinstance(v,int) else format(v,'.9g')
def arr(v):return '{'+', '.join(n(x) for x in v)+'}'
def render(data):
    validate(data)
    out=['--!strict','-- Generated: data/showcase_models.json (do not edit this Luau catalog manually).','-- Original display-only art. No ID assignment, rewards, server authority or physics.','return {']
    for ident,ch in sorted(data['characters'].items()):
        out.append('    ['+q(ident)+'] = {')
        for key in ('name','category','rarity','world','story','silhouette'):
            out.append('        '+key+' = '+q(ch[key])+',')
        out.append('        parts = {')
        for p in ch['parts']:
            out.append('            {name='+q(p['name'])+', shape='+q(p['shape'])+', pos='+arr(p['pos'])+', size='+arr(p['size'])+', rgb='+arr(p['rgb'])+', far='+str(p['far']).lower()+', zrot='+n(p['zrot'])+'},')
        out+=['        },','    },']
    out+=['}','']
    return '\n'.join(out)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    source=json.loads(SOURCE.read_text(encoding='utf-8'));target=render(source)
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding='utf-8')!=target:raise SystemExit('GENERATOR_MISMATCH')
        print('GENERATED_CATALOG_EXACT')
    else:
        TARGET.write_text(target,encoding='utf-8');print('GENERATED_CATALOG_WRITTEN')
if __name__=='__main__':main()
