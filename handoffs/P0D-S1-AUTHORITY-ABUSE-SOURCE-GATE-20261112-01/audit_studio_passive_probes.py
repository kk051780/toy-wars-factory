#!/usr/bin/env python3
"""Independent read-only source QA for two optional Studio passive observers.

This does not run Roblox Studio, control player instances, certify the
sole integrator's receipt, or grant a Roblox release score/permission.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile

RC = "5dc6c958ea5549b1e859d6d250e6179e731181fb"
ROOT = "releases/P0D_S1_KIDS_RC01/"
SOURCE_BLOBS = {
    "src/server/Game.server.luau": "3d3c5934e110099517fc4a7eb5aa914fcd52f145",
    "src/server/MapBuilder.luau": "d2127b8c20c8abd880a21f84aeeb706feeb14ce8",
    "src/client/HUD.client.luau": "458a23e83d261c51b3bec174e36e183960532f8c",
    "src/client/FirstMinuteCoach.client.luau": "63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9",
}
CLIENT_TOKENS = (
    "RunService:IsStudio()", "TrapRaidersS1Remote", "OnClientEvent:Connect",
    "SNAPSHOT", "TWO_SIDES_ON_SERVER", "FIRST_MINUTE", "EGG_CARRY",
    "SCORE_INCREASE", "RESULTS", "REMATCH_OBSERVED", "UI_VIEW",
    "UI_WARNING", "BOSS_VISUAL_UNEXPECTED", "STATUS_NOT_PASS",
    "engine_test_requires_manual_evidence=1"
)
SERVER_TOKENS = (
    "RunService:IsStudio()", "TRAP_RAIDERS_S1", "TrapRaidersS1Remote",
    "_CASTLE", "_EGG", "_SCORE_PAD", "REAL_HUMANOID_DAMAGE",
    "REAL_EGG_PROMPT", "REAL_SCORE_PROMPT", "SERVER_ROSTER",
    "MAP_CHECK", "no_gameplay_mutation=1"
)
FORBIDDEN = (
    r":\s*FireServer\s*\(", r":\s*FireClient\s*\(",
    r":\s*FireAllClients\s*\(", r":\s*TakeDamage\s*\(",
    r":\s*LoadCharacter\s*\(", r":\s*Destroy\s*\(",
    r":\s*Clone\s*\(", r":\s*MoveTo\s*\(",
    r"\bInstance\s*\.\s*new\s*\(", r"\bSetAttribute\s*\(",
    r"\bDataStoreService\b", r"\bTeleportService\b",
    r"\bHttpService\b", r"\bOnServerEvent\s*:\s*Connect\s*\(",
    r"\bplayer\.Team\s*=", r"\bscript\s*\.\s*Parent\s*=",
    r"\bgame\s*:\s*BindToClose\s*\(",
)
def check(condition, code):
    if not condition:
        raise RuntimeError(code)

def git_source(repo, path, desired):
    p = subprocess.run(["git", "-C", repo, "show", RC + ":" + ROOT + path],
                       capture_output=True, check=False, timeout=20)
    check(p.returncode == 0, "SOURCE_UNAVAILABLE_" + path)
    raw = p.stdout
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    check(digest == desired, "OFFICIAL_SOURCE_DRIFT_" + path)
    return raw.decode("utf8")

def exact_official_contract(repo):
    sources = {path: git_source(repo, path, blob)
               for path, blob in SOURCE_BLOBS.items()}
    game = sources["src/server/Game.server.luau"]
    world = sources["src/server/MapBuilder.luau"]
    hud = sources["src/client/HUD.client.luau"]
    coach = sources["src/client/FirstMinuteCoach.client.luau"]
    for token in (
        'Instance.new("RemoteEvent")', 'remote.Name = "TrapRaidersS1Remote"',
        "remote.OnServerEvent:Connect", "redPlayers = teamCount",
        "bluePlayers = teamCount", "local CANONICAL_S1_ENABLED = false",
        "local D07_D08_RELEASE_REVIEW_APPROVED = false",
        'match.phase = "RESULTS"', 'match.phase = "COUNTDOWN"',
    ):
        check(token in game, "GAME_CONTROLLER_CONTRACT_DRIFT_" + token)
    for token in ('"TRAP_RAIDERS_S1"', '"RED"', '"BLUE"', '"_CASTLE"',
                  '"_EGG"', '"_SCORE_PAD"', '"_CASTLE_CORE"', "ProximityPrompt"):
        check(token in world, "MAP_CONTRACT_DRIFT_" + token)
    check('"TrapRaidersS1HUD"' in hud and '"Attack"' in hud
          and '"TR_S1_FirstMinuteCoach"' in coach
          and '"CoachPanel"' in coach,
          "CLIENT_GUI_CONTRACT_DRIFT")
    print("P0D_PASSIVE_PROBE_OFFICIAL_RC_CONTRACT_PASS verified_sha1=4/4")

def basic(script, kind):
    check(script.lstrip().startswith("--!strict"), kind + "_MISSING_STRICT")
    check("if not RunService:IsStudio() then return end" in script,
          kind + "_NOT_STUDIO_GATED")
    for pattern in FORBIDDEN:
        check(re.search(pattern, script) is None,
              kind + "_MUTATION_OR_AUTHORITY_DETECTED_" + pattern)
    for token in CLIENT_TOKENS if kind == "CLIENT" else SERVER_TOKENS:
        check(token in script, kind + "_REQUIRED_EVIDENCE_TOKEN_ABSENT_" + token)
    if kind == "CLIENT":
        check(script.count("remote.OnClientEvent:Connect(") == 1,
              "CLIENT_REMOTE_LISTENER_NOT_SINGLE")
        check("actual_two_Studio_clients_must_be_separately_confirmed=1" in script,
              "CLIENT_CLAIMS_UNPROVEN_2CLIENT")
    else:
        check(script.count("Players.PlayerAdded:Connect(") == 1,
              "SERVER_ROSTER_LISTENER_NOT_SINGLE")
    return True

def negative_controls(client, server):
    variants = [
        ("client_attack", client + '\nremote:FireServer({action="ATTACK"})\n', "CLIENT"),
        ("client_missing_guard", client.replace(
            "if not RunService:IsStudio() then return end", "", 1), "CLIENT"),
        ("client_new_remote", client + '\nlocal r=Instance.new("RemoteEvent")\n', "CLIENT"),
        ("client_forged_listener", client +
         '\nremote.OnServerEvent:Connect(function() end)\n', "CLIENT"),
        ("client_gui_destruction", client + '\ngui:Destroy()\n', "CLIENT"),
        ("server_health_write", server + '\nh:TakeDamage(999)\n', "SERVER"),
        ("server_emits_remote", server +
         '\nremote:FireAllClients({action="ATTACK"})\n', "SERVER"),
        ("server_missing_guard", server.replace(
            "if not RunService:IsStudio() then return end", "", 1), "SERVER"),
        ("server_new_remote", server + '\nlocal r=Instance.new("RemoteEvent")\n', "SERVER"),
        ("server_storage", server + '\nlocal s=game:GetService("DataStoreService")\n',
         "SERVER"),
    ]
    for label, altered, kind in variants:
        try:
            basic(altered, kind)
        except RuntimeError:
            print("P0D_STUDIO_PASSIVE_NEGATIVE_REJECTED_" + label)
        else:
            raise RuntimeError("NOT_REJECTED_" + label)
    print("P0D_STUDIO_PASSIVE_NEGATIVE_CONTROLS=10/10")

def luau_parse(luau, client, server):
    if not luau:
        return
    for kind, src in (("CLIENT", client), ("SERVER", server)):
        delimiter = 0
        while "]" + "=" * delimiter + "]" in src:
            delimiter += 1
        opener = "[" + "=" * delimiter + "["
        closer = "]" + "=" * delimiter + "]"
        def compile_check(body, should_pass):
            chunk = (
                "local func,err=loadstring(" + opener + body + closer +
                ',"studio_probe")\nif not func then error(err,0) end\n' +
                'print("P0D_STUDIO_PASSIVE_' + kind + '_PARSED")\n'
            )
            with tempfile.TemporaryDirectory() as d:
                f = Path(d) / "probe_parse_only.luau"
                f.write_text(chunk, encoding="utf8")
                p = subprocess.run([luau, str(f)], capture_output=True, text=True,
                                   check=False, timeout=25)
            if should_pass:
                check(p.returncode == 0 and
                      ("P0D_STUDIO_PASSIVE_" + kind + "_PARSED") in p.stdout,
                      kind + "_LUAU_SYNTAX_FAIL_" + (p.stdout + p.stderr)[-800:])
            else:
                check(p.returncode != 0, kind + "_INVALID_SYNTAX_NOT_REJECTED")
        compile_check(src, True)
        compile_check(src + "\nlocal = 1\n", False)
        print("P0D_STUDIO_PASSIVE_LUAU_PARSE_PASS_" + kind + " negative=1")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--luau", default="")
    opts = parser.parse_args()
    root = Path(__file__).resolve().parent
    client = (root / "StudioPassiveClientProbe.client.luau").read_text("utf8")
    server = (root / "StudioPassiveServerProbe.server.luau").read_text("utf8")
    exact_official_contract(opts.repo)
    basic(client, "CLIENT")
    basic(server, "SERVER")
    print("P0D_STUDIO_PASSIVE_PROBE_STATIC_SAFETY_PASS modules=2/2")
    negative_controls(client, server)
    luau_parse(opts.luau, client, server)
    print("P0D_STUDIO_PASSIVE_PROBE_PREP_ONLY_SUCCESS NO_STUDIO_RUN")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, OSError, UnicodeError,
            subprocess.TimeoutExpired) as err:
        print("P0D_STUDIO_PASSIVE_QA_BLOCKED " + str(err), file=sys.stderr)
        sys.exit(1)
