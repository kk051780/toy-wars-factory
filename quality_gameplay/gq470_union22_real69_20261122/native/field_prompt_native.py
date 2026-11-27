"""Run the prepared field-prompt cases on exact Host/RULES sections of both Places."""

from pathlib import Path
import json
import subprocess


FILE_NAMES = {"receipt.json"} | {
    f"{variant}-{name}" for variant in ("off", "on") for name in ("case.luau", "stdout.log", "stderr.log")
}


def assemble(path, lock, control, compose):
    repair = lock["field_prompt_followup"]
    host_route = compose.VAULT_SOURCE
    rules_route = "ServerScriptService/EGGRUMBLE_CastleMatchRules.luau"
    rules = compose.read_file(path / rules_route)
    host = compose.read_file(path / host_route)
    expected = repair["rows"][host_route]["parent"] if control else lock["sources"][host_route]
    compose.need(compose.identity(host) == expected["after"]
                 and compose.identity(rules) == lock["sources"][rules_route]["after"], "FIELD_PROMPT_SOURCE_PINS")
    template = compose.read_file(Path(__file__).with_name("field_prompt_cases.luau"))
    compose.need(compose.identity(template) == repair["native_case"], "FIELD_PROMPT_FIXTURE_PIN")

    def section(first, last):
        compose.need(host.count(first) == host.count(last) == 1, "FIELD_PROMPT_HOST_ANCHOR")
        start, end = host.index(first), host.index(last)
        compose.need(start < end, "FIELD_PROMPT_HOST_SECTION_ORDER")
        return host[start:end]

    declare = b" local fieldEggPrompts={}\n"
    compose.need(host.count(declare) == int(not control), "FIELD_PROMPT_REGISTRATION_SCOPE")
    inserts = {
        b"__FIELD_RULES__": rules,
        b"__FIELD_DEADLINE__": section(b"local Deadline={}\n", b"-- MATCH_DEADLINE_DRAW_499 END ORIGINAL POLICY"),
        b"__FIELD_BLOCK__": section(b"local function block(", b"local function board("),
        b"__FIELD_PROMPT__": section(b"local function prompt(", b"-- Display availability follows"),
        b"__FIELD_LOOP__": section(b" -- Field eggs available in both modes", b" -- One trusted visual stage"),
        b"__FIELD_REFRESH__": section(b" session.refresh=function()\n",
                                      b"  -- All current castle/deadline finish paths refresh before yielding."),
        b"__FIELD_DECLARATION__": b"" if control else declare,
        b"__FIELD_IS_CONTROL__": b"true" if control else b"false",
    }
    result = template
    for marker, raw in inserts.items():
        compose.need(result.count(marker) == 1, "FIELD_PROMPT_TEMPLATE_MARKER")
        result = result.replace(marker, raw, 1)
    return result, {marker.decode(): compose.identity(raw) for marker, raw in inserts.items()}


def verify(path, output, vm_pin, context, lock, compose):
    runs = {}
    for tag, folder in (("off", path.parent / compose.FIELD_PROMPT_OFF / "sources"), ("on", path)):
        control = tag == "off"
        program, fragments = assemble(folder, lock, control, compose)
        file = output / f"{tag}-case.luau"
        stdout = compose.read_file(output / f"{tag}-stdout.log")
        stderr = compose.read_file(output / f"{tag}-stderr.log")
        verdict = "REPRODUCED_CONTROL" if control else "FIELD_PROMPTS_DISABLED"
        rows = [f"PASS\t{mode}\t{finish}\t{verdict}\tfresh replay and other mode unchanged"
                for mode in ("TEAM", "BATTLE_ROYALE") for finish in ("CASTLE", "DEADLINE")]
        compose.need(compose.read_file(file) == program and not stderr and stdout.decode().splitlines() == rows,
                     "FIELD_PROMPT_EXACT_NATIVE_CASE_VECTOR")
        runs[tag] = {"program": compose.identity(program), "sections": fragments, "rows": rows,
                     "stdout": compose.identity(stdout), "stderr": compose.identity(stderr)}
    return {"schema": "UNION22_FIELD_PROMPT_NATIVE_V1", "status": "PASS", "context": context, "native": vm_pin,
            "scope": "Exact host field/prompt/terminal sections and entire Rules on mocked Roblox objects",
            "runs": runs}


def run(path, output, binary, vm_pin, context, lock, compose):
    output.mkdir()
    for tag, folder in (("off", path.parent / compose.FIELD_PROMPT_OFF / "sources"), ("on", path)):
        program, _ = assemble(folder, lock, tag == "off", compose)
        target = output / f"{tag}-case.luau"
        target.write_bytes(program)
        result = subprocess.run([str(binary), str(target)], capture_output=True, timeout=60, check=True)
        (output / f"{tag}-stdout.log").write_bytes(result.stdout)
        (output / f"{tag}-stderr.log").write_bytes(result.stderr)
    receipt = verify(path, output, vm_pin, context, lock, compose)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("field_prompt: 8 OFF/ON cases; TEAM and BR city/deadline finish, stale action, fresh rematch PASS", flush=True)
