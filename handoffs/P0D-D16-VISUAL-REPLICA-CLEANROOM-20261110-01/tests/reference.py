"""Python behavioral reference for original D16 visual replica cleanroom.
Not executable Luau and not real Roblox integration evidence.
"""
import math


def finite(v):
    return type(v) in (int, float) and math.isfinite(v) and abs(v) < 1e12


def valid_id(v):
    return type(v) is str and 1 <= len(v) <= 96


def nonneg(v):
    return finite(v) and v >= 0 and int(v) == v


class ServerBridge:
    def __init__(self):
        self.round = None
        self.seq = -1

    def project(self, s):
        if not isinstance(s, dict) or s.get('server_authorized') is not True or s.get('event_approved') is not True:
            return {'kind': 'REJECTED'}
        if s.get('event_name') not in ('GIANT_ONE', 'MINI_ALL'):
            return {'kind': 'REJECTED'}
        if not valid_id(s.get('match_id')) or not nonneg(s.get('epoch')) or not nonneg(s.get('sequence')):
            return {'kind': 'REJECTED'}
        elapsed = s.get('server_round_elapsed_seconds')
        expires = s.get('expires_at_round_seconds')
        if not finite(elapsed) or not finite(expires) or elapsed < 0:
            return {'kind': 'REJECTED'}
        remain = expires - elapsed
        if remain <= 0 or remain > 8:
            return {'kind': 'REJECTED'}
        ids = s.get('target_user_ids')
        if not isinstance(ids, list) or not 1 <= len(ids) <= 8 or any(not nonneg(x) or x <= 0 for x in ids) or len(set(ids)) != len(ids):
            return {'kind': 'REJECTED'}
        if s['event_name'] == 'GIANT_ONE' and len(ids) != 1:
            return {'kind': 'REJECTED'}
        key = (s['match_id'], s['epoch'])
        if self.round == key and s['sequence'] <= self.seq:
            return {'kind': 'REJECTED'}
        self.round, self.seq = key, s['sequence']
        return {'kind': 'DISPLAY', 'from_server_bridge': True,
                'source_clock': 'SERVER_ROUND_ELAPSED',
                'event_name': s['event_name'], 'match_id': s['match_id'],
                'epoch': s['epoch'], 'sequence': s['sequence'],
                'target_user_ids': list(ids),
                'remaining_seconds': remain,
                'scale_factor': 1.6 if s['event_name'] == 'GIANT_ONE' else 0.7}


class ClientPolicy:
    def __init__(self):
        self.active = False
        self.previous = None
        self.previous_seq = -1
        self.targets = set()
        self.match = None
        self.epoch = None
        self.expires = 0
        self.last_local = None
        self.scale = 1.0
        self.max_avatars = 0
        self.max_parts = 0

    def clear(self):
        self.active = False
        self.targets.clear()
        self.match = self.epoch = self.last_local = None

    def begin(self, p, local_time, reduced_motion):
        if not isinstance(p, dict) or p.get('kind') != 'DISPLAY' or p.get('from_server_bridge') is not True:
            return 'REJECTED'
        if p.get('source_clock') != 'SERVER_ROUND_ELAPSED' or self.active or not finite(local_time) or type(reduced_motion) is not bool:
            return 'REJECTED'
        event = p.get('event_name')
        if event not in ('GIANT_ONE', 'MINI_ALL') or not valid_id(p.get('match_id')) or not nonneg(p.get('epoch')) or not nonneg(p.get('sequence')):
            return 'REJECTED'
        if p.get('scale_factor') != (1.6 if event == 'GIANT_ONE' else 0.7):
            return 'REJECTED'
        remaining = p.get('remaining_seconds')
        if not finite(remaining) or remaining <= 0 or remaining > 8:
            return 'REJECTED'
        ids = p.get('target_user_ids')
        if not isinstance(ids, list) or not 1 <= len(ids) <= 8 or any(not nonneg(x) or x <= 0 for x in ids) or len(set(ids)) != len(ids):
            return 'REJECTED'
        if event == 'GIANT_ONE' and len(ids) != 1:
            return 'REJECTED'
        key = (p['match_id'], p['epoch'])
        if self.previous == key and p['sequence'] <= self.previous_seq:
            return 'REJECTED'
        self.previous, self.previous_seq = key, p['sequence']
        self.active, self.targets = True, set(ids)
        self.match, self.epoch = key
        self.expires, self.last_local = local_time + remaining, local_time
        self.scale = p['scale_factor']
        self.max_avatars, self.max_parts = (4, 6) if reduced_motion else (8, 18)
        return 'START'

    def frame(self, local_time, match, epoch, viewer, avatars):
        if not self.active:
            return ('IDLE', [])
        if not finite(local_time) or local_time < self.last_local or local_time >= self.expires or (match, epoch) != (self.match, self.epoch):
            self.clear()
            return ('CLEAR', [])
        if not isinstance(viewer, tuple) or len(viewer) != 3 or any(not finite(x) for x in viewer) or not isinstance(avatars, list):
            self.clear()
            return ('CLEAR', [])
        self.last_local = local_time
        seen, result = set(), []
        for u in avatars:
            if len(result) >= self.max_avatars:
                break
            if not isinstance(u, dict) or u.get('user_id') not in self.targets or u['user_id'] in seen:
                continue
            pos = u.get('position')
            if not isinstance(pos, tuple) or len(pos) != 3 or any(not finite(x) for x in pos):
                continue
            if sum((a-b)**2 for a,b in zip(viewer,pos)) <= 90**2:
                result.append(u['user_id'])
                seen.add(u['user_id'])
        return ('FRAME', result)
