"""Independent Python behavioral oracle for isolated D08->D07 shape mapper.

Reference only; models decisions, not Roblox Luau execution or server source attestation.
"""
import math
import re


def valid_id(x):
    return isinstance(x, str) and 1 <= len(x) <= 64 and re.fullmatch(r"[A-Za-z0-9_-]+", x) is not None


def num(x, low, high):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and low <= x <= high


class Mapper:
    def __init__(self, read_round, start_combined, abort_combined, *, enabled=False, approved=False):
        self.read_round = read_round
        self.start_combined = start_combined
        self.abort_combined = abort_combined
        self.enabled = enabled is True and approved is True
        self.disabled_reason = None
        self.in_callback = False
        self.attested = None
        self.attempted = set()
        self.last_now = None

    def is_canonical(self, activation):
        return self.enabled and self.in_callback and activation is self.attested

    def _round(self):
        try:
            r = self.read_round()
        except Exception:
            return None
        if not isinstance(r, dict) or not valid_id(r.get('matchId')) or r.get('stage') not in ('S1', 'S3'):
            return None
        if not num(r.get('epoch'), 0, 1023) or int(r['epoch']) != r['epoch']:
            return None
        if not num(r.get('now'), 0, 1e12) or not num(r.get('deadline'), 0, 1e12):
            return None
        if r['deadline'] <= r['now'] or r.get('active') is not True:
            return None
        # Frozen-value evidence, not an alias to a mutable server table.
        return {k:r[k] for k in ('matchId','stage','epoch','now','deadline','active')}

    def handle(self, e):
        if not self.enabled:
            return False, self.disabled_reason or 'DISABLED_DEFAULT'
        if self.in_callback:
            return False, 'REENTRANT_CALLBACK'
        if not isinstance(e, dict) or e.get('phase') != 'ACTIVATE' or e.get('kind') != 'BOSS' or e.get('subtype') != 'GOROGAN' or not valid_id(e.get('matchId')) or e.get('stage') not in ('S1','S3') or not num(e.get('epoch'),0,1023) or int(e['epoch']) != e['epoch'] or not num(e.get('validUntil'),0,1e12):
            return False, 'INVALID_D08_ENVELOPE'
        s = self._round()
        if not s or e['matchId'] != s['matchId'] or e['stage'] != s['stage'] or e['epoch'] != s['epoch'] or e['validUntil'] <= s['now']+2 or e['validUntil'] > s['deadline']:
            return False, 'SERVER_ROUND_MISMATCH'
        if self.last_now is not None and s['now'] < self.last_now:
            self.enabled = False
            self.disabled_reason = 'SERVER_CLOCK_REVERSED'
            return False, self.disabled_reason
        self.last_now = s['now']
        key = (s['matchId'],s['epoch'])
        if key in self.attempted:
            return False, 'EVENT_REPLAY'
        if len(self.attempted) >= 128:
            self.enabled = False
            self.disabled_reason = 'ATTEMPT_CAP_REACHED'
            return False, self.disabled_reason
        self.attempted.add(key)
        activation = {'event':'ACTIVATE','kind':'BOSS','subtype':'GOROGAN','matchId':s['matchId'],'untilAt':e['validUntil']}
        self.in_callback = True
        self.attested = activation
        try:
            try:
                started, reason = self.start_combined(activation)
                ok = True
            except Exception:
                started, reason, ok = False, 'EXCEPTION', False
        finally:
            self.in_callback = False
            self.attested = None
        fresh = self._round()
        same = (fresh is not None and fresh['matchId']==s['matchId'] and fresh['stage']==s['stage']
                and fresh['epoch']==s['epoch'] and fresh['deadline']==s['deadline']
                and fresh['now']>=s['now'] and fresh['active'] is True)
        if not ok or started is not True or not same or (fresh is not None and fresh['now'] >= activation['untilAt']):
            try:
                aborted = self.abort_combined(s['matchId']) is True
            except Exception:
                aborted = False
            self.enabled = False
            self.disabled_reason = 'START_FAILED_OR_STALE' if aborted else 'CRITICAL_ABORT_NOT_CONFIRMED'
            return False, self.disabled_reason
        self.last_now = fresh['now']
        return True, 'DELIVERED_ONCE'
