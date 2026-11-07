"""Character catalog and benefit/effort checks. No release or execution authority.

Scores are design hypotheses, not measured acquisition, revenue or retention.
The source parser checks the project's literal balance table; Lua regressions
remain responsible for executing model, selection, production and combat code.
"""
import argparse
import json
from pathlib import Path
import re

BASELINE_IDS = {"pon", "guardon", "tankuru"}
EFFORT_KEYS = {"model", "animation", "combat", "ui", "qa"}
APPEAL_KEYS = {"acquisition", "retention", "strategy"}


# This is a conservative literal-source gate, not a general Luau interpreter.
# Ignore strings/comments when locating roster writes. A single literal
# B.UNITS = { ... } declaration is required; later roster/field writes are
# forbidden even if the original catalog still matches the first declaration.
_LUA_TOKEN = re.compile(
    r'(?P<comment>--\[\[.*?\]\]|--[^\n]*)'
    r'|(?P<string>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    r'|(?P<name>[A-Za-z_][A-Za-z0-9_]*)'
    r'|(?P<op>==|~=|<=|>=|\+=|-=|\*=|/=|%=|[^\s])',
    re.S,
)
_ASSIGNMENTS = {"=", "+=", "-=", "*=", "/=", "%="}


def _unit_declaration_start(source):
    tokens = [
        (match.group(), match.start())
        for match in _LUA_TOKEN.finditer(source)
        if match.lastgroup != "comment"
    ]
    words = [value for value, _ in tokens]
    declarations = []
    getunit_definitions = 0
    for i, word in enumerate(words):
        if word != "B":
            continue
        # Only the original local B = {} is permitted: replacing the module
        # later bypasses comparisons against the first registered unit table.
        if i + 1 < len(words) and words[i + 1] in _ASSIGNMENTS:
            if i == 0 or words[i - 1] != "local" or words[i + 1] != "=":
                raise ValueError("balance module reassignment is forbidden")
        # Bracketed module writes can dynamically target UNITS (B[key] = ...).
        # The canonical balance contract has no bracketed B member lookups,
        # so fail closed instead of attempting to infer the dynamic key.
        if words[i + 1:i + 2] == ["["]:
            raise ValueError("dynamic B member alias or write is forbidden")
        # B.getUnit returns a mutable B.UNITS[id] record. Disallow calls,
        # function aliases and reassignments in the checked module, retaining
        # exactly one canonical method definition.
        if words[i + 1:i + 3] == [".", "getUnit"]:
            if i >= 1 and words[i - 1] == "function" and words[i + 3:i + 4] == ["("]:
                getunit_definitions += 1
            else:
                raise ValueError("B.getUnit reference outside declaration is forbidden")
            continue
        if words[i + 1:i + 3] == [".", "UNITS"]:
            j = i + 3
            dot_form = True
        elif (words[i + 1:i + 4] in
              (["[", '"UNITS"', "]"], ["[", "'UNITS'", "]"])):
            j = i + 4
            dot_form = False
        else:
            continue

        # The canonical source uses B.UNITS, never B["UNITS"] aliases.
        if not dot_form:
            raise ValueError("dynamic B.UNITS alias is forbidden")

        # Consume nested read-only fields such as B.UNITS[id].cost. A write
        # at any depth must fail, but lookups and ~= / == are not writes.
        end = j
        while end < len(words):
            if (words[end] == "." and end + 1 < len(words) and
                    re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", words[end + 1])):
                end += 2
            elif words[end] == "[":
                depth = 1
                end += 1
                while end < len(words) and depth:
                    if words[end] == "[":
                        depth += 1
                    elif words[end] == "]":
                        depth -= 1
                    end += 1
                if depth:
                    raise ValueError("unbalanced B.UNITS accessor")
            else:
                break

        is_write = end < len(words) and words[end] in _ASSIGNMENTS
        # Exposing the whole B.UNITS table permits local alias mutation:
        # local roster=B.UNITS; roster.pon=nil.
        if end == j and not is_write:
            raise ValueError("bare B.UNITS reference can escape the roster")
        # A unit/roster record assigned to a variable would carry a mutable
        # reference. An exact primitive leaf read in the existing JUNK threat
        # formula is different: these fields are literal numeric values in the
        # canonical roster and the checker still forbids any field write.
        # Deliberately narrow: NOT a generic "all property reads are safe"
        # exception and NOT cross-module alias/type analysis.
        readonly_junk_numeric = words[i:end] in (
            ["B", ".", "UNITS", ".", "junk", ".", "hp"],
            ["B", ".", "UNITS", ".", "junk", ".", "damage"],
        )
        if i >= 1 and words[i - 1] == "=" and not readonly_junk_numeric:
            raise ValueError("B.UNITS reference assigned to mutable alias")
        if (i >= 2 and words[i - 1] == "(" and words[i - 2] == "="
                and not readonly_junk_numeric):
            raise ValueError("parenthesized B.UNITS alias is forbidden")
        if is_write:
            if end != j or words[end] != "=" or words[end + 1:end + 2] != ["{"]:
                raise ValueError("mutable B.UNITS roster is forbidden")
            declarations.append(tokens[i][1])

        # Lua helpers can mutate the table without a direct assignment.
        if i >= 2 and words[i - 2:i] in (
                ["rawset", "("], ["setmetatable", "("]):
            raise ValueError("mutating B.UNITS helper call is forbidden")
        if i >= 4 and words[i - 4:i - 2] == ["table", "."] and words[i - 2] in (
                "clear", "insert", "remove", "move", "sort") and words[i - 1] == "(":
            raise ValueError("mutating B.UNITS table operation is forbidden")

        if (i >= 2 and words[i - 2:i] == ["rawset", "("] and
                words[i + 1:i + 3] == [",", '"UNITS"']):
            raise ValueError("mutating B.UNITS helper call is forbidden")

    # rawset(B, dynamic_key, value) can change UNITS even when the key is
    # computed elsewhere; a literal-key-only check is insufficient.
    for i in range(len(words) - 3):
        if words[i:i + 4] in (["rawset", "(", "B", ","],
                              ["setmetatable", "(", "B", ","]):
            raise ValueError("mutating B module helper call is forbidden")
    if getunit_definitions != 1:
        raise ValueError("exactly one B.getUnit declaration required")
    if len(declarations) != 1:
        raise ValueError("exactly one literal B.UNITS declaration required")
    return declarations[0]


def registered_ids(source):
    """Parse each real top-level unit field, never infer identity from indent.

    A Lua table field can start after any whitespace or on the same line;
    regex matching only four leading spaces silently omitted real entries.
    Tokenizing also excludes comments and strings from the key count.
    """
    start = _unit_declaration_start(source)
    words = [
        match.group() for match in _LUA_TOKEN.finditer(source[start:])
        if match.lastgroup != "comment"
    ]
    if words[:5] != ["B", ".", "UNITS", "=", "{"]:
        raise ValueError("literal B.UNITS table missing or malformed")
    ids = []
    i = 5
    while i < len(words):
        if words[i] == "}":
            break
        if (not re.fullmatch(r"[a-z][a-z0-9_]*", words[i]) or
                words[i + 1:i + 3] != ["=", "{"]):
            raise ValueError("nonliteral or unsupported B.UNITS table key")
        ids.append(words[i])
        i += 2
        depth = 0
        while i < len(words):
            if words[i] == "{":
                depth += 1
            elif words[i] == "}":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        if depth:
            raise ValueError("unbalanced literal B.UNITS unit record")
        if i < len(words) and words[i] in (",", ";"):
            i += 1
        elif i < len(words) and words[i] != "}":
            raise ValueError("malformed B.UNITS field separator")
    else:
        raise ValueError("unterminated literal B.UNITS table")
    if len(ids) != len(set(ids)) or "junk" not in ids:
        raise ValueError("duplicate unit or missing NPC boundary")
    return set(ids) - {"junk"}


def playable_ids(source):
    matches = re.findall(r"(?m)^[ \t]*B\.PLAYABLE_IDS[ \t]*=[ \t]*(.*)$", source)
    if len(matches) != 1:
        raise ValueError("playable roster missing or ambiguous")
    definition = matches[0].strip()
    if not (definition.startswith("{") and definition.endswith("}")):
        raise ValueError("playable roster must be a literal list")
    tokens = [part.strip() for part in definition[1:-1].split(",")]
    if tokens and not tokens[-1]:
        tokens.pop()
    if not tokens:
        raise ValueError("playable roster empty")
    ids = []
    for token in tokens:
        match = re.fullmatch(r"([\"'])([a-z][a-z0-9_]*)\1", token)
        if not match:
            raise ValueError("nonliteral playable character id")
        ids.append(match.group(2))
    if len(ids) != len(set(ids)) or "junk" in ids:
        raise ValueError("duplicate or NPC in playable roster")
    return set(ids)


def catalog_errors(catalog, balance_source, required):
    errors = []
    active = catalog.get("characters")
    planned = catalog.get("candidates", [])
    if not isinstance(active, list) or not active or not isinstance(planned, list):
        return ["invalid character lists"]
    entries = active + planned
    if any(not isinstance(c, dict) for c in entries):
        return ["invalid character record"]
    ids = [c.get("id") for c in entries]
    if any(not isinstance(i, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", i) for i in ids):
        return ["invalid character id"]
    if len(ids) != len(set(ids)) or "junk" in ids:
        errors.append("duplicate/player-NPC identity")
    active_ids = {c["id"] for c in active}
    if not BASELINE_IDS <= active_ids:
        errors.append("baseline characters removed")
    try:
        if active_ids != registered_ids(balance_source):
            errors.append("catalog and executable balance roster disagree")
        if active_ids != playable_ids(balance_source):
            errors.append("catalog and playable HUD roster disagree")
    except ValueError as exc:
        errors.append(str(exc))
    for c in entries:
        if any(c.get(k) in (None, "", []) for k in required):
            errors.append("required identity/role missing: " + c["id"])
    for key in ("shape", "color"):
        values = [c.get(key) for c in entries]
        if any(not isinstance(v, str) for v in values) or len(values) != len(set(values)):
            errors.append("indistinct " + key)
    if any(c.get("status") != "prototype" for c in active):
        errors.append("active roster must report prototype status")
    if any(c.get("status") != "design_proposal_not_implemented" for c in planned):
        errors.append("planned characters presented as implemented")
    for c in entries:
        if c["id"] in BASELINE_IDS:
            continue
        business = c.get("business_case", {})
        effort = business.get("effort_points", {})
        appeal = business.get("appeal_scores", {})
        if (not business.get("acquisition_hook") or not business.get("retention_hypothesis") or
                business.get("evidence_status") != "HYPOTHESIS_NOT_MEASURED"):
            errors.append("unmeasured benefit must remain a hypothesis: " + c["id"])
        if (not isinstance(effort, dict) or set(effort) != EFFORT_KEYS or
                any(type(v) is not int or not 1 <= v <= 20 for v in effort.values())):
            errors.append("invalid effort estimate: " + c["id"])
        if (not isinstance(appeal, dict) or set(appeal) != APPEAL_KEYS or
                any(type(v) is not int or not 1 <= v <= 5 for v in appeal.values())):
            errors.append("invalid benefit estimate: " + c["id"])
        visual = c.get("visual_contract", {})
        budget = visual.get("primitive_part_budget")
        if (not visual.get("signature") or type(budget) is not int or not 1 <= budget <= 24 or
                visual.get("silhouette_pixels") != [32, 64]):
            errors.append("missing simple-shape visual budget: " + c["id"])
        if visual.get("native_render_verified") is not False:
            errors.append("native visual proof not supplied by this pipeline: " + c["id"])
        refs = c.get("source_review")
        if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x.startswith("https://") for x in refs):
            errors.append("primary reference review missing: " + c["id"])
    return errors


def assess(catalog):
    result = []
    for c in catalog.get("candidates", []):
        b = c["business_case"]
        a = b["appeal_scores"]
        effort = sum(b["effort_points"].values())
        benefit = 2*a["acquisition"] + 2*a["retention"] + a["strategy"]
        result.append({"id": c["id"], "name_ja": c["name_ja"],
                       "estimated_benefit_points": benefit, "estimated_effort_points": effort,
                       "estimated_priority": round(benefit/effort, 4),
                       "market_effect": "NOT_MEASURED", "native_visuals": "NOT_RUN"})
    return sorted(result, key=lambda c: (-c["estimated_priority"], c["id"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    catalog = json.loads((args.root/"config/characters.json").read_text())
    policy = json.loads((args.root/"config/quality_policy.json").read_text())
    errors = catalog_errors(catalog, (args.root/"src/ToyWarsBalance.lua").read_text(), policy["character_required"])
    report = {"status": "FAIL" if errors else "PASS_CATALOG_ONLY", "errors": errors,
              "runtime_characters": len(catalog["characters"]), "planned_characters": len(catalog.get("candidates", [])),
              "candidate_priority_hypotheses": [] if errors else assess(catalog),
              "scope": "No acquisition, retention, Roblox rendering or release certification"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
