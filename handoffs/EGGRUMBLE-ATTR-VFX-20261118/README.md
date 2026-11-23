# Current official69 → attribute71 SOURCE continuation (2026-11-23)

This continues original PR #778 / `BATTLE_ATTR_VFX_20261118`. The historical
REAL31/33 implementation and evidence below remain historical. This preparation
adds two client presentation sources to the immutable official69 input; it does
not merge the old branch wholesale or replace the canonical producer.

## Player-visible behavior

Confirmed local-player casts can display a brief elemental silhouette near the
current character. The existing server signature is the only trigger.

| Existing role/slot | Cue |
| --- | --- |
| MAGE A | ICE |
| MAGE B | FIRE |
| MAGE C | LIGHTNING |
| WARRIOR C | DIVINE |
| ZOMBIE C | CURSE |

The renderer retains eight descriptor silhouettes and its old public API. The
live adapter has these five mappings only; peer visibility, HIT, weakness,
shield results, and eight-element gameplay are not implemented by this change.
No server, HP, XP, inventory, purchase or entitlement source is changed.

## Bounded lifecycle repair

- Evict the oldest owned cue **before** parenting a new anchor. Live anchor peak
  is eight, including the ninth render's allocation boundary.
- Keep at most eight Beams per PC cue or four per Touch cue, and the original
  independent Debris deadline of at most 0.9 seconds.
- `Visual.clear()` is idempotent and removes this module's owned anchors only.
  Detached or expired references are pruned before another valid render.
- Seed the currently observed cast signature on attachment. Preserve the largest
  observed sequence for the **current LocalScript runtime** across roles,
  characters and rounds. Do not replay consumed sequences after return.
- Capture concrete player, arena, character, root, castle/core and camera
  identities. Rebind using existing events, explicitly disconnect old callbacks,
  and clear cues when delivered lifecycle events invalidate that binding.
  CharacterRemoving retires the specific current character before its actual
  removal; delayed events for an older character cannot retire the new one.
- Own-script teardown is best effort. A script's own Deferred Destroying callback
  may not execute after that script has been destroyed; external Debris still
  bounds cue lifetime. No heartbeat/polling loop or fabricated server epoch is
  introduced. The signature has no epoch, so these tests do not establish
  arbitrary network-order or arbitrary script-restart replay immunity.

## Exact official input and rollback

The reviewed input is defined in
`quality_gameplay/gq778_attribute_visual_current69_20261123/source_lock.json`:

- official RC `72d620d86761f2aa5da80263a251cc5fa63fecbb`;
- successful official push run `45132949073`, artifact `14798134590`;
- ZIP 7,144,237 bytes / SHA256
  `d178f62489f275831da86eaceda8b8ce1fba6a8ccf86366bd86cb8c5507a926b`;
- original Place 829,213 bytes / SHA256
  `cacc922501717c417c05e60bdf3c32c6d917e3622931401ab45fc8eeed3da3c5`;
- all 69 source paths, byte hashes, instance routes and classes are locked.

This input explicitly follows the adopted Bot PR1027 update. Compared with the
prior H93 evidence, the official project, 68 source bodies and all 75 instance
non-Source property records are unchanged. The existing BotActors source is retained at
19,625 bytes / SHA256
`c38bcf82df581d2d9f105f9d7843eef0eff8e8bd6315b8520765ee646e1c5051`.
The original client/module/fixture logic is unchanged by this input rebind.
The old H93 SOURCE evidence remains historical; it is not relabeled H72.

ON71 preserves all 69 source bodies and all 75 original instances and non-Source
properties, adding only `ReplicatedStorage/EGGRUMBLE_ElementVisuals` and
`StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AttributeCue` (77 instances total).
OFF69 rebuilds the original project, all source files and Place byte-for-byte.
The builder imports source files only from the hash-verified ZIP, rejects unsafe
paths and duplicate members, and publishes into a new exclusively created
directory. It never overwrites an existing output directory.

Rollback is the exact OFF69 profile, or removal of precisely the two additions
and their project entries from the standalone ON71 composition. Canonical/RC
rollback is outside this SOURCE preparation and requires its own reviewed scope.
If the official parent moves, its current artifact and the explicit same-claim
base/input amendment must be reviewed before source publication or adoption;
changing the hash alone is not a rebind.

## Reproducible source evidence

Normal artifact-free discovery executes pure integrity contracts and explicitly
skips only the external official-input class:

```bash
python3 -B -m unittest discover -s tests \
  -p test_gq778_attribute_visual_current69_20261123.py -v
```

The dedicated gate requires the exact official ZIP. It builds fresh Luau from
`f46d879e28302a430029304f7f6a162aed66f103`, verifies tracked source blobs and its
tree, compiles ON71 and OFF69 (140 compiler invocations), runs full unmodified
source bodies, checks targeted failure mutants, and builds both profiles with
checksum-pinned Rojo 7.7.1:

```bash
python3 -B quality_gameplay/gq778_attribute_visual_current69_20261123/native/run_current71.py \
  --artifact /path/to/official.zip \
  --luau-source /path/to/clean/pinned-luau-checkout \
  --rojo /path/to/verified-rojo \
  --out-dir /path/to/new-evidence-directory
```

