# GQ8 PROMPT REACH — unique, reversible source candidate (2026-11-17)

Target: **EGGRUMBLE_InteractionGuard** only, original author #482 fixed HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, original blob `ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe`.
Base official RC HEAD when authored: `9466312436d9567db8bb464a57b664d133f6a6cf`.

### Confirmed gap
The original common server-side ProximityPrompt gate uses a fixed `MAX_DISTANCE=16` plus 1.3-stud surface tolerance even though the actual lobby/castle/egg prompt is configured at 14 studs. In multi-mode play this makes some prompt actions executable from farther away than their own server-owned prompt limits.

### Concrete source repair
Use the **enabled, server-owned matching ProximityPrompt.MaxActivationDistance** as a hard upper bound (also keep the preexisting global 16-stud cap), with the unchanged 1.3-stud geometry tolerance. Reject missing, disabled, duplicate or invalid prompt settings. Preserve every verb cooldown, line-of-sight raycast, alive check, and human/session callsite. No second Prompt, Game, Remote, Score, Store, or AI authority.

Original source ON/OFF remains exact by `verify.py`. Only one existing Guard module is replaced in the canonical *31* script project when the sole #220 integrator adopts this candidate. Do not add a 32nd runtime script. Other 30 canonical scripts must be byte-identical.

### Gates
- Same HEAD CI: `.github/workflows/gq8-prompt-reach-20261117.yml` (native Luau compiler + original Git blob + exact reversible selector).
- Formal 31/31 current canonical Luau/Rojo/source exact and official RC same-HEAD artifact/receipt: **PENDING sole #220 nonforce CAS**.
- Studio 2-client / Android 15-minute / kid FUN / owner: **NOT TESTED / NO_GO**.
- Off/rollback: reselect original author blob `ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe`, keep other 30 sources byte-exact.
- RED: original source drift, syntax/native fail, >1 selected Guard or duplicate gameplay owners. YELLOW: visual/engine scenario pending; do not call final quality PASS.

Owner/author per-feature acknowledgement is not a blocking condition; RC branch writes remain exclusive to #220. Do not merge this PR, merge main, publish Roblox, or spend money.
