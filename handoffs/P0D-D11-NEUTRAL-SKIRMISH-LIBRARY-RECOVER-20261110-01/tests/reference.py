"""Offline behavioral model for the independent v43A Luau reference module.
No claims about Luau compilation or Studio are made by running this file.
"""
import math
from copy import deepcopy

MAX_UNITS, MAX_CANDIDATES, RADIUS = 2, 64, 14
CAPTURE, ALLY, COOLDOWN = 3, 8, 4
TEAMS = {'BLUE', 'RED'}
KINDS = {'BEAST', 'ZOMBIE'}


def finite(n):
    return type(n) in (int, float) and math.isfinite(n)


def valid_id(v):
    return isinstance(v, str) and 1 <= len(v.encode('utf-8')) <= 96


def new(match_id, items, started_at=0):
    if not valid_id(match_id) or not finite(started_at):
        return None, 'INVALID_MATCH'
    if not isinstance(items, list) or not (1 <= len(items) <= MAX_UNITS):
        return None, 'INVALID_UNITS'
    units = {}
    for item in items:
        if (not isinstance(item, dict) or not valid_id(item.get('id'))
                or item.get('kind') not in KINDS or item['id'] in units):
            return None, 'INVALID_UNIT'
        units[item['id']] = dict(id=item['id'], kind=item['kind'], faction='NEUTRAL',
                                 pendingTeam=None, progress=0, expiresAt=0,
                                 blockedUntil=started_at)
    return dict(matchId=match_id, order=sorted(units), units=units,
                lastAt=started_at, closed=False), None


def candidate_team(candidates):
    if not isinstance(candidates, list) or len(candidates) > MAX_CANDIDATES:
        return None
    seen, found = set(), None
    for p in candidates:
        if not isinstance(p, dict) or not valid_id(p.get('playerId')) or p['playerId'] in seen:
            return None
        seen.add(p['playerId'])
        if (p.get('alive') is True and p.get('wantsCapture') is True
                and p.get('carryingEgg') is not True and p.get('team') in TEAMS
                and finite(p.get('distance')) and 0 <= p['distance'] <= RADIUS):
            if found is not None and found != p['team']:
                return None
            found = p['team']
    return found


def step(previous, at, observations):
    if (not isinstance(previous, dict) or previous['closed'] or not finite(at)
            or not finite(previous['lastAt']) or at < previous['lastAt']
            or not isinstance(observations, dict)):
        return previous, [], 'REJECTED_STEP'
    elapsed = min(at - previous['lastAt'], 1)
    ns = deepcopy(previous)
    ns['lastAt'] = at
    events = []
    counts = dict(BLUE=0, RED=0)
    for id in ns['order']:
        u = ns['units'][id]
        if u['faction'] in TEAMS and at >= u['expiresAt']:
            events.append(dict(type='EXPIRED', unitId=id, previousTeam=u['faction']))
            u.update(faction='NEUTRAL', blockedUntil=at + COOLDOWN,
                     pendingTeam=None, progress=0)
        if u['faction'] in TEAMS:
            counts[u['faction']] += 1
    for id in ns['order']:
        u = ns['units'][id]
        if u['faction'] == 'NEUTRAL':
            team = candidate_team(observations.get(id) or []) if at >= u['blockedUntil'] else None
            if team is None or counts[team] >= 1:
                u.update(pendingTeam=None, progress=0)
            else:
                if u['pendingTeam'] != team:
                    u.update(pendingTeam=team, progress=0)
                u['progress'] = min(CAPTURE, u['progress'] + elapsed)
                if u['progress'] >= CAPTURE:
                    u.update(faction=team, expiresAt=at + ALLY,
                             progress=0, pendingTeam=None)
                    counts[team] += 1
                    events.append(dict(type='CAPTURED', unitId=id, kind=u['kind'],
                                       team=team, expiresAt=u['expiresAt']))
    return ns, events, None


def end_round(s, at):
    if not isinstance(s, dict) or s['closed'] or not finite(at) or at < s['lastAt']:
        return s, [], 'REJECTED_END'
    ns = deepcopy(s)
    ns['closed'] = True
    ns['lastAt'] = at
    for u in ns['units'].values():
        u.update(faction='NEUTRAL', pendingTeam=None, progress=0, expiresAt=0)
    return ns, [], None


def hostile(a, b, ka=None, kb=None):
    if a == 'NEUTRAL' and b == 'NEUTRAL':
        return ka in KINDS and kb in KINDS and ka != kb
    if a == 'NEUTRAL': return b in TEAMS
    if b == 'NEUTRAL': return a in TEAMS
    return a in TEAMS and b in TEAMS and a != b


def actor(player_id='p', team='BLUE', distance=4, alive=True, wants=True, egg=False):
    return dict(playerId=player_id, team=team, distance=distance, alive=alive,
                wantsCapture=wants, carryingEgg=egg)
