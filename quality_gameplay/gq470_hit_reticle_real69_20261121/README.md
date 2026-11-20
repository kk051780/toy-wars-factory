# GQ470 / FB-015 — confirmed-hit centered matte reticle (REAL69)

## Original source scope

This **changes real selected Roblox Luau**, not solely a QA document. Input: original official RC e80973c354f14a0d0088577f3cc1a875454f0f8f, verified same-head [GitHub run 44695199140](https://github.com/kk051780/toy-wars-factory/actions/runs/44695199140), artifact 14610422120, 69 selected Luau sources, 798,390 B original private Place. PRIVATE_COMPANION does not replace S1 rich51 ACTIVE_RUNTIME.

One selected original LocalScript: StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel. Original SHA256 d378d6a356b9462c99deddc19b4393d79bf113225047a057658d1782e1e8a32e, candidate SHA256 ae43ff66055698dd72ccf6beb2aa3fcc61080e49343055b3d8cd3594831c0b1c. Source bytes 26,226 -> 26,683 (+457). Other 68 original selected sources, paths and classes are preserved.

## Actual visual change

The original reticle animates its HitConfirm parent from 12 to 26 px while four child ticks use fixed upper-left pixel coordinates. That causes 7 px diagonal center drift during real HIT expansion. New tick positions use center-relative UDim2.new(0.5,x,0.5,y), with four 2x9 px matte radial strokes. The transient server-confirmed ConfirmedHit042 label uses bounded 78x20 px matte typography, fixed 12px glyph size, and long CHAIN label truncation. No always-visible new HUD, Part, Remote, new GUI instance, extra connection/render loop, camera recoil change, scoring, or server authority change.

Reuse original #482/#503 CombatFeel; nonoverlap with #928 KO, #940 skill VFX, #943 role motion, #947 HUD, #939 atmosphere, #931 ART6 and other candidates. Scoped claim [#218 comment 7052865365](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7052865365).

## Reproducible gate

1. Download official run 44695199140 artifact P0D-EGGRUMBLE-V3-REAL69-CANONICAL-PRIVATE-STUDIO to local original directory.
2. Run: python3 -B quality_gameplay/gq470_hit_reticle_real69_20261121/patch_hit_reticle.py --self-test --base /path/to/original
3. Run: python3 -B quality_gameplay/gq470_hit_reticle_real69_20261121/patch_hit_reticle.py --base /path/to/original --out /tmp/hit-candidate
4. Local true original artifact: 69-route exact SHA lock, one selected LocalScript patch, 68 other sources byte-exact, inverse OFF69 original backup, 12 corrupted mutations rejected. CI additionally compiles Luau 69 ON + 69 OFF, builds pinned Rojo ON and byte-exact OFF original Place, checks source truth 48 historical flags and #420 source ART.
5. Native and Rojo status are PENDING until actual candidate workflow success. ZIP artifacts include real private candidate Place and B220_RETICLE_ONE_SOURCE_NOT_FORMAL one-source SHA manifest.

## Admission and truth

A branch is independent game source implementation; not an RC write. First #910 playable P0 and existing #931 ART6, then #250 ADOPT value decision, #220 sole authenticated writer reGETs official head, checks source class/claim/conflicts, uses nonforce expected-SHA CAS for selected one-script adoption, runs same-HEAD official CI, records actual Place/ZIP and rollback.

Studio solo, 2client, Android15, first3min fun, human ART and OWNER are NOT_TESTED. Real before-after screenshots 0/32. ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO / PRODUCT_NO_GO / OWNER_ACCEPTED=0. Source tests are not game quality acceptance. Neither direct-write official RC/main nor whole-PR merge blindly.


## Cross-chat SOURCE conflict resolution: #949 + #952 (preferred conditional B packet)

An independently authored [PR #949](https://github.com/kk051780/toy-wars-factory/pull/949) also edits this SAME selected original LocalScript, adding two matte diagonal confirmed-hit streaks and eliminated-player suppression. Its original author source is **reused**, not recoded. Pin #949 actual A HEAD d94e8852b0da3d3c65d671f8ea263ab042b11c8d, CI run 44834993878 SUCCESS, artifact 14677759742, exact one-source SHA256 860a8d60e7e577b7e5f01ca08b901290ec0a040beec63a46c66993ab71187dd3 (27,640 B). A second independent B source-write would overwrite one of these improvements.

The **preferred conditional combined** source is produced by compose_949_952.py: authentic #949 source, then the minimal #952 center/label transformation, ending at 28,097 B SHA256 **b37194cb97357cf7290fc6eb3f94396720265b15915ad588d2bd05b9b870e833**. From official original 26,226 B this is +1,871 B, the full sum of two features; selected source count still 69, exactly one LocalScript changed, 68 other sources exact. +2 noninteractive existing GUI child Frames, +0 world Parts and new loops/remotes/gameplay authorities. The standalone #952 patch SHA256 ae43ff66055698dd72ccf6beb2aa3fcc61080e49343055b3d8cd3594831c0b1c remains a *testable isolated source slice*, NOT the preferred combined B packet.

The updated same-head Actions workflow downloads both fixed genuine source artifacts and **rejects a changed #949 author HEAD**, then tests real combined Luau/Rojo ON/OFF and exact original rollback. B #220 must use the combined selected source manifest if both proposals pass #250 adoption; never independently apply #949 then #952 as blind competing one-source replacements. This resolves lane conflict without a second RC or unauthorized B write. Studio/Android32 camera images remain 0/32 and ART_NO_GO.
