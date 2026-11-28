"""Execute the real selected First90 cue policy with the frozen previous inputs."""
from hashlib import sha256
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
CASES = {"ON": "first90_context_on", "OFF": "first90_context_off"}
PROCESS_COUNT = 2
FILES = {name+"."+suffix for name in CASES.values()
         for suffix in ("luau","stdout.log","stderr.log","status.txt")}
SOURCE_PINS = {
    "ON": {"bytes":10549,"sha256":"b10c462bcf12631b59e6be4fc3ab632bfaf94e1662a8d69e1808668d0e52ca1a"},
    "OFF": {"bytes":9516,"sha256":"f3067a5b4c7bbffdecf491ff6cae58ec5d61cb0ad99e537ab6017c9f8c84224e"},
}
FIXTURE_PINS = {
    "legacy": "d59eddc28d666c91594028da3b434d32bbae9127fdbcc76d452518190306747f",
    "new": "452399dae6d8101b44bf448168bdec2348d8fd1e27c40144eb1fd0615b750b1c",
}
BASE_MARKERS = (
    "FB004_EACH_REAL_ROLE_HAS_OWN_FIRST_ACTION_PASS",
    "FB004_KIT_SELECTION_SAFE_ROLLBACK_AND_NARROW_FALLBACK_PASS",
    "FB004_READY_COMBAT_BUTTONS_OBJECTIVE_AND_ELIMINATION_PASS",
    "FB004_ECLIPSE_WARRIOR_CUES_AND_UTF8_KIT_TITLE_PASS",
)
NEW_MARKERS = (
    "FIRST90_DELAYED_QUEUES_ARE_QUIET_AND_BOUNDED_PASS",
    "FIRST90_LATE_DEPLOY_SEES_ATTACK_AND_OBJECTIVE_TIMING_PASS",
    "FIRST90_ACTUAL_CUSTODY_OVERRIDES_AND_ELIMINATION_CLEARS_PASS",
    "FIRST90_LIVE_OFF_RESTORES_LEGACY_TIMING_AND_HINTS_PASS",
)
START = b"local roleIntroduction=table.freeze"
END = b"task.spawn(function()\n while alive and player.Parent==Players do"

def need(condition,reason):
    if not condition: raise ValueError("FIRST90_CONTEXT_"+reason)

def program(source_root,mode):
    need(mode in CASES,"MODE")
    body=(Path(source_root)/ROUTE).read_bytes()
    need({"bytes":len(body),"sha256":sha256(body).hexdigest()}==SOURCE_PINS[mode],"SOURCE")
    legacy=(HERE.parent/"first90_role/cases.luau").read_bytes()
    cases=(HERE/"first90_context_cases.luau").read_bytes()
    need(sha256(legacy).hexdigest()==FIXTURE_PINS["legacy"] and sha256(cases).hexdigest()==FIXTURE_PINS["new"],"CASE_PIN")
    header=b'''local player={attrs={}}
local workspace={attrs={}}
function player:GetAttribute(key) return self.attrs[key] end
function workspace:GetAttribute(key) return self.attrs[key] end
'''
    names=(b"DURATION",b"STEP1",b"STEP2",b"LOBBY_WATCH_LIMIT") if mode=="ON" else (b"STEP1",b"STEP2")
    constants=[]
    for key in names:
        matches=re.findall(rb"(?m)^local "+key+rb"=[0-9]+$",body)
        need(len(matches)==1,"TIMER_CONSTANT")
        constants.extend(matches)
    declarations=[b"local deployedAt:number?=nil"]
    if mode=="ON": declarations.append(b"local firstDeploymentAt:number?=nil")
    need(all(body.count(line)==1 for line in declarations),"TIMER_DECLARATIONS")
    need(body.count(START)==body.count(END)==1 and body.index(START)<body.index(END),"BOUNDARY")
    return header+b"\n".join(constants+declarations)+b"\n"+body[body.index(START):body.index(END)]+legacy+(
        b"\n"+cases if mode=="ON" else b"")

def assert_result(mode,stdout,stderr,exit_code):
    need(mode in CASES and type(exit_code) is int and exit_code==0 and not stderr,"RESULT_STATUS")
    markers=BASE_MARKERS+(NEW_MARKERS if mode=="ON" else ())
    need(tuple(stdout.decode("ascii").splitlines())==markers,"RESULT_MARKERS")
    return markers
