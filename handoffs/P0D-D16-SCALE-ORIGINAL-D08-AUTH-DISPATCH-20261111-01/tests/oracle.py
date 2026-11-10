"""Independent Python behavioral specification for an optional ORIGINAL-D16/D08 bridge.

Synthetic callbacks only: deliberately no Roblox native runtime claims.
"""
from copy import deepcopy
from math import isfinite
import re

WEATHER = {'WX01_METEOR', 'WX02_SMALL', 'WX03_CROWN', 'WX04_GLIDE', 'WX05_CLOCK'}
STAGE = {'S1', 'S2', 'S3', 'S4'}
ID = re.compile(r'^[A-Za-z0-9_.-]{1,96}$')


def ident(s):
    return isinstance(s, str) and ID.fullmatch(s) is not None


def time(v):
    return isinstance(v, (float, int)) and not isinstance(v, bool) and isfinite(v) and 0 <= v <= 1e12


class OriginalCore:
    """Fake API of exact original, not an implementation of the real Luau code."""
    def __init__(self):
        self.calls = []

    def new(self, match):
        self.calls.append(('new', match))
        assert ident(match)
        return dict(matchId=match, status='IDLE', used=False, targets=[], lastTime=0)

    def begin(self, s, match, event, kind, actor, roster, now):
        self.calls.append(('begin', match, event, kind, actor, tuple(roster), now))
        if match != s['matchId'] or s['used'] or s['status'] == 'CLOSED' or not ident(event):
            return False, 'INVALID_CONTEXT'
        if kind not in ('GIANT_ONE', 'MINI_ALL') or len(roster) < 1 or len(roster) > 16:
            return False, 'INVALID_INPUT'
        if kind == 'GIANT_ONE' and actor not in roster:
            return False, 'INVALID_ACTOR'
        if kind == 'MINI_ALL' and actor is not None:
            return False, 'ACTOR_NOT_APPLICABLE'
        s.update(status='ACTIVE', used=True, targets=[actor] if kind == 'GIANT_ONE' else sorted(roster),
                 lastTime=now, expiresAt=now + 8, kind=kind, eventId=event)
        return True, 'STARTED'

    def advance(self, s, match, now):
        self.calls.append(('advance', match, now))
        if match != s['matchId'] or now < s['lastTime']:
            return False, 'INVALID_TIME'
        s['lastTime'] = now
        if now >= s['expiresAt'] or not s['targets']:
            s['status'] = 'EXPIRED'
            s['targets'] = []
        return True, s['status']

    def leave(self, s, match, actor):
        self.calls.append(('leave', match, actor))
        if match != s['matchId']:
            return False, 'STALE_MATCH'
        s['targets'] = [p for p in s['targets'] if p != actor]
        if not s['targets']:
            s['status'] = 'EXPIRED'
        return True, s['status']

    def close(self, s, match):
        self.calls.append(('close', match))
        if match != s['matchId']:
            return False, 'STALE_MATCH'
        s['status'] = 'CLOSED'
        s['targets'] = []
        return True, 'CLOSED'

    def snapshot(self, s, match):
        self.calls.append(('snapshot', match))
        return dict(matchId=match, eventId=s.get('eventId'), status=s['status'], kind=s.get('kind'),
                    scaleMilli={'GIANT_ONE': 1600, 'MINI_ALL': 700}.get(s.get('kind'), 1000),
                    targets=list(s['targets']), expiresAt=s.get('expiresAt'))


class Harness:
    def __init__(self, mapping=None, approved=True, enabled=True):
        self.clock = 100.0
        self.state = dict(matchId='m1', epoch=1, stage='S1', startedAt=80., deadline=140., active=True)
        self.roster = ['alice', 'bob']
        self.actor = 'alice'
        self.authentic = True
        self.authentic_cleanup = True
        self.id = 'serverEvent1'
        self.hooks = {}
        self.core = OriginalCore()
        self.gate = OracleGate(self, mapping if mapping is not None else {'WX02_SMALL': 'MINI_ALL'},
                               approved=approved, enabled=enabled)

    def call(self, name):
        fn = self.hooks.pop(name, None)
        if fn:
            fn()

    def round(self):
        self.call('round')
        return {**deepcopy(self.state), 'now': self.clock}

    def envelope(self, subtype='WX02_SMALL'):
        return dict(matchId='m1', epoch=1, stage='S1', phase='ACTIVATE', kind='WEATHER',
                    subtype=subtype, validUntil=135.)

    def cleanup(self):
        return dict(matchId='m1', epoch=1, stage='S1', kind='WEATHER', subtype='WX02_SMALL')


