"""Independent pure state oracle of D14 client-only non-authoritative vehicle render packets."""
from __future__ import annotations
import math
import re
from copy import deepcopy

ID = re.compile(r"[A-Za-z0-9_-]{1,32}\Z", re.ASCII)
KINDS = {"START", "UPDATE", "STOP", "ROUND_END"}
VALID = {"CART", "RAFT"}
MAX = 4


def _ident(value):
    return isinstance(value, str) and ID.fullmatch(value) is not None


def _int(value, lo, hi):
    return type(value) is int and lo <= value <= hi


def _coord(value, bound=8192):
    return type(value) in (float, int) and math.isfinite(value) and abs(value) <= bound


class Policy:
    def __init__(self, round_id):
        if not _ident(round_id):
            raise ValueError('bad round')
        self.round_id = round_id
        self.seq = -1
        self.items = {}
        self.closed = False

    def ingest(self, packet):
        if self.closed or not isinstance(packet, dict) or packet.get('roundId') != self.round_id:
            return []
        seq = packet.get('seq')
        if not _int(seq, 0, 2147483647) or seq <= self.seq:
            return []
        kind = packet.get('kind')
        if kind == 'ROUND_END':
            self.seq = seq
            self.items.clear()
            self.closed = True
            return [{'op': 'CLEAR'}]
        if kind not in {'START', 'UPDATE', 'STOP'} or not _ident(packet.get('vehicleId')):
            return []
        vid = packet['vehicleId']
        if kind == 'STOP':
            self.seq = seq
            old = self.items.pop(vid, None)
            return [{'op': 'REMOVE', 'vehicleId': vid}] if old else []
        if packet.get('vehicleType') not in VALID or packet.get('team') not in ('BLUE', 'RED'):
            return []
        if type(packet.get('driverOccupied')) is not bool or type(packet.get('passengerOccupied')) is not bool:
            return []
        if not _int(packet.get('remainingMs'), 1, 20000):
            return []
        if any(not _coord(packet.get(k)) for k in ('x','y','z','yawDeg')):
            return []
        if abs(packet['yawDeg']) > 360:
            return []
        old = self.items.get(vid)
        if kind == 'UPDATE' and old is None:
            return []
        if kind == 'START' and old is None and len(self.items) >= MAX:
            return []
        if old and (old['vehicleType'] != packet['vehicleType'] or old['team'] != packet['team']):
            return []
        content = {k:packet[k] for k in ('vehicleType','team','driverOccupied','passengerOccupied','x','y','z','yawDeg','remainingMs')}
        self.items[vid] = deepcopy(content)
        self.seq = seq
        return [{'op': 'SPAWN' if old is None else 'MOVE', 'vehicleId': vid, 'presentation':deepcopy(content)}]

    def close(self):
        if self.closed:
            return []
        self.closed = True
        self.items.clear()
        return [{'op': 'CLEAR'}]
