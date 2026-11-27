"""Run the selected Private HUD layout and its unmodified policy in native Luau."""
from pathlib import Path
import subprocess

POLICY = "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy.luau"
EXPECTED_STDOUT = b"PRIVATE_NATIVE_EXISTING_POLICY_TOUCH_JUMP_CACHE_SAFE_INSET_PASS\n"
FILES = {"generated.luau", "stdout.log", "stderr.log", "receipt.json"}


def program(root, lock, compose):
    route = compose.PRIVATE_TOUCH_SOURCE
    pins = {name: lock["sources"][name]["after"] for name in (route, POLICY)}
    hud, policy = (compose.read_file(root / name) for name in pins)
    compose.need({route: compose.identity(hud), POLICY: compose.identity(policy)} == pins,
                 "PRIVATE_TOUCH_NATIVE_SOURCE_PINS")
    fixture = lock["private_touch_followup"]["native_fixture"]
    template = compose.read_file(compose.REPO / fixture["path"])
    compose.need(compose.identity(template) == {key: fixture[key] for key in ("bytes", "sha256")}
                 and template.count(b"__POLICY__") == template.count(b"__HUD_LAYOUT__") == 1,
                 "PRIVATE_TOUCH_NATIVE_FIXTURE")
    start = b"local function touchJumpGeometry()"
    finish = b"\nrefreshMapLayout=function()"
    compose.need(hud.count(start) == hud.count(finish) == 1 and hud.index(start) < hud.index(finish),
                 "PRIVATE_TOUCH_NATIVE_LAYOUT_BOUNDARY")
    body = hud[hud.index(start):hud.index(finish) + len(b"\n")]
    return template.replace(b"__POLICY__", policy).replace(b"__HUD_LAYOUT__", body), pins


def observe(root, output, binary, binary_pin, context, lock, compose):
    expected, pins = program(root, lock, compose)
    generated = output / "generated.luau"
    stdout = compose.read_file(output / "stdout.log")
    compose.need(compose.read_file(generated) == expected
                 and stdout.replace(b"\r\n", b"\n") == EXPECTED_STDOUT
                 and compose.read_file(output / "stderr.log") == b""
                 and compose.identity(compose.read_file(binary)) == binary_pin, "PRIVATE_TOUCH_NATIVE_RESULT")
    return {"status": "PASS", "exit_code": 0, "context": context, "binary": binary_pin,
            "source_pins": pins,
            "generated": compose.identity(expected), "stdout": compose.identity(stdout),
            "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def run(root, output, binary, binary_pin, context, lock, compose, environment):
    generated, _ = program(root, lock, compose)
    output.mkdir()
    dest = output / "generated.luau"
    dest.write_bytes(generated)
    result = subprocess.run([str(binary), str(dest)], capture_output=True, env=environment, timeout=30)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    compose.need(result.returncode == 0, "PRIVATE_TOUCH_NATIVE_EXIT")
    compose.write_json(output / "receipt.json",
                       observe(root, output, Path(binary), binary_pin, context, lock, compose))