class OracleGate:
    def __init__(self, env, mapping, approved=True, enabled=True):
        if any(k not in WEATHER or v not in ('MINI_ALL', 'GIANT_ONE') for k, v in mapping.items()):
            raise ValueError('UNAPPROVED_MAP_VALUE')
        self.env, self.map = env, dict(mapping)
        self.enabled = bool(enabled and approved)
        self.stopped = False
        self.active = None
        self.pending = None
        self.busy = False
        self.generation = 0
        self.seen = set()
        self.last_now = 0.

    def round(self):
        r = self.env.round()
        if not (isinstance(r, dict) and ident(r.get('matchId')) and r.get('stage') in STAGE
                and time(r.get('now')) and time(r.get('startedAt')) and time(r.get('deadline'))
                and r['startedAt'] <= r['now'] and r['deadline'] > r['startedAt']
                and time(r.get('epoch')) and r['epoch'] % 1 == 0 and r['epoch'] <= 1e6
                and isinstance(r.get('active'), bool)):
            return None
        return r

    @staticmethod
    def same_round(a, b):
        return all(a[k] == b[k] for k in ('matchId', 'stage', 'epoch', 'startedAt', 'deadline'))

    def close(self):
        if not self.active:
            return True
        a = self.active
        self.active = None
        ok, _ = self.env.core.close(a['state'], a['round']['matchId'])
        if not ok:
            self.enabled = False
        return ok

    def activate(self, e):
        if not self.enabled or self.stopped:
            return False, 'DISABLED_DEFAULT'
        if self.busy:
            return False, 'REENTRANT_ACTIVATION'
        if self.active:
            return False, 'ALREADY_ACTIVE'
        if not (isinstance(e, dict) and e.get('phase') == 'ACTIVATE'
                and e.get('kind') == 'WEATHER' and e.get('subtype') in WEATHER
                and ident(e.get('matchId')) and e.get('stage') in STAGE
                and time(e.get('epoch')) and e['epoch'] % 1 == 0 and time(e.get('validUntil'))):
            return False, 'INVALID_D08_ENVELOPE'
        fields = {k: e[k] for k in ('matchId', 'stage', 'epoch', 'subtype', 'validUntil', 'phase', 'kind')}
        def same_envelope():
            return all(e.get(k) == v for k, v in fields.items())
        kind = self.map.get(e['subtype'])
        if not kind:
            return False, 'OWNER_MAPPING_NOT_APPROVED'
        first = self.round()
        if not (first and first['active'] and first['now'] < first['deadline']
                and first['now'] < e['validUntil'] and first['now'] >= self.last_now
                and all(first[k] == e[k] for k in ('matchId', 'stage', 'epoch'))):
            return False, 'STALE_OR_INACTIVE_ROUND'
        key = (first['matchId'], first['epoch'])
        if key in self.seen or len(self.seen) >= 128:
            return False, 'DUPLICATE_OR_ROUND_LIMIT'
        self.seen.add(key)
        self.generation += 1
        ticket = self.generation
        self.busy = True
        self.pending = {k: first[k] for k in ('matchId', 'epoch', 'stage')}
        def finish(ok, reason):
            self.busy = False
            if self.generation == ticket:
                self.pending = None
            return ok, reason
        self.env.call('auth')
        if not self.env.authentic:
            return finish(False, 'NOT_AUTHENTIC_D08_ENVELOPE')
        self.env.call('roster')
        roster = self.env.roster
        if not (isinstance(roster, list) and 1 <= len(roster) <= 16 and
                all(ident(p) for p in roster) and len(set(roster)) == len(roster)):
            return finish(False, 'INVALID_TRUSTED_ROSTER')
        actor = None
        if kind == 'GIANT_ONE':
            self.env.call('actor')
            actor = self.env.actor
            if not ident(actor) or actor not in roster:
                return finish(False, 'INVALID_SERVER_ACTOR')
        self.env.call('event_id')
        event_id = self.env.id
        if not ident(event_id):
            return finish(False, 'INVALID_SERVER_EVENT_ID')
        fresh = self.round()
        if not (self.enabled and not self.stopped and self.generation == ticket
                and fresh and self.same_round(first, fresh) and fresh['active']
                and fresh['now'] >= max(first['now'], self.last_now)
                and fresh['now'] < min(fresh['deadline'], fields['validUntil'])
                and same_envelope()):
            return finish(False, 'REVOKED_OR_CHANGED_DURING_CALLBACK')
        self.env.call('auth2')
        if not self.env.authentic:
            return finish(False, 'AUTHORITY_RECHECK_FAILED')
        last = self.round()
        if not (self.enabled and not self.stopped and self.generation == ticket
                and last and self.same_round(first, last) and last['active']
                and last['now'] >= max(fresh['now'], self.last_now)
                and last['now'] < min(last['deadline'], fields['validUntil'])
                and same_envelope()):
            return finish(False, 'REVOKED_AFTER_PROVENANCE_RECHECK')
        self.last_now = last['now']
        state = self.env.core.new(first['matchId'])
        ok, msg = self.env.core.begin(state, first['matchId'], event_id, kind,
                                      actor, list(roster), last['now'])
        if not ok:
            self.enabled = False
            return finish(False, 'CORE_BEGIN_FAILED')
        if self.generation != ticket or not self.enabled or self.stopped:
            self.env.core.close(state, first['matchId'])
            return finish(False, 'REVOKED_AFTER_BEGIN')
        self.active = {'round': last, 'state': state, 'kind': kind,
                       'eventId': event_id, 'eventValidUntil': fields['validUntil']}
        return finish(True, msg)

    def cleanup(self, e):
        self.env.call('cleanup_auth')
        if not (isinstance(e, dict) and ident(e.get('matchId')) and e.get('stage') in STAGE
                and time(e.get('epoch')) and e['epoch'] % 1 == 0
                and self.env.authentic_cleanup):
            return False, 'UNTRUSTED_CLEANUP'
        fields = ('matchId', 'stage', 'epoch')
        if not (self.active and all(self.active['round'][k] == e[k] for k in fields)
                or self.pending and all(self.pending[k] == e[k] for k in fields)):
            return False, 'STALE_CLEANUP'
        self.generation += 1
        self.pending = None
        ok = self.close()
        return ok, 'CLOSED' if ok else 'CORE_CLOSE_FAILED'

    def tick(self):
        if not self.enabled or self.stopped:
            return False, 'DISABLED_DEFAULT'
        if not self.active:
            return False, 'NO_ACTIVE_EFFECT'
        a, ticket = self.active, self.generation
        r = self.round()
        if not (self.enabled and not self.stopped and self.generation == ticket
                and self.active is a and r and self.same_round(r, a['round'])
                and r['active'] and r['now'] >= max(a['round']['now'], self.last_now)
                and r['now'] < r['deadline'] and r['now'] < a['eventValidUntil']):
            self.generation += 1
            self.close()
            return False, 'ROUND_INVALID_OR_EXPIRED'
        self.last_now = r['now']
        ok, status = self.env.core.advance(a['state'], a['round']['matchId'], r['now'])
        if not ok:
            self.enabled = False
            self.close()
            return False, 'CORE_ADVANCE_FAILED'
        if status != 'ACTIVE':
            self.close()
            return True, 'EFFECT_ENDED'
        return True, 'ACTIVE'

    def leave(self, pid):
        if not self.enabled or not self.active or not ident(pid):
            return False, 'INVALID_TRUSTED_LEAVE'
        tick_ok, tick_status = self.tick()
        if not tick_ok or tick_status != 'ACTIVE':
            return False, 'ROUND_OR_EFFECT_NOT_ACTIVE'
        a = self.active
        ok, status = self.env.core.leave(a['state'], a['round']['matchId'], pid)
        if not ok:
            self.enabled = False
            self.close()
            return False, 'CORE_LEAVE_FAILED'
        if status != 'ACTIVE':
            self.close()
        return True, status

    def snapshot(self):
        if not self.enabled or self.stopped or not self.active:
            return None, 'NO_ACTIVE_EFFECT'
        a, ticket = self.active, self.generation
        r = self.round()
        if not (self.enabled and not self.stopped and self.generation == ticket
                and self.active is a and r and self.same_round(r, a['round'])
                and r['active'] and r['now'] >= max(a['round']['now'], self.last_now)
                and r['now'] < r['deadline'] and r['now'] < a['eventValidUntil']):
            self.generation += 1
            self.close()
            return None, 'ROUND_INVALID_OR_EXPIRED'
        v = self.env.core.snapshot(a['state'], a['round']['matchId'])
        if v['status'] != 'ACTIVE' or not time(v['expiresAt']) or r['now'] >= v['expiresAt']:
            self.close()
            return None, 'EFFECT_EXPIRED_OR_INACTIVE'
        self.last_now = r['now']
        return deepcopy(v), None

    def stop(self):
        self.stopped = True
        self.enabled = False
        self.generation += 1
        self.pending = None
        ok = self.close()
        return ok, 'STOPPED' if ok else 'CORE_CLOSE_FAILED'
