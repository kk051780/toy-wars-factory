# Test and evidence contract

`python -m unittest discover -s tests -v` from packet root exercises synthetic ZIPs only. These are *not* any of the four real legacy ZIP contents.

States:
- `MISSING_ORIGINAL` — expected filename not found in owner-supplied directory.
- `SOURCE_REJECTED` — exists but wrong filename/size/SHA, unsafe path/symlink, corruption or disallowed bytes.
- `ORIGINAL_ZIP_SHA_VERIFIED_NOT_GITHUB_SOURCE` — verified original ZIP outer hash and member safety; original source not yet published.
- `ORIGINAL_ZIP_STAGED_NOT_GITHUB_DELIVERED_NOT_STUDIO` — isolated local staging only.

Final migration requires a distinct `PUBLIC_SOURCE_V1` source commit, actual `BUILD_MANIFEST.json`, remote all-file byte+SHA readback, and a separate Windows Codex receipt. The game-wide status stays incomplete while any old packet is absent.
