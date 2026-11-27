"""Exercise the shipped Host/HUD relay presentation and the unchanged rule boundary."""

import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
PACKAGE = "quality_gameplay/gq470_relay_eligibility_20261127"
RULES = "ServerScriptService/EGGRUMBLE_CastleMatchRules.luau"
CLIENT_MARKER = b"-- @RELAY_PRESENTATION_MOUNTED@\n"
RECEIVER = b"EGGRUMBLE_RelayPresentationReceiverReady"
COUNTS = {"candidate_client": 25, "server_display": 9, "unchanged_rules": 48}
RULE_PREFIX = b'''local engineTypeof = typeof
local function typeof(value)
    if type(value) == "table" and value.__fixtureType == "Vector3" then return "Vector3" end
    return engineTypeof(value)
end
local Rules = (function()
'''


def replace_once(raw, old, new, compose):
    compose.need(raw.count(old) == 1, "RELAY_ELIGIBILITY_FIXTURE_MARKER")
    return raw.replace(old, new, 1)


def section(body, first, last, compose):
    compose.need(body.count(first) == 1 and body.count(last) == 1
                 and body.index(first) < body.index(last), "RELAY_ELIGIBILITY_HOST_REGION")
    return body[body.index(first):body.index(last)]


def assemble(root, lock, compose):
    repair = lock["relay_eligibility_followup"]
    inputs = {name: compose.read_file(compose.REPO / PACKAGE / name) for name in repair["native_fixtures"]}
    compose.need(set(inputs) == {"client_cases.luau", "server_context.luau", "server_cases.luau",
                                 "rules_boundary.luau"}
                 and {name: compose.identity(raw) for name, raw in inputs.items()} == repair["native_fixtures"],
                 "RELAY_ELIGIBILITY_SOURCE_FIXTURES")
    active, prior = root / "sources", root / compose.RELAY_ELIGIBILITY_OFF / "sources"
    selected = {route: compose.read_file(active / route) for route in compose.RELAY_ELIGIBILITY_SOURCES}
    compose.need(all(compose.identity(raw) == lock["sources"][route]["after"] for route, raw in selected.items()),
                 "RELAY_ELIGIBILITY_EXACT_ACTIVE_SOURCE_PINS")
    rules = compose.read_file(active / RULES)
    compose.need(rules == compose.read_file(prior / RULES)
                 and compose.identity(rules) == repair["rules_exact"], "RELAY_ELIGIBILITY_RULES_CHANGED")
    host, hud = (selected[route] for route in compose.RELAY_ELIGIBILITY_SOURCES)
    old_host = compose.read_file(prior / compose.VAULT_SOURCE)
    first = b"    table.insert(session.lifeConnections,relayPrompt.Triggered:Connect(function(receiver:Player)"
    last = b'    task.spawn(function()\n     while sessions[mode]==session and session.rules.phase=="ACTIVE"'
    compose.need(section(host, first, last, compose) == section(old_host, first, last, compose),
                 "RELAY_ELIGIBILITY_TRANSFER_CALLBACK_CHANGED")
    publisher = section(host, b"  local function publishRelayReady(", b"  session.eggRelayStop=function()", compose)
    display = section(host, b"      local id=tostring(carrierPlayer.UserId)\n", b"      task.wait(.35)\n", compose)
    mounted = section(hud, b"task.spawn(function()\n--!strict", b'local Players=game:GetService("Players")', compose)
    fixture = compose.read_file(HERE / "relay_presentation_cases.luau")
    compose.need(compose.identity(fixture) == lock["relay_presentation_followup"]["native_case"],
                 "RELAY_ELIGIBILITY_PRESERVE_22_NATIVE_CASES")
    seed = b"\t\tprompt:SetAttribute(READY, carrying)\n"
    fixture = replace_once(fixture, seed, seed + b'\t\tprompt:SetAttribute("' + RECEIVER + b'", true)\n', compose)
    rejoin = b'[ROUND] = 1, [TEAM] = "RED", [HEIGHT] = 4, [READY] = true'
    fixture = replace_once(fixture, rejoin, rejoin + b', ["' + RECEIVER + b'"] = true', compose)
    done = b'print("PROJECTION_NATIVE_PASS", count)'
    fixture = replace_once(fixture, done, inputs["client_cases.luau"] + b"\n" + done, compose)
    programs = {"candidate_client": replace_once(fixture, CLIENT_MARKER, mounted, compose),
                "server_display": inputs["server_context.luau"] + publisher + b"\nlocal function refresh()\n"
                + display + b"\nend\n" + inputs["server_cases.luau"],
                "unchanged_rules": RULE_PREFIX + rules + b"\nend)()\n" + inputs["rules_boundary.luau"]}
    compose.need({name: compose.identity(raw) for name, raw in programs.items()} == repair["native_programs"],
                 "RELAY_ELIGIBILITY_EXACT_PROGRAMS")
    return programs, {route: compose.identity(raw) for route, raw in selected.items()}


def observe(root, folder, pin, context, lock, compose, binary=None):
    programs, sources = assemble(root, lock, compose)
    files, observed = {"receipt.json"}, {}
    for label, raw in programs.items():
        program, stdout, stderr = (folder / (label + suffix) for suffix in (".luau", ".stdout", ".stderr"))
        if binary is not None:
            program.write_bytes(raw)
            result = subprocess.run([str(binary), str(program)], capture_output=True, timeout=30)
            stdout.write_bytes(result.stdout)
            stderr.write_bytes(result.stderr)
            compose.need(result.returncode == 0, "RELAY_ELIGIBILITY_NATIVE_EXIT:" + label)
        actual = compose.read_file(stdout)
        compose.need(compose.read_file(program) == raw and compose.read_file(stderr) == b""
                     and compose.identity(actual.replace(b"\r\n", b"\n"))
                     == lock["relay_eligibility_followup"]["native_stdout"][label],
                     "RELAY_ELIGIBILITY_EXACT_VECTOR:" + label)
        observed[label] = {"program": compose.identity(raw), "stdout": compose.identity(actual), "cases": COUNTS[label]}
        files.update({program.name, stdout.name, stderr.name})
    return {"status": "PASS", "source_only": True, "binary": pin, "context": context,
            "source_pins": sources, "programs": observed}, files


def run(root, folder, binary, pin, context, lock, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "RELAY_ELIGIBILITY_BINARY")
    folder.mkdir()
    receipt, files = observe(root, folder, pin, context, lock, compose, binary=binary)
    (folder / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    compose.need({p.name for p in folder.iterdir()} == files
                 and compose.identity(compose.read_file(binary)) == pin, "RELAY_ELIGIBILITY_OUTPUT")
    print("relay_eligibility: 25 client cases, nine server display cases and 48 real Rules checks PASS", flush=True)
