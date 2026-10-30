# A14 — GitHub Actions current-source RBXLX export (candidate, not verified by engine)

This addition is the missing **portable GitHub Actions artifact producer** for an XML place using accepted current-main Luau sources. It does not create another Rojo build-only workflow, does not modify the accepted build/handoff workflow, does not merge PR #143 or #145, and never contacts Roblox.

## Actual effect on the existing CI runner

`.github/workflows/bootstrap-quality.yml` already executes `python3 -m unittest discover -s tests -p 'test_*.py' -v` and, in an `if: always()` step, uploads `.qa/auto/` under artifact name `twf-autonomous-regressions-not-engine`. The new `test_system_xml_artifact_export.py` exports exactly two files **into that existing folder during a source-pinned PR run or a real main push run**:

- `twf_source_pinned_NOT_ENGINE_VERIFIED.rbxlx`: version-4 Roblox XML place, ten instances, four original accepted Luau source bytes and a RemoteEvent.
- `twf_source_pinned_UNTRUSTED_receipt.json`: four SHA1 Git blob and SHA256 content pins; XML size and digest; no engine/upload/publish or authentication claims.

Every other test checks isolated temporary folders and never touches real game source. If source files are modified from their accepted Git blob hashes, the generation fails. There is no new token, network call, deploy step, schedule, or workflow change. This is an **UNREVIEWED PR Actions artifact until the workflow/code itself is independently reviewed**. Merely finding the filename inside the artifact is not proof of engine acceptance or genuine supplier identity.

## How to verify at the point of handoff

1. Review exact PR HEAD and ensure the `offline` and `compile_hold` jobs succeeded. Confirm `.github/workflows/bootstrap-quality.yml` was the job workflow and the run matches that HEAD.
2. Fetch native Actions artifacts for the run, find `twf-autonomous-regressions-not-engine`, note its real artifact ID and `digest=sha256:...`.
3. Download the original artifact ZIP and hash it against the native digest. Read the XML and receipt, verify their digests and the four Git Blob SHA1s by independent GitHub GET on the accepted main. Ensure 10-instance XML topology, no extra scripts or DTD, and four embedded Source hashes.
4. The **separate protected PR #145 XML Saved-only adapter** should accept the bytes and the exact pinned source/sha/size. This verification can be done offline before any Roblox secret is used. Results from this PR do not attest PR #145 or Studio support.
5. Only after independent protected review and actual authorization of a nonpublic test universe/place and a scoped API key, a reviewed one-shot runner may issue `versionType=Saved` to Roblox. No publishing to production and no automatic retry on uncertain API outcomes.

## Explicit HOLD

Before a real independent, authenticated Roblox result: `studio_open_verified=false`, `roblox_engine_verified=false`, `roblox_upload_attested=false`, `public_publish_authorized=false`. A successful GitHub XML artifact is not a `Rojo .rbxl`, Roblox runtime proof, mobile/2-client proof, protected source merge, or A14/G08 gate closure.

Upstream primary references: https://create.roblox.com/docs/projects/place-files ; https://github.com/rojo-rbx/rbx-dom/blob/master/docs/xml.md .
