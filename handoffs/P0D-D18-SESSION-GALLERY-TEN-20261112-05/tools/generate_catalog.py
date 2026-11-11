#!/usr/bin/env python3
"""Regenerate SOURCE-only Luau from checked-in JSON, with no external deps."""
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
def serial(x):
    if isinstance(x,str):return json.dumps(x,ensure_ascii=False)
    if isinstance(x,bool):return 'true' if x else 'false'
    if isinstance(x,(int,float)):return repr(x)
    if isinstance(x,list):return '{'+', '.join(serial(v) for v in x)+'}'
    if isinstance(x,dict):return '{'+', '.join('['+serial(k)+']='+serial(v) for k,v in x.items())+'}'
    raise TypeError(type(x))
def output():
  data=json.loads((ROOT/'data/gallery.json').read_text(encoding='utf8'))
  lines=['-- GENERATED FROM data/gallery.json by tools/generate_catalog.py. Do not edit by hand.',
         '-- Non-authoritative original preview data only; no inventory, rewards or entitlements.',
         'local entries = '+serial(data['entries']),'','local byId = {}','for _, item in ipairs(entries) do',
         '    assert(byId[item.id] == nil, "duplicate gallery ID")', '    byId[item.id] = item','end','',
         'local Catalog = {}','function Catalog.all()','    return entries','end',
         'function Catalog.byId(id)','    return byId[id]','end',
         'function Catalog.filter(category, onlyFavorites, favorites)', '    local result = {}',
         '    for _, entry in ipairs(entries) do',
         '        local categoryOK = (category == "すべて" or category == nil or entry.category == category)',
         '        local favoriteOK = not onlyFavorites or (favorites ~= nil and favorites[entry.id] == true)',
         '        if categoryOK and favoriteOK then', '            table.insert(result, entry)',
         '        end','    end','    return result','end','return Catalog','']
  return '\n'.join(lines)
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
 dest=ROOT/'src/D18GalleryCatalog.luau';s=output()
 if args.check:
  assert dest.read_text(encoding='utf8')==s,'Generated gallery catalog is stale'
  print('catalog generation EXACT')
 else:
  dest.write_text(s,encoding='utf8');print('wrote',dest)
if __name__=='__main__':main()
