#!/usr/bin/env python3
"""Deterministically compile D18 JSON art-direction geometry to a Luau ModuleScript."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def lua(value, depth=0):
    pad = '    ' * depth
    inner = '    ' * (depth + 1)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return 'nil'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        if not value:
            return '{}'
        if len(value) <= 4 and not any(isinstance(e, (dict, list)) for e in value):
            return '{' + ', '.join(lua(e, depth + 1) for e in value) + '}'
        return '{\n' + ''.join(inner + lua(e, depth + 1) + ',\n' for e in value) + pad + '}'
    if isinstance(value, dict):
        if not value:
            return '{}'
        return '{\n' + ''.join(inner + '[' + lua(k) + '] = ' + lua(v, depth + 1) + ',\n' for k, v in sorted(value.items())) + pad + '}'
    raise TypeError(type(value))


def render(data):
    return ('-- GENERATED from data/mascot_geometry.json; do not hand-edit.\n'
            '-- Standalone cosmetic-only, noncombat geometry data; no asset IDs.\n'
            'local Catalog = {}\n'
            'Catalog.Data = ' + lua(data) + '\n\n'
            'function Catalog.get(characterId)\n'
            '    return Catalog.Data.characters[characterId]\n'
            'end\n\nreturn Catalog\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads((args.root/'data/mascot_geometry.json').read_text(encoding='utf-8'))
    dest = args.root/'luau/MascotPreviewCatalog.luau'
    result = render(data)
    if args.check:
        assert dest.read_text(encoding='utf-8') == result, 'Luau catalog out of sync with JSON'
        print('GENERATED_CATALOG_EXACT_MATCH')
    else:
        dest.write_text(result, encoding='utf-8')
        print(f'GENERATED {dest}')

if __name__ == '__main__':
    main()