The full-body fixture has 140 observation checks, including eight renderer
cases and 192 actual mocked renders. Its 61 original/repaired expectation
differences include Immediate/Deferred repetitions and cumulative observations;
they are not 61 distinct bugs. Original observations confirm known defects;
running the original against the repaired contract must fail. Thirteen isolated
behavior mutants must also fail. The unchanged original descriptor generator
is executed separately and its budget mutant remains a required failure.

The dedicated workflow checks actual GitHub run/artifact provenance and the
same source HEAD, then rechecks the official parent before publishing evidence.
A failed gate retains failure evidence; neither a local report nor uploaded
artifact issues independent source approval. The old current31 workflow is kept
unchanged and can reject the now-69-source official RC. Its historical result is
not presented as current all-PR green.

## Acceptance status

Product direction: conditional SOURCE adoption recorded at #2507093588802.
Source scope request: #2187093506118. Issuance, a separate SOURCE lease,
registered independent same-HEAD review, canonical selection, unique RC writer,
and official same-new-R artifact acceptance remain distinct operations.
This README does not grant those operations. Studio, Android, ART/FUN and OWNER
acceptance require their own actual same-R evidence.

---

## Original 2026-11-18 record (preserved)

# BATTLE-ATTR-VFX — eight attribute silhouettes (lane 2 / #765)

**State:** isolated native client presentation + optional REAL31->ON33 / exact OFF31 candidate; **NOT canonical RC**, **NOT Studio/Android FUN certified**.
**Feature:** BATTLE_ATTR_VFX_20261118
**Unique claim:** #765 comment 6968039688; #766 owns affinity mathematics, #770 its original31 bridge; #775 owns passive HP; lane8 owns MAGE revive. This lane does not touch those files.

## Actual LuaU
- `ElementVisuals.luau` (ReplicatedStorage ModuleScript) exports `describe(element,kind,outcome,lowEnd)`, `capacity()`, `render(element,kind,outcome,position,lowEnd)`.
- Eight *visually different outlines* beyond hue: FIRE jagged flame, WATER wave, LIGHTNING broken zigzag, WIND curled current, EARTH angular rock, ICE snow-crystal, DIVINE closed halo, CURSE chain-and-hook.
- WEAPON / ATTACK / SHIELD presentation. ADVANTAGE thick/double-pulse metadata, RESIST thin, IMMUNE diagonal slash. Actual HUD text for those outcomes belongs to #765 lane3, not this writer.
- A rendered cue uses exactly one invisible anchor and at most eight short camera-facing Beams (at most four on low-end). Maximum eight active cue anchors, Debris cleanup in 0.42–0.9s. No gameplay collision, bright box/sphere filler, persistent FX, or costly world scan.
- New `EGGRUMBLE_AttributeCue.client.luau` (StarterPlayerScripts) subscribes only to existing server-written `EGGRUMBLE_SkillCastSignature`. The server skill IDs from #482 confirm Mage A=ICE, B=FIRE, C=LIGHTNING, Warrior C=DIVINE, Zombie C=CURSE. Unverified role/slot attributes are **not painted**. Existing signal means cast only, so this adapter renders ATTACK/NORMAL, **never claims real HIT, immunity or multiplier**. Other 3 visual contexts are API-ready pending server-confirmed gameplay event.
- No new RemoteEvent or damage owner. Invalid IDs/outcomes fail closed; nil camera/server calls render nothing.

## QA evidence / rollback
- Native source-derived Luau test runs all 8 elements × 3 presentation kinds × 4 outcomes = **96 descriptor combinations**, rejects indistinguishable geometry, tests low-end beam cap and no overlong object lifetimes.
- Deliberate mutant raising 8 active FX to 88 must fail with `RED_BUDGET`, proving the bound is tested.
- Actual candidate composer `quality_gameplay/gq8_attribute_visual_real31_20261118/compose_real33.py` appends just two real scripts to current original31 ON33 / restores exact OFF31; existing 31 original scripts byte unchanged, no combat or serialized state migration. Formal intake is still only by #220 after same-head CI.

## Formal RC adoption request to unique #220 integrator
1. Re-fetch latest `rc/p0d-s1-kids-rc01` SHA and this candidate's source SHA. Before adoption, inspect #765 lane2/3 and any newer presentation owner to prevent overlap.
2. Reuse the existing `ElementVisuals` ModuleScript plus `EGGRUMBLE_AttributeCue.client` LocalScript. Original server `SkillCastSignature` is enough for five **verified cast-only** elemental flourishes, not actual Hit. Any added advantageous/resistant/immune outcome callback must come from an existing verified server hit/shield event, never client arithmetic. Do **not** create a second damage/hit/score/attribute/HP authority.
3. Compose original31+two presentation scripts (ON33), verify class/source and exact OFF31; compile true Native and Rojo same HEAD. Perform source lock, nonforce expected-SHA CAS and official HEAD readback **only using #220 authorized writer**.
4. Verify in genuine Studio 2-client: 8 outlines, weapon/attack/shield, advantaged/resisted/immune differentiable without color, no phantom HIT, camera/round destruction, children HUD not obscured. Low Android 15-minute FPS/memory and first 3 minutes of FUN remain YELLOW until measured; this preparation does not imply a pass.

## Eight-domain coordination
Character = immutable 7 roles; Field = no world edits; Battle = only visual layer; Castle = no HP writes; Neutral = no hit claim; Items = future confirmed weapon visuals; Lobby = no UI writes; Balance = #766 multiplier source not copied. Sole writer #220 handles formal RC. MAIN, publish, monetization, and spend untouched.
