"""P0-D D17 offline privacy-first telemetry oracle. Not Roblox SDK or payment code.

Inputs must come from an authenticated SERVER recorder, never from client claims.
Session IDs are random, ephemeral, and must be rotated; no permanent user IDs.
"""
from collections import defaultdict
import math

ALLOWED_FIELDS={'event_id','session_id','round_id','timestamp','origin','event'}
TYPES={'session_start','round_start','round_end','rematch_click',
       'cosmetic_preview_open','shop_preview_open'}
ORIGINS={'studio','live'}


def sanitize(events):
    """Strict allowlist, dedupe event_id per origin, stable sorted events and fail closed.

    Any PII or suspicious payload is rejected; this is a reference model only.
    """
    out=[];seen=set()
    for e in events:
        if not isinstance(e,dict) or set(e)-ALLOWED_FIELDS or (ALLOWED_FIELDS-set(e)):
            raise ValueError('INVALID_EVENT_SCHEMA')
        if any(not isinstance(e[k],str) or not e[k] or len(e[k])>96
               for k in ('event_id','session_id','round_id','origin','event')):
            raise ValueError('INVALID_EVENT_ID')
        if e['origin'] not in ORIGINS or e['event'] not in TYPES:
            raise ValueError('INVALID_EVENT_TYPE')
        t=e['timestamp']
        if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or t<0:
            raise ValueError('INVALID_TIMESTAMP')
        key=(e['origin'],e['event_id'])
        if key not in seen:
            seen.add(key);out.append(e.copy())
    return sorted(out,key=lambda x:(x['origin'],x['timestamp'],x['event_id']))


def summarize(events,origin):
    """Compute session-only ratios; NEVER infer D1, sales, Robux or production KPI.

    A valid completed round must have a same-session round start at/before end.
    A rematch click is counted only for a session with a completed round.
    Studio and live observations remain separate to avoid fictitious business data.
    """
    if origin not in ORIGINS: raise ValueError('INVALID_ORIGIN')
    clean=sanitize(events)
    sessions=set();round_starts=defaultdict(list);round_ends=defaultdict(list)
    rematch=set();cosmetic=set();shop=set()
    for e in clean:
        if e['origin']!=origin:continue
        sid=e['session_id'];key=(sid,e['round_id']);kind=e['event']
        if kind=='session_start':sessions.add(sid)
        elif kind=='round_start':round_starts[key].append(e['timestamp'])
        elif kind=='round_end':round_ends[key].append(e['timestamp'])
        elif kind=='rematch_click':rematch.add(sid)
        elif kind=='cosmetic_preview_open':cosmetic.add(sid)
        elif kind=='shop_preview_open':shop.add(sid)
    started={sid for sid,rid in round_starts if sid in sessions}
    completed=set();completed_rounds=0
    for (sid,rid),ends in round_ends.items():
        starts=round_starts.get((sid,rid),[])
        if sid not in sessions or not starts:continue
        if any(end>=min(starts) for end in ends):
            completed.add(sid);completed_rounds+=1
    den=len(started)
    ratio=lambda n,d:round(n/d,6) if d else None
    return {'origin':origin,'sessions':len(sessions),'sessions_with_round_start':den,
       'sessions_with_round_end':len(completed),'completed_rounds':completed_rounds,
       'first_round_completion_rate':ratio(len(completed),den),
       'rematch_intent_rate':ratio(len(rematch&completed),len(completed)),
       'cosmetic_preview_rate':ratio(len(cosmetic&completed),len(completed)),
       'shop_preview_rate':ratio(len(shop&completed),len(completed)),
       'D1_retention':'UNKNOWN','D7_retention':'UNKNOWN','purchases':'UNKNOWN',
       'Robux_revenue':'UNKNOWN','net_revenue':'UNKNOWN','users_returned':'UNKNOWN',
       'disclaimer':'Offline, session-only; neither production engagement nor sales proved'}
