# GQ470 FB-014/015 — REAL69 First90 microcue A PREP

Scope: existing selected LocalScript StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90; one changed source, zero new scripts, Remotes or server authority. All other 68 selected routes must remain byte-identical to sole formal RC e80973c354f14a0d0088577f3cc1a875454f0f8f.

Visual risk: a 210x43 BillboardGui can occupy the avatar's view during the first ninety seconds. Mobile readability and combat line-of-sight are unmeasured. This is a source fix with a defined human art gate, not a beauty assertion.

Actual patch: 184x36 3D cue and less opaque background, 4.5s after a semantic cue change, 24s selection reminders ONLY before role/mode acknowledgment, max 90s, Studio-only, AlwaysOnTop=false, server-owned role/mode attributes unchanged. No per-frame render callback or new Part/GUI instance. Existing elimination, respawn and teardown handling retained. A late initial Head and changed respawn Head each re-arm the bounded 4.5-second cue once, while an unchanged Head cannot keep hints visible across polls.

Tests: exact original SHA, one-source source-select, byte-exact inverse rollback, synthetic cue timing edge cases, corrupted source mutation rejection, optional real69 source receipt/OFF check. source_lock.json is not a formal admission certificate.

Not yet measured: actual first-time-player readability, Studio Solo/2client, Android FPS/heat, 32 before/after PNGs, human art evaluation, FUN, product release, OWNER acceptance. All NOT_TESTED/NO_GO.

B gate: sole #220 authenticated integration after P0 #910 and incumbent ART6 queue, fresh formal head, proper source-lock, nonforce expected SHA CAS, official same-head CI/Place/ZIP. No whole-PR merge, no Work, Codex, Publish or payment.

Other scopes excluded: #924 BotActors, #925 SocialPlaza, #926 Foliage, #928 KO, #929 weapons, #930 giant, #931 art composite, #933 canyon, #934 fortress, #916 ridge.
