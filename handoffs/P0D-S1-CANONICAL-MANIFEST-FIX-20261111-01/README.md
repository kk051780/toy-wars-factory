# P0-D initial S1 manifest-only repair candidate

Original game fixed SHA: 35d7d0525388e885aac8281eff2315a59831e0cf
Original source directory: releases/P0D_S1_KIDS_RC01
Authoritative S1 integration owner: issue #220 (sole writer of rc/p0d-s1-kids-rc01).
Independent static QA blocker: issue #220 comment 6779832110.

## Defect and minimal fix

The source game's original BUILD_MANIFEST.json has seven root keys. Official
P0D_PUBLIC_SOURCE_V1 requires exactly six: files, format, game_id, packet_id,
public_source_allowed, work_id. The additional root "status" is forbidden by
the original p0d_public_pack.py verifier. Existing per-source file hashes are
still 15/15 valid; status already lives correctly in docs/RELEASE_STATUS.json.

BUILD_MANIFEST_S1_FIXED.json here is the proposed exact canonical manifest
regenerated from the original 15-file metadata, **with no source additions or
Luau changes**. Its original packet_id and all 15 listed digests/sizes remain
unchanged. #220 integrator may adopt ONLY after validating against newest own
game source and regenerating with the original official tool. Do not overwrite
newer releases or assume this fixes missing D07/D08/D11 or Studio tests.

## Safe test on disposable copy only

```sh
tmpdir="$(mktemp -d)"
cp -a releases/P0D_S1_KIDS_RC01/. "$tmpdir/"
cp handoffs/P0D-S1-CANONICAL-MANIFEST-FIX-20261111-01/BUILD_MANIFEST_S1_FIXED.json "$tmpdir/BUILD_MANIFEST.json"
python3 handoffs/P0D_PUBLIC_SOURCE_HANDOFF/tools/p0d_public_pack.py verify \
 --root "$tmpdir" \
 --packet-id P0D-S1-KIDS-RC01-SOURCE-INTEGRATION-20261111-01
```

An isolated branch GitHub Actions workflow separately runs the official
verifier, source SHA checks, original 80 Python tests, and actual Python
six-file source-assembly replay. It tests this repair in a temp copy and does
not modify the sole S1 integrated RC branch.

## Safety and proof boundaries

This packet is **a source-metadata patch candidate**, not a playable new build,
not evidence of original D07/D08 integration, no Roblox Studio QA and no
OWNER permission for release/paid operations. No PC Codex, main, P0-A/B/C CAS
or five existing automations changed.
