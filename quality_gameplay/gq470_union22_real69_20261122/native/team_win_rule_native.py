"""Run the real PRIVATE queue-board function before and after the FB-003 fix."""
from pathlib import Path
import subprocess

FILES = {"generated.luau", "stdout.log", "stderr.log", "receipt.json"}
EXPECTED = b"PRIVATE_TEAM_WIN_BOARD_ACTUAL_HOST_OFF_RED_ON_8_CASES_PASS\n"
PROGRAM_ARG = "team_win_rule/generated.luau"


def program(root, lock, compose):
    followup = lock["team_win_rule_followup"]
    route = compose.VAULT_SOURCE
    pins = {"before": followup["rows"][route]["parent"]["after"],
            "after": lock["sources"][route]["after"]}
    paths = {"before": root.parent / compose.TEAM_WIN_RULE_OFF / "sources" / route,
             "after": root / route}
    fixture = followup["native_fixture"]
    template = compose.read_file(compose.REPO / fixture["path"])
    compose.need(compose.identity(template) == {key: fixture[key] for key in ("bytes", "sha256")}
                 and template.count(b"__HOST_REFRESH_PROGRAMS__") == 1, "TEAM_WIN_RULE_NATIVE_FIXTURE")
    programs = []
    for name, path in paths.items():
        host = compose.read_file(path)
        compose.need(compose.identity(host) == pins[name], "TEAM_WIN_RULE_NATIVE_HOST:" + name)
        bounds = [b"local function refreshQueueBoard(", b"local function getCastlePoint("]
        compose.need(all(host.count(mark) == 1 for mark in bounds)
                     and host.index(bounds[0]) < host.index(bounds[1]), "TEAM_WIN_RULE_NATIVE_BOUNDARY")
        declarations = [line for line in host.splitlines()
                        if line.startswith((b"local MODE_SEATS=", b"local COUNTDOWN="))]
        compose.need(len(declarations) == 2, "TEAM_WIN_RULE_NATIVE_CONSTANTS")
        programs.extend((
            f"local function {name}Refresh(queueBoards,queues,sessions,queueStartedAt,time)".encode(),
            *declarations, host[host.index(bounds[0]):host.index(bounds[1])],
            b"return refreshQueueBoard", b"end",
        ))
    return template.replace(b"__HOST_REFRESH_PROGRAMS__", b"\n".join(programs)), pins


def observe(root, output, binary, binary_pin, context, lock, compose):
    generated, pins = program(root, lock, compose)
    stdout = compose.read_file(output / "stdout.log")
    compose.need(compose.read_file(output / "generated.luau") == generated
                 and stdout.replace(b"\r\n", b"\n") == EXPECTED
                 and not compose.read_file(output / "stderr.log")
                 and compose.identity(compose.read_file(binary)) == binary_pin, "TEAM_WIN_RULE_NATIVE_RESULT")
    return {"status": "PASS", "context": context, "binary": binary_pin,
            "argv": [str(binary), PROGRAM_ARG], "source_pins": pins,
            "generated": compose.identity(generated), "stdout": compose.identity(stdout),
            "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def run(root, output, binary, binary_pin, context, lock, compose, environment):
    generated, _ = program(root, lock, compose)
    output.mkdir()
    dest = output / "generated.luau"
    dest.write_bytes(generated)
    result = subprocess.run([str(Path(binary).resolve()), PROGRAM_ARG], cwd=output.parent,
                            capture_output=True, env=environment, timeout=30)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    compose.need(result.returncode == 0, "TEAM_WIN_RULE_NATIVE_EXIT")
    compose.write_json(output / "receipt.json",
                       observe(root, output, Path(binary), binary_pin, context, lock, compose))
