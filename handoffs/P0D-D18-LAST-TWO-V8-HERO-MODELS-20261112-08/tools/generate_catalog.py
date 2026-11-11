#!/usr/bin/env python3
"""Deterministically generate plain original Luau from immutable local JSON."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'characters.json'
OUT = ROOT / 'src' / 'ShowcaseCatalog.luau'

def lua(value, indent=0):
    pad = ' ' * indent
    if value is None:
        return 'nil'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int,float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        if not value: return '{}'
        return '{\n' + ''.join(' ' * (indent+4) + lua(x,indent+4) + ',\n' for x in value) + pad+'}'
    if isinstance(value, dict):
        if not value: return '{}'
        return '{\n' + ''.join(' ' * (indent+4) + '[' + lua(k)+'] = '+lua(value[k],indent+4)+',\n' for k in sorted(value)) +pad+'}'
    raise TypeError(type(value))

def render():
    data=json.loads(DATA.read_text())
    assert set(data['characters'])=={'TRCA-TR-063','TRCA-WE-099'}
    return ('-- ORIGINAL P0-D D18 v8 last two original flagship standalone catalog.\n'
            '-- GENERATED: python tools/generate_catalog.py --check. No third-party assets.\n'
            'local C = {}\n'
            'local DEFINITIONS = '+lua(data['characters'])+'\n'
            'function C.get(id)\n'
            '    if type(id) ~= "string" then return nil end\n'
            '    return DEFINITIONS[id]\n'
            'end\n'
            'function C.ids()\n'
            '    return {"TRCA-TR-063", "TRCA-WE-099"}\n'
            'end\n'
            'return C\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    actual=render()
    if args.check:
        assert OUT.read_text()==actual, 'generated source does not match data'
        print('CATALOG_SOURCE_MATCH PASS')
    else:
        OUT.write_text(actual)
        print('Generated',OUT)
