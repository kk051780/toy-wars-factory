#!/usr/bin/env python3
"""Deterministic JSON-to-Luau source. stdlib only, no Roblox runtime required."""
import argparse, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]

def lua_string(s):
    return json.dumps(s, ensure_ascii=False)

def render(data):
    a=["--!strict", "-- GENERATED: python tools/generate_catalog.py --check", "-- Display-only original D18 models. Do not edit directly.", "return {"]
    for m in data['models']:
        a += ["  ["+lua_string(m['id'])+"] = {", "    id = "+lua_string(m['id'])+",", "    name = "+lua_string(m['name'])+",", "    rarity = "+lua_string(m['rarity'])+",", "    world = "+lua_string(m['world'])+",", "    parts = {"]
        for p in m['parts']:
            def nums(xs): return "{"+", ".join(str(x) for x in xs)+"}"
            a.append("      {name="+lua_string(p['name'])+", shape="+lua_string(p['shape'])+", pos="+nums(p['position'])+", size="+nums(p['size'])+", rgb="+nums(p['color'])+", rot="+str(p['rotation_z'])+", far="+("true" if p['far_detail'] else "false")+"},")
        a += ["    },", "  },"]
    return "\n".join(a+["}",""])

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    data=json.loads((ROOT/'data/showcase_models.json').read_text(encoding='utf-8'))
    output=ROOT/'luau/ShowcaseCatalog.luau'; expected=render(data)
    if args.check:
        if not output.exists() or output.read_text(encoding='utf-8')!=expected:
            print('FAIL: catalog not generated from exact JSON',file=sys.stderr); return 1
        print('CATALOG_EXACT_OK');return 0
    output.write_text(expected, encoding='utf-8');print('GENERATED',output);return 0
if __name__=='__main__': raise SystemExit(main())
