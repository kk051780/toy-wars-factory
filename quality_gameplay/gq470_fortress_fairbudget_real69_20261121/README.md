# #470 FB-015 | Fortress identity under the real 320-part cap

Feature: `GQ470_FORTRESS_VISUAL_FAIR_BUDGET_REAL69_20261121`
BASE: `e80973c354f14a0d0088577f3cc1a875454f0f8f`
SELECTED: `ServerScriptService/EGGRUMBLE_FlagshipFieldArt` (single existing Script, no new runtime Script)
BEFORE: `d77fdaf390506f87dfea3064611898320288690f4ef14b97f4e8416eaef40395`.

Original selected REAL69 has **existing** 3-route 12-part silhouette art; duplicate PR #932 was rejected. Original landscape yields 140 decorative parts: 24 route waystones, 12 lane identities, 80 trees, 20 rocks, four ruins. Original **19** visual components per castle, up to **16** heroes. 140+16×19=444 exceeds the **320** per-arena cap. Original code paints the landscape before castles and later castles can lose even roofs/entrance/crest as the budget fills.

This surgical source-select patch does **not create or remove any original feature**. It reserves the initial ten already-existing castle identity pieces: 4 roofs + door keystone + two buttresses + two cornices + one team-colored heraldic crest. Subsequent optional RC86 finial/slit/banner parts are added opportunistically, then reclaimed by later castle creation only when necessary. No collision, camera/UI, egg, HP, store or remote changes, and no added Parts. The mobile 320 total and the 19-detail per-castle original code are preserved.

Worst-case 16 castle base art + existing landscape = 16×10+140=300. With independently planned #916's twelve ridge wedges: 312, leaving eight spare (if #916 is adopted). This is a *source-model upper-bound argument*, not actual measured Part count or FPS. Every real visual frame and source identity still requires Studio/Android inspection.

The local-source negative QA uses the exact immutable original official artifact from #44695199140, 69 selected source hashes/classes, exactly one changed source, exact OFF original copy including Place, second-apply rejection, 16 castle arithmetic and destructive mutations. GitHub workflow additionally attempts pinned Native Luau69 ON/OFF and Rojo69 ON/OFF with inverse Place. Both source and visual gates must be independently labeled.

**Admission rule:** DRAFT A PREP, not official RC. #916 alters the *same* FieldArt author at a separate hunk, so B #220 must compose it from latest official source, independently test all 69, preserve original 48 feature inventory and 17 family receipts, and use authenticated fresh SHA nonforce CAS. No wholesale PR merge. P0 playable loop #910 and #931 art6 already in the queue take priority. Studio solo/2client, 32 real comparison images, low-end Android15min, kid FUN, human ART score and OWNER acceptance remain **NOT_TESTED/NO_GO**.
