# P0D RC｜競合作業ガード・即時選択採用記録（2026-11-15）

OWNER方針：稼働速度優先、非重複の複数ライターを条件付きで許可。品質ゲート #470 は不合格を見つけて終わらず、元作者のゲーム実修正→正式RC統合→Studio/Android/競合比較→OWNER合格まで対応する。

## SOURCE_LOCK / 採用対象

- Original source: PR #469 HEAD `35faf7291beba68c5b23aeda2cac1387b1c0bf40`
- Adopt **only** identical Git blobs: `tools/p0d_work_claim_guard.py` and `tests/test_p0d_work_claim_guard.py`.
- These are deterministic/offline fail-closed collision checks of FEATURE_ID/resources/real target path, owners, expiry, official source SHA and duplicate reservations. No Game/HUD/HP/egg/Store/MapBuilder or Rojo changed.
- Existing #473 `multiwriter/guard.py` checks separate writer/expected-head CAS proof. This #469 subset is the *pre-work claim collision* layer, not a second RC writer or duplicate implementation.
- **Do not adopt PR #469 workflow yet**: it assumes all PRs already have coordinator-issued grants while real `coord/p0d-work-claims` currently contains `claims=[]`. Enforcing this workflow now would reject all work and slow development. Retain source & unit tests; activate workflow only after protected trust source and owner grants are live.
- Do not adopt PR #469's stale sole-writer prose; the OWNER 2026-11-15 multiwriter policy supersedes it. Existing original author PRs and settled feature claims are reused; same-feature reauthoring is prohibited.

## Production activation remains fail-closed

RC branch and coord branch reported `protected=false`. Code presence or this note does **not** grant GitHub credentials or enable extra production writers. Require trusted branch rules, authenticated actor, unique short-lived scope, source-exact same-proposed-commit CI and nonforce expected-head CAS. Wrong/old expected head aborts. No main/Roblox publish/paid functionality/Windows operation authorized.

## Verification

Run `python3 -m unittest discover -s tests -p 'test_p0d_work_claim_guard.py' -v` for source-only unit tests. On this RC change, existing source-locked unified Studio build is triggered by the new `rc_fastlane/**` record; its success/failure must be verified on the new official HEAD rather than borrowed from older RC82. Official RC source changes here are governance-only; gameplay quality remains PRODUCT_NO_GO until actual live owner acceptance.
