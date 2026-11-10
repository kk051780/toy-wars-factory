# P0-D S1 multi-authority source assembler compatible fork

game_id: TRAP_RAIDERS
work_id: p0d-siege-v19
source_v2_commit: ae80548d0c6905b4ee35e7cdedd3928d344ff239
reason: https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-6778426109

The V2 source assembler accepts one singular `authority` per real source unit. The current S1 `Game.server.luau` legitimately owns ROUND + EVENT_CHOOSER + DAMAGE. This fork adds an optional plural `authorities` array **for the same real source unit**, preserving legacy `authority` behavior and the one-global-owner-per-authority check.

Example declaration (replace placeholders with actual immutable source evidence):
```json
{
 "unit_id": "s1_game_server",
 "source_commit": "<40HEX_SHA>",
 "source_path": "<REAL_FILE>",
 "target_path": "src/server/Game.server.luau",
 "sha256": "<ACTUAL_SHA256>",
 "authorities": ["round", "event_chooser", "damage"],
 "depends_on": []
}
```

Do NOT provide both `authority` and `authorities`. Invalid/empty/duplicate/unknown roles, `none` within an array, or a second owner of the same role are rejected. This is source metadata only, not proof that the Luau runtime has a unique server authority. Independent static/dynamic QA must inspect real game scripts.

Files preserve the V2 original except for the authority declaration/receipt compatibility hunk and additional tests. Run `python -m unittest discover -s tests -v` to run the inherited V2 regression suite plus 12 new tests.

No write to original V2 branch, S1 RC branch, main, PC, Studio, protected P0-A/B/C, automations, or public game. The #220 integrator and V2 author must review and choose this compatible fork or refactor actual S1 code, not duplicate scripts or fake owners. SOURCE CANDIDATE ONLY; actual assembled RC and Roblox Studio still NOT_TESTED.
