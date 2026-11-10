"""Deterministic S1 CASTLE versus two-EGG optimistic LOWER-BOUND calculator.

These are no-defender theoretical fastest times. All obstacles, PvP interruptions,
network/server scheduler latency, collision and map elevation are ignored.
For route travel between two interaction areas, subtract BOTH radii, hence an
optimistic lower bound (not a physically achievable full-path assertion).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SOURCE_SHA = '35d7d0525388e885aac8281eff2315a59831e0cf'
ALLOWED_ROLES = ('RAIDER', 'GUARDIAN')


class ModelError(ValueError):
    pass


def _positive_number(v: Any, label: str, *, allow_zero: bool = False) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ModelError(f'{label} must be an ordinary number')
    if not math.isfinite(v) or (v < 0 if allow_zero else v <= 0):
        raise ModelError(f'{label} must be finite and {"nonnegative" if allow_zero else "positive"}')
    return float(v)


def _pos_pair(x: float, z: float) -> tuple[float, float]:
    return (float(x), float(z))


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _keys(x: Any, expected: set[str], label: str) -> dict:
    if not isinstance(x, dict) or set(x) != expected:
        raise ModelError(f'{label} unexpected keys')
    return x


def validate_contract(doc: Any) -> dict:
    _keys(doc, {'format', 'game_id', 'work_id', 'release_id', 'baseline_commit',
                'baseline_file_sha1', 'arena', 'baseline', 'candidate'}, 'contract')
    if doc['format'] != 'P0D_S1_BALANCE_CONTRACT_V1' or doc['game_id'] != 'TRAP_RAIDERS' or \
       doc['work_id'] != 'p0d-siege-v19' or doc['release_id'] != 'P0D-S1-KIDS-RC01' or \
       doc['baseline_commit'] != SOURCE_SHA:
        raise ModelError('contract provenance identity changed')
    if not isinstance(doc['baseline_file_sha1'], dict) or len(doc['baseline_file_sha1']) != 3 or \
       any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 40 or
           any(ch not in '0123456789abcdef' for ch in v)
           for k, v in doc['baseline_file_sha1'].items()):
        raise ModelError('baseline Git blob evidence invalid')
    arena = _keys(doc['arena'], {
        'spawn_x_abs', 'egg_x_abs', 'egg_z', 'score_x_abs', 'score_z',
        'enemy_core_x_abs', 'enemy_core_z', 'interaction_distance',
        'castle_reach', 'prompt_hold_seconds', 'captures_to_win'}, 'arena')
    signed_coordinates = ('egg_z', 'score_z', 'enemy_core_z')
    for key in arena:
        if key not in signed_coordinates:
            _positive_number(arena[key], 'arena.' + key,
                             allow_zero=key == 'prompt_hold_seconds')
    # z may be signed; must remain a finite real coordinate.
    for key in signed_coordinates:
        value = arena[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ModelError('arena coordinate invalid: ' + key)
    if type(arena['captures_to_win']) is not int or arena['captures_to_win'] not in (1, 2, 3):
        raise ModelError('captures_to_win must be 1, 2 or 3 for supported analytic model')
    if arena['interaction_distance'] >= min(arena['spawn_x_abs'], arena['egg_x_abs']):
        raise ModelError('interaction radius exceeds supported arena geometry')
    for name in ('baseline', 'candidate'):
        p = _keys(doc[name], {'castle_hp', 'castle_attack_damage', 'attack_cooldown_seconds',
                              'role_walk_speed', 'match_seconds'}, name)
        if type(p['castle_hp']) is not int or p['castle_hp'] <= 0:
            raise ModelError(f'{name}.castle_hp positive integer required')
        if type(p['match_seconds']) is not int or p['match_seconds'] <= 0:
            raise ModelError(f'{name}.match_seconds positive integer required')
        _positive_number(p['attack_cooldown_seconds'], name + '.attack_cooldown_seconds')
        for field in ('castle_attack_damage', 'role_walk_speed'):
            mp = _keys(p[field], set(ALLOWED_ROLES), name+'.'+field)
            for role in ALLOWED_ROLES:
                _positive_number(mp[role], name+'.'+field+'.'+role)
        if p['castle_attack_damage']['GUARDIAN'] > p['castle_attack_damage']['RAIDER']:
            raise ModelError('guardian must not unexpectedly become higher castle attack role')
    return doc


def _geometry(a: dict, team: str) -> tuple[tuple, tuple, tuple, tuple]:
    if team not in ('RED', 'BLUE'):
        raise ModelError('unknown team')
    side = -1 if team == 'RED' else 1
    # Opposite team's egg and castle; team-side scoring pad.
    spawn = _pos_pair(side * a['spawn_x_abs'], 0)
    egg = _pos_pair(-side * a['egg_x_abs'], a['egg_z'])
    score = _pos_pair(side * a['score_x_abs'], a['score_z'])
    core = _pos_pair(-side * a['enemy_core_x_abs'], a['enemy_core_z'])
    return spawn, egg, score, core


def calculate(a: dict, p: dict, team: str, role: str, *, walk_multiplier: float = 1.0,
              cooldown_multiplier: float = 1.0, prompt_multiplier: float = 1.0) -> dict:
    if role not in ALLOWED_ROLES:
        raise ModelError('role invalid')
    for name, v in [('walk_multiplier',walk_multiplier),('cooldown_multiplier',cooldown_multiplier),
                    ('prompt_multiplier',prompt_multiplier)]:
        _positive_number(v,name)
    walk = _positive_number(p['role_walk_speed'][role], 'walk_speed') * walk_multiplier
    cool = _positive_number(p['attack_cooldown_seconds'], 'cooldown') * cooldown_multiplier
    damage = _positive_number(p['castle_attack_damage'][role], 'castle_damage')
    hp = _positive_number(p['castle_hp'], 'castle_hp')
    reach = _positive_number(a['castle_reach'], 'castle_reach')
    radius = _positive_number(a['interaction_distance'], 'interaction_distance')
    hold = _positive_number(a['prompt_hold_seconds'], 'hold', allow_zero=True) * prompt_multiplier
    caps = a['captures_to_win']
    spawn, egg, score, core = _geometry(a,team)
    required_hits = math.ceil(hp / damage)
    # First attack can be immediate after reaching the enemy core (resetRound sets lastAttack=-inf).
    castle_walk_lower_bound = max(0.0, _distance(spawn,core) - reach) / walk
    castle_attack_lower_bound = max(0, required_hits-1) * cool
    castle_lower_bound = castle_walk_lower_bound + castle_attack_lower_bound
    # Two separate capture loops, each egg resets to its base after scoring.
    prev, prev_radius = spawn, 0.0
    segments = []
    for _ in range(caps):
        for current in (egg,score):
            # Lower bound for walking from any point in radius-prev disk to
            # any point in radius-current disk. Independent segment optima
            # need not be jointly feasible -> optimistic lower bound.
            needed = max(0.0,_distance(prev,current)-prev_radius-radius)
            segments.append(needed/walk)
            prev,prev_radius=current,radius
    eggs_lower_bound = sum(segments)+2*caps*hold
    return {
        'team': team, 'role': role, 'hits_required': required_hits,
        'castle_walk_lb_s': round(castle_walk_lower_bound,5),
        'castle_attack_lb_s': round(castle_attack_lower_bound,5),
        'castle_total_lb_s': round(castle_lower_bound,5),
        'egg_total_lb_s': round(eggs_lower_bound,5),
        'castle_to_egg_lb_ratio': round(castle_lower_bound/eggs_lower_bound,5),
        'assumptions': 'no_enemy_no_obstacles_no_latency_2d_optimistic_geometry'
    }


def report(contract: dict) -> dict:
    validate_contract(contract)
    results = {}
    for variant in ('baseline','candidate'):
        results[variant]={team:{role:calculate(contract['arena'],contract[variant],team,role)
                                        for role in ALLOWED_ROLES}
                            for team in ('RED','BLUE')}
    return {'format':'P0D_S1_ANALYTIC_LOWER_BOUND_REPORT_V1',
            'baseline_commit':contract['baseline_commit'], 'scenarios':results,
            'limitations': ['Not simultaneous physically achievable routes',
                            'No defender, obstacle, packet loss, respawn, lag or NPC effects',
                            'Cannot establish empirical player balance, fun, retention or monetization',
                            'Proposed profile optional OFF; #220 sole integration owner']}


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--contract',type=Path,default=Path(__file__).resolve().parents[1]/'data/source_contract.json')
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    result=report(json.loads(args.contract.read_text(encoding='utf-8')))
    data=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(data,encoding='utf-8')
    else:
        print(data,end='')


if __name__=='__main__':
    main()
