"""Independent Python mirror of pure server round-time->client TTL transport format."""
from .client_policy import valid_id, valid_number, SCALES

def build(snapshot, elapsed):
    if type(snapshot) is not dict or not valid_id(snapshot.get('matchId')) or not valid_id(snapshot.get('eventId')) or not valid_number(elapsed) or elapsed < 0:
        return None, 'INVALID_SOURCE'
    status = snapshot.get('status')
    if status == 'ACTIVE':
        kind = snapshot.get('kind')
        if kind not in SCALES or snapshot.get('scaleMilli') != SCALES[kind] or not valid_number(snapshot.get('expiresAt')) or snapshot['expiresAt'] < 0:
            return None,'INVALID_ACTIVE'
        ts=snapshot.get('targets')
        if type(ts) is not list or not 1 <= len(ts) <= 16 or (kind=='GIANT_ONE' and len(ts)!=1) or any(not valid_id(v) for v in ts) or len(set(ts))!=len(ts):
            return None,'INVALID_TARGETS'
        ttl=snapshot['expiresAt']-elapsed
        if not 0 < ttl <= 8:return None,'INVALID_ACTIVE_TTL'
        return {'matchId':snapshot['matchId'],'eventId':snapshot['eventId'],'status':'ACTIVE','kind':kind,'targets':sorted(ts),'scaleMilli':SCALES[kind],'remainingSeconds':ttl},None
    if status in ('EXPIRED','CLOSED'):
        ts=snapshot.get('targets',[])
        if type(ts) is not list or ts:return None,'INVALID_TERMINAL'
        return {'matchId':snapshot['matchId'],'eventId':snapshot['eventId'],'status':status,'kind':snapshot.get('kind'),'targets':[], 'scaleMilli':1000,'remainingSeconds':0},None
    return None,'UNEXPECTED_STATUS'
