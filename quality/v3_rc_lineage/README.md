# P0D GQ — latest-author RC lineage admission gate (2026-11-16)

**Unique claim:** #218 GQ-LATEST-AUTHOR-LINEAGE-20261116. This is NOT another #482 gameplay writer, #484 Rojo/private Place composer, #485 artist, #487 score engine, #488 device-evidence checker, #469 claim allocator or #220 official RC writer. It does not change source files in any of those owners' scopes.

## Why this exists

At receipt time #482's 7-role/field/battle/castle/neutral/items/lobby/balance author HEAD is
fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9.
#484's 21-source-composite candidate is d93be40675b27d39f2847c76e682c04eff68cf54, built against a **different, older** #482 HEAD.
Its successful **private source-exact** Place is not proof that current #482 (including one-original-boss-per-session module, item respawn and client poses) has been accepted into official RC.

This validator consumes actual Luau bytes and Rojo maps from an explicit **original author tree** and a **candidate tree**. It rejects:

- stale author_sha or rc_sha relative to independently retrieved current GitHub branch tips;
- omitted mandatory V3 modules (latest 19 server + 2 client source map), duplicate Game, wrong server/client placement, escaping paths and duplicate source paths;
- any replaced/added author module without one owner-scoped overlay with actual source SHA256, original SHA256, FEATURE ID, rationale and rollback;
- declared but untouched overlays, orphan overlay declarations and unpinned changed hashes.

It also reports eight **source inventory only** domains. They represent module presence, *not* feature behavior.

## How to use in the selective intake (do NOT wholesale merge)

Prepare two checked-out, immutable source trees AUTHOR and CANDIDATE (the latter may include claim-reviewed #484/#485/#487 overlay sources). Create an intake JSON:

~~~json
{
  "schema":"EGGRUMBLE_V3_RC_LINEAGE_V1",
  "author_sha":"<40-digit SHA from original #482 snapshot>",
  "candidate_sha":"<40-digit SHA for the exact reviewed composite>",
  "rc_sha":"<40-digit official RC snapshot>",
  "overlays":{
    "EGGRUMBLE_BotActors":{
      "owner":"#484",
      "feature_id":"FB-AI-NAV",
      "reason":"claim-reviewed collision fix",
      "rollback":"<recorded original commit or path>",
      "sha256":"<SHA256 of candidate Luau bytes>",
      "original_sha256":"<SHA256 of author Luau bytes>"
    }
  }
}
~~~

If there is no change to an author module, omit it from overlays. New ART/SCORE modules require their respective owner and actual SHA256. Do not waive author missing modules for source count convenience.

Run locally (Python 3.11+):

~~~sh
python quality/v3_rc_lineage/validate.py \
  --author-dir "$AUTHOR" --candidate-dir "$CANDIDATE" \
  --author-project "$AUTHOR/EGGRUMBLE_V3_STUDIO.project.json" \
  --candidate-project "$CANDIDATE/EGGRUMBLE_V3_STUDIO.project.json" \
  --provenance "$INTAKE_JSON" \
  --latest-author-head "$CURRENT_482_HEAD" \
  --latest-rc-head "$CURRENT_220_RC_HEAD"
python -m unittest discover -s quality/v3_rc_lineage -p 'test_*.py' -v
~~~

CURRENT_482_HEAD and CURRENT_220_RC_HEAD must be read directly from actual branch tips immediately before intake (e.g., git ls-remote). Never use self-declared candidate values. The push CI pins initially observed #482 and official RC SHAs; if either moves, it fails and demands fresh source selection.

## Progress/acceptance boundary

The following milestones are separate: (1) original per-domain source, (2) current source-lineage guard, (3) full source-selective composite and actual Rojo binary/source parity, (4) latest official RC authenticated CAS and same-HEAD CI/Place/ZIP, (5) Studio 1+15/2+14, Android 15m, visual/FUN, (6) OWNER final acceptance.

Passing this gate authorizes only source intake review, not integration into rc/p0d-s1-kids-rc01. Only #220 is authorized for official RC. This module has no main/RC write, publish, pay or game-SOURCE effects. For YELLOW changes, original owners keep feature flags/rollback, but missing ownership/current HEAD is RED in intake. Revert by discarding this independent branch/PR.

**Fixed source receipt at creation:** official RC HEAD d2f3ed1a47558fdaf07be0181c83c698bdb2ce34; #482 HEAD fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9; no official V3 integration is claimed.
