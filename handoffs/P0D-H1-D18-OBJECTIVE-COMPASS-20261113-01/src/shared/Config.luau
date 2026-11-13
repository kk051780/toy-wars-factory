--!strict
-- TRAP RAIDERS S1: one authoritative match / objectives / damage controller.
return {
    MinPlayers = 2,
    IntermissionSeconds = 7,
    MatchSeconds = 360,
    ResultsSeconds = 9,
    CapturesToWin = 2,
    CastleMaxHp = 300,
    CastleAttackDamage = {RAIDER = 14, GUARDIAN = 10},
    CombatDamage = {RAIDER = 24, GUARDIAN = 18},
    RoleHealth = {RAIDER = 100, GUARDIAN = 135},
    RoleWalkSpeed = {RAIDER = 19, GUARDIAN = 15},
    AttackReach = 10,
    CastleReach = 18,
    AttackCooldown = 0.85,
    RoleSelectCooldown = 2,
    -- Guardian trap numeric authority lives in S1TrapRules; client cannot override it.
    RespawnInvulnerability = 2.5,
    InteractDistance = 12,
    SnapshotInterval = 0.5,
    TeamColors = {
        RED = Color3.fromRGB(231, 82, 88),
        BLUE = Color3.fromRGB(71, 149, 241),
    },
}
