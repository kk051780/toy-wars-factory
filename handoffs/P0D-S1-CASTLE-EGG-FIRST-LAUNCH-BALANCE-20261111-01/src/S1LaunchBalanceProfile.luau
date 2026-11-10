--!strict
-- P0-D S1 potential first-release balance profile, OPT-IN DATA ONLY.
-- NEVER load this script automatically, and NEVER create a second round/combat owner.
-- Does NOT modify Config until the unique #220 CHAT-INTEGRATOR reviews/chooses it.
-- Optimistic travel/attack estimates are not Roblox Studio or player data.
return table.freeze({
    CastleMaxHp = 420,
    CastleAttackDamage = table.freeze({
        RAIDER = 12,
        GUARDIAN = 10,
    }),
    -- All other S1 values stay exactly as in current Config.luau.
})
