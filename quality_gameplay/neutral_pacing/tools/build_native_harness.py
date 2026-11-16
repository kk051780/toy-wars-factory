#!/usr/bin/env python3
"""Execute exact neutral pacing source in native Luau VM (no mock rewrite)."""
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'EGGRUMBLE_NeutralSpawnPacing.luau'
SPEC = ROOT / 'tests' / 'spec_native.luau'

def build():
    source = SRC.read_text(encoding='utf-8')
    spec = SPEC.read_text(encoding='utf-8')
    assert source.rstrip().endswith('return Pacing'), 'source entrypoint changed'
    assert source.count('function Pacing.step(') == 1
    assert re.search(r'Pacing.MAX_ALIVE\s*=\s*110', source), 'actor cap changed'
    return source.rsplit('return Pacing', 1)[0] + '\n' + spec

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(build(), encoding='utf-8')
    print('EXACT_ORIGINAL_SOURCE_HARNESS_WRITTEN', args.out)
