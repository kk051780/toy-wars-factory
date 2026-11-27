
local function observe(held, last, t, enabled, donorReady, receiverReady, label)
    now = t
    session.rules.eggRelayLastAt["42"] = last
    session.rules.castles["42"] = { heldEggs = held, alive = true, isAI = view.isAI }
    joined[42] = view.joined or mode
    refresh()
    assert(relayPrompt.Enabled == enabled and values.EGGRUMBLE_RelayPresentationReady == donorReady
           and values.EGGRUMBLE_RelayPresentationReceiverReady == receiverReady, label)
    print("PASS", label)
end
view.humanoid = 100
observe(2, nil, 100, true, true, true, "two_eggs_allow_both")
observe(3, 100, 112, true, true, false, "full_blocks_receive_only")
observe(0, nil, 100, false, false, true, "empty_blocks_donation_only")
observe(2, 100, 111.999, true, false, false, "cooldown_hides_without_disabling_server_prompt")
observe(2, 100, 112, true, true, true, "exact_twelve_seconds")
observe(2, 120, 100, true, false, false, "future_last_clock_rejected")
view.eliminated = true
observe(2, nil, 100, false, false, false, "eliminated_clears_both")
view.eliminated = nil
view.joined = "BATTLE_ROYALE"
observe(2, nil, 100, false, false, false, "incorrect_mode_clears_both")
view.joined = nil
view.humanoid = 0
observe(1, nil, 100, false, false, false, "knocked_out_clears_both")
