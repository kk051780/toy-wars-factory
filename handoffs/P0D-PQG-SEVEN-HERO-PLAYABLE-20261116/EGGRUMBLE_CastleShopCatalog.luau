--!strict
-- EGGRUMBLE concept catalog. NO PURCHASES HERE. No product IDs, prompts, or cash handling.
-- OWNER wants optional pre-match castle defense, house building, and monetization without unfair strength gaps.
-- All competitive modules are earnable for free, and use the SAME slot/point/HP budget.
local Catalog={}
Catalog.CORE_CASTLE_HP=1000
Catalog.CASTLE_LAYOUT="STANDARD_COMBAT_SHELL"
Catalog.MAX_DEFENSE_SLOTS=3
Catalog.MAX_DEFENSE_POINTS=10
Catalog.MAX_EFFECTIVE_EXTRA_ENDURANCE=50 -- <=5% of 1000HP. HARDENED and REPAIR exclude each other.
Catalog.PAID_POWER_MULTIPLIER=1 -- no direct paid castle durability
Catalog.defenses={
 HARDENED={label="盾装甲",cost=5,type="shield",benefit=50,unlock="PLAY_OR_OPTIONAL_KIT"},
 REPAIR={label="応急修理",cost=5,type="repair",benefit=50,unlock="PLAY_OR_OPTIONAL_KIT"},
 TURRET={label="迎撃砲塔",cost=4,type="counter",unlock="PLAY_OR_OPTIONAL_KIT"},
 TRAP={label="防衛トラップ",cost=3,type="control",unlock="PLAY_OR_OPTIONAL_KIT"},
 SENSOR={label="監視装置",cost=2,type="intel",unlock="FREE"},
}
Catalog.cosmetics={
 CASTLE_SKIN_SAKURA={name="桜城スキン",kind="pass",payToWin=false,affectsHitbox=false},
 CASTLE_SKIN_SKY={name="天空石の城スキン",kind="pass",payToWin=false,affectsHitbox=false},
 FLAG_PACK={name="武将旗・紋章セット",kind="pass",payToWin=false,affectsHitbox=false},
 HOME_BUILDER_SET={name="マイホーム装飾パーツ",kind="pass",payToWin=false,affectsHitbox=false},
 TURRET_VISUAL_PACK={name="砲台演出・弾道スキン",kind="pass",payToWin=false,affectsHitbox=false},
}
Catalog.homePlan={
 maxDecorPieces=48,editableWithinPlotStuds=24,decorationsNoCombatCollision=true,
 combatCoreIsIdenticalForAll=true,roofBannerGardenStatuesWindowsOnly=true,
 modularWallsAllowedOnlyOutsideEggRoutes=false,
}
Catalog.policy={
 noPaidRandomDefense=true, noPaywallForBestDefense=true, freeEqualMaxBudget=true,
 noPurchasesDuringMatch=true, requireClearShopLabels=true,
 neverModifyRemoteOrDataStoreSchemaFromCatalog=true,
}
return Catalog
