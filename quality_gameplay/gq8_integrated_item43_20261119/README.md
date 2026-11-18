# GQ8 latest successor: REAL42 weather + REAL43 neutral8 + 3D item pickup

## 2026-11-19 live integration discovery: already selected Item source

The immutable #796 WEATHER42 source already contains the **exact #812 GQ802 marker** in the original FieldItemPickups. An initial real CI caught `RED_GQ802_DOUBLE_PATCH`. This is **not** a request to produce another Item controller or to patch the same code twice. The successor composer now validates the existing inverse and reapplication, preserves the existing Item source **byte for byte**, and combines only original #815 Swarm+Policy into a 43-source private candidate. `item_already_present_in_weather42=true`, `changed_existing=[]` in the second stage. If the next official source lacks the original Item patch, its exact #812 patch can be selected once with strict rollback.

Status remains **NO FORMAL RC ADOPTION**. The private Real42 and Real43 source bytes do not become official until the separately authenticated B #220 CAS, same-head build, readback and receipt.

FEATURE_ID: GQ8_REAL42_WEATHER_NEUTRAL43_ITEM_SCULPTURE_SOURCE_INTAKE_20261119

**No parallel game subsystem is invented.** This is an integration-only slice not covered by upstream #796 (weather/castle/stage), #815 (neutral/finisher), or #812 (item preview on old Core36).

Inputs are exact immutable original author/DRI sources:
- #796 latest HEAD 34cafed1cb9e92e08bbc8f2afa67d50ae52a083a; run44319450066 portable WEATHER42, 42 original scripts, retaining #809 siege, #811 stages, #814 weather, #764 air/sea and original seven jobs.
- #815 latest HEAD a8bc2ba30bf67515282ae27de2814c1bc6dbab89; original composer blob 0f712d05533f5744cd95ac147c8c14a5bf6f67fe, neutral8 single-Swarm candidate blob 3f1359b8fa7413bf6885d634d5c9da06190f2e90; #801 unchanged original NeutralFinisherPolicy blob 42f512c4aaa389e0027be774c327e1f5a106aabf.
- #812 HEAD be1dbb2f9707d53d7f5ecd5e25e0ce5ef31ac2a8; original reversible Item visual patch blob 2c81da640d465d27630840be2f1f5245bc7cd5db.

Composition is **42 -> 43 neutral (existing Swarm patched + one author policy) -> 43 item visual (existing Item only)**, then a self-contained portable43 project with same 43 source routes/classes. Original 42 weather unchanged at first stage. Original neutral43 all other 42 sources unchanged in second stage, including the single Swarm/HP/KO/Score/Host/Store/Remote. It uses the existing 3 HEAL/DASH/SHIELD pickups, not new pickups/rewards. Item visual effect is reversible by running #812 inverse against the selected item; OFF43 is the untouched neutral43 original.

CI must verify authors' fresh HEADs and official RC f77b4d..., source git blobs, source-mutation negative cases, native ALL 42/43/43/43 Luau compile, actual source-derived three-item native VM, Rojo Source/Class ON43, OFF43, portable byte-identical Place and exact source routes.

**Official RC adoption is NOT implied by this PR.** Certified B #220 must select and land this portable 43 source into only formal rc/p0d-s1-kids-rc01 using authenticated non-force expected-SHA CAS and official same-HEAD build/lock/OFF/ZIP receipt. Never merge this PR as a whole to the main branch. Do not publish Roblox / turn on purchases. Studio two clients, Android 15min FPS, child FUN and owner acceptance are untested.

Handoff: successor Chat continues from this existing FEATURE_ID and PR without any original author ACK. On stale author HEAD or formal RC movement, update the source pins and revalidate before final B CAS, never override newer owner/source. 
