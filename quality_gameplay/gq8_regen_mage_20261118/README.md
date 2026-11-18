# GQ8 REGEN × MAGE crosslane 34-source compatibility (not another gameplay author)

Scope unique to #765: connect existing **#775 regen** to **#777 Mage downed-rescue** in one real original31 Host, without forking either owner. Distinct from #780 **Realm + Regen** crosslane. 31 baseline + #775 original two modules + #777 original one module = 34 scripts. Existing Host alone is patched (two ordered equip hooks); existing other30 and exact upstream Luau bytes preserved. No new Game, Combat, DamageOwner, Store, Remote or new job.

Upstream source locks:
- #775 HEAD `5b82f300e6dee08ea1ac20ccd1449db0cd73dbc3` is branch ancestry; its pure policy imports exact #773 Git blob.
- #777 Mage source HEAD `2f4c1e43a7802929de3f633370b32791f7bf8d96`, Lua Git blob `c75c2db439a5a68f2bc866ad42562fc16687849d`. Tested by SHA-1 Git blob formula.
- genuine official RC HEAD to be fetched anew in workflow (source changes => RED, never silently accept stale).
- ON34 requires existing original31+2 Regen33 source project. Mage original ModuleScript is supplied by pinned source-author checkout, not copied here. OFF31 is exact original31.

Why joint test: #777 sets `EGGRUMBLE_Downed` on the player/humanoid, #775 regen blocks on player downed, and both independently attach after `SevenRoleCombat.equip`. Without a single ordered Host hook merge, either module may be silently dropped, or duplicate Health writers created.

Remaining safety boundary: #777 initial down occurs only on **non-lethal <=20%** real HP; lethal HP0 still dies, so it is **not full revive-after-death**. #777 Mage skill currently remains existing +25HP (the desired 30%/18s combat heal is a separate unfinished integration). Studio/Android/FUN NOT_TESTED. Physical Roblox engine semantics and crosslane response to actual damage remain NO_GO.

Admission: exact author source, synthetic malicious mutation rejection, genuine same-head official31 source artifact rehydrate, original #775 composer real33, this composer ON34, pinned Native Luau compile, pinned Rojo7.7.1 real ON34 and OFF31 Script Class+Source exact, readback official HEAD. Only the one authenticated #220 writer can update formal RC via nonforce expectedSHA CAS; no original author ACK required. No main/Publish/paid actions.

This code is QA/compose-only, no duplicated owner Lua. Source-preparation success is not formal RC implementation or game-engine validation.
