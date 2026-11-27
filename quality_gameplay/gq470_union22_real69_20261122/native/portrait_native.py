"""Exercise the original #947 layout tests against the exact selected Policy."""
import importlib.util
import subprocess

FILES = {"generated.luau", "stdout.log", "stderr.log", "receipt.json"}
STDOUT = b"GQ470_HUD_PORTRAIT_REAL_LUAU_LAYOUT_18_CASES_PASS\n"


def program(root, lock, compose):
    pinned = lock["portrait_followup"]["author"]
    author = compose.REPO / pinned["path"]
    compose.need(compose.identity(compose.read_file(author)) == pinned["identity"], "PORTRAIT_NATIVE_AUTHOR_PIN")
    spec = importlib.util.spec_from_file_location("union22_portrait_author", author)
    suite = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(suite)
    suite.self_test()
    route = compose.PORTRAIT_SOURCE
    policy = compose.read_file(root / route)
    policy_pin = compose.identity(policy)
    compose.need(policy_pin == lock["sources"][route]["after"], "PORTRAIT_NATIVE_POLICY_PIN")
    return suite.native_test_source(policy.decode("utf-8")).encode("utf-8"), policy_pin


def observe(root, output, binary, pin, context, lock, compose):
    expected, policy = program(root, lock, compose)
    stdout = compose.read_file(output / "stdout.log")
    compose.need(compose.read_file(output / "generated.luau") == expected
                 and stdout.replace(b"\r\n", b"\n") == STDOUT
                 and compose.read_file(output / "stderr.log") == b""
                 and compose.identity(compose.read_file(binary)) == pin, "PORTRAIT_NATIVE_RESULT")
    return {"status": "PASS", "exit_code": 0, "context": context, "binary": pin,
            "source": policy, "native_cases": 18, "author_negative_mutants": 5,
            "program": compose.identity(expected), "stdout": compose.identity(stdout),
            "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def run(root, output, binary, pin, context, lock, compose, environment):
    generated, _ = program(root, lock, compose)
    output.mkdir()
    target = output / "generated.luau"
    target.write_bytes(generated)
    result = subprocess.run([str(binary), str(target)], capture_output=True, env=environment, timeout=30)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    compose.need(result.returncode == 0, "PORTRAIT_NATIVE_EXIT")
    compose.write_json(output / "receipt.json", observe(root, output, binary, pin, context, lock, compose))
