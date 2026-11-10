"""Python specification oracle for independent RoundEvidenceGate.luau.
Do not treat Python success as proof of Luau execution or Studio integration.
"""
from __future__ import annotations
import math
import re

MAPS = frozenset(('S1','S2','S3','S4'))
JOBS = frozenset(('WARRIOR','NINJA','TRAPPER','ZOMBIE_MASTER','BEAST_TAMER','MAGE','BUILDER'))
TEAMS = frozenset(('BLUE','RED'))
WINNERS = frozenset(('BLUE','RED','DRAW'))
ACTIONS = ('enemyHits','objectiveInteractions','trapsTriggered','minionOrders','allySupport','structuresBuilt','eggCarryActions')
ASSISTS = ('defense','rescue','siege')
MAX_USER_ID = 9007199254740991


def integer(value, low, high):
    return type(value) in (int,float) and math.isfinite(value) and value == int(value) and low <= value <= high


def number(value, low, high):
    return type(value) in (int,float) and math.isfinite(value) and low <= value <= high


def member(members, user_id):
    if not isinstance(members, list) or not (1 <= len(members) <= 50):
        return False
    if any(not integer(item, 1, MAX_USER_ID) for item in members):
        return False
    if len(set(members)) != len(members):
        return False
    return user_id in members


def derive(round_, player, expected_user_id):
    if not isinstance(round_, dict) or not isinstance(player, dict):
        return None, 'INVALID_SNAPSHOT'
    if round_.get('serverOwned') is not True or round_.get('phase') != 'RESULT_FINALIZED':
        return None, 'ROUND_NOT_FINALIZED'
    match_id = round_.get('matchId')
    if not isinstance(match_id,str) or not (8 <= len(match_id) <= 80) or not re.fullmatch(r'[A-Za-z0-9_-]+', match_id):
        return None, 'INVALID_MATCH_ID'
    if round_.get('mapId') not in MAPS:
        return None, 'INVALID_MAP'
    if round_.get('winnerTeam') not in WINNERS:
        return None, 'INVALID_WINNER'
    duration = round_.get('durationSeconds')
    if not number(duration,1,3600):
        return None, 'INVALID_DURATION'
    if not integer(expected_user_id,1,MAX_USER_ID) or player.get('userId') != expected_user_id or not member(round_.get('participantUserIds'), expected_user_id):
        return None, 'PARTICIPANT_MISMATCH'
    if player.get('job') not in JOBS:
        return None, 'INVALID_JOB'
    if player.get('team') not in TEAMS:
        return None, 'INVALID_TEAM'
    roster=round_.get('participantTeams')
    if not isinstance(roster,dict) or roster.get(str(expected_user_id))!=player['team'] or any(roster.get(str(uid)) not in TEAMS for uid in round_['participantUserIds']):
        return None, 'ROSTER_TEAM_MISMATCH'
    if not number(player.get('activeSeconds'),0,duration):
        return None, 'INVALID_ACTIVE_TIME'
    counts = player.get('actionCounts')
    if not isinstance(counts,dict) or any(not integer(counts.get(key),0,100000) for key in ACTIONS):
        return None, 'INVALID_ACTION_COUNTS'
    total = sum(counts[key] for key in ACTIONS)
    flags = player.get('assistFlags')
    if not isinstance(flags,dict) or any(type(flags.get(key)) is not bool for key in ASSISTS):
        return None, 'INVALID_ASSIST_FLAGS'
    assists = [key for key in ASSISTS if flags[key]]
    egg_by = round_.get('eggDeliveredByUserId')
    egg_team = round_.get('eggDeliveredByTeam')
    egg_delivered = False
    if egg_by is not None:
        if not integer(egg_by,1,MAX_USER_ID) or not member(round_.get('participantUserIds'),egg_by) or round_['winnerTeam']=='DRAW' or egg_team != round_['winnerTeam'] or roster.get(str(egg_by)) != round_['winnerTeam']:
            return None, 'INVALID_EGG_RECEIPT'
        egg_delivered = egg_by == expected_user_id and player['team']==round_['winnerTeam']
    elif egg_team is not None:
        return None, 'INVALID_EGG_RECEIPT'
    return {
        'userId': expected_user_id, 'matchId': match_id, 'mapId': round_['mapId'], 'job':player['job'],
        'participationSeconds': player['activeSeconds'], 'matchDurationSeconds': duration,
        'meaningfulActionCount': total, 'won': round_['winnerTeam']!='DRAW' and player['team']==round_['winnerTeam'],
        'eggDelivered': egg_delivered, 'assistKinds': assists,
        'matchCompleted':True,
    }, None
