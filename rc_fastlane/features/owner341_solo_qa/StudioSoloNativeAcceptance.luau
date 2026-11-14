--!strict
-- This is appended to the ACTUAL composed StudioSoloPreviewRules.luau,
-- never a reimplementation of the policy. No Roblox engine APIs are mocked.
local cases = 0
local function expect(name: string, actual: any, expected: any)
    cases += 1
    assert(actual == expected, name .. ": unexpected " .. tostring(actual))
end

-- Normal two-team starts are the same in Studio and on public servers.
expect("public_balanced", Solo.canStart(false, 2, 1, 1, 2), true)
expect("studio_balanced", Solo.canStart(true, 2, 1, 1, 2), true)
expect("public_one_red", Solo.canStart(false, 1, 1, 0, 2), false)
expect("public_one_blue", Solo.canStart(false, 1, 0, 1, 2), false)
expect("studio_one_red", Solo.canStart(true, 1, 1, 0, 2), true)
expect("studio_one_blue", Solo.canStart(true, 1, 0, 1, 2), true)
expect("studio_no_team", Solo.canStart(true, 1, 0, 0, 2), false)
expect("studio_empty", Solo.canStart(true, 0, 0, 0, 2), false)
expect("studio_two_red", Solo.canStart(true, 2, 2, 0, 2), false)
expect("studio_two_blue", Solo.canStart(true, 2, 0, 2, 2), false)
expect("studio_invalid_team_sum", Solo.canStart(true, 1, 1, 1, 2), false)

-- The solo tag is latched at round kickoff, not recomputed when others quit.
expect("solo_latched_red", Solo.isSoloRound(true, 1, 1, 0), true)
expect("solo_latched_blue", Solo.isSoloRound(true, 1, 0, 1), true)
expect("public_not_solo", Solo.isSoloRound(false, 1, 1, 0), false)
expect("balanced_not_solo", Solo.isSoloRound(true, 2, 1, 1), false)

-- One-player Studio practice cannot instantly be ended by an empty team.
expect("solo_red_no_empty_winner", Solo.emptyWinner(true, true, 1, 1, 0), nil)
expect("solo_blue_no_empty_winner", Solo.emptyWinner(true, true, 1, 0, 1), nil)

-- Real/public or multi-player rounds must preserve team-empty resolution.
expect("public_empty_blue", Solo.emptyWinner(false, true, 1, 1, 0), "RED")
expect("studio_multiplayer_red_survives", Solo.emptyWinner(true, false, 1, 1, 0), "RED")
expect("studio_multiplayer_blue_survives", Solo.emptyWinner(true, false, 1, 0, 1), "BLUE")
expect("studio_balanced_no_winner", Solo.emptyWinner(true, false, 2, 1, 1), nil)
expect("solo_tag_but_two_red", Solo.emptyWinner(true, true, 2, 2, 0), "RED")
expect("solo_tag_but_no_red", Solo.emptyWinner(true, true, 1, 0, 0), "BLUE")
expect("public_balanced_no_winner", Solo.emptyWinner(false, false, 2, 1, 1), nil)

assert(cases == 24, "P0D_STUDIO_SOLO_CASE_COUNT_MISMATCH")
print("P0D_STUDIO_SOLO_ACTUAL_POLICY_NATIVE_24_CASES_PASS")
