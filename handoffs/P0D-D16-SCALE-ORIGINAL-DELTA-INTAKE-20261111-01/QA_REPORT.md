# D16 Original ScaleFx Delta Intake — QA

- Scope: new independent Python-only immutable commit/manifest/source validator and isolated local staging helper.
- Offline local regression: 13/13 PASS (`python -m unittest discover -s tests -v`), 2026-11-11 JST.
- Cases: positive fixture; read-only source extraction; output receipts; output overwrite denial; destination within repo denial; wrong manifest SHA; non-40-character ref; wrong game packet; duplicated paths; tampered file SHA; symlink; traversal/hidden paths; incompatible ScaleFx Lua; valid git commit source.
- Immutable original source: `584b11ef24cf3d44695d86b505207491bbd3844e`; previously recovered in another chat and source verified independently by its author. **This helper is not another original-source recovery**.
- Real original commit present on Windows local clone: NOT_TESTED.
- Windows staging/actual PC receipt: NOT_TESTED.
- Native Luau / Studio / 2client / mobile: NOT_TESTED.
- Real actor scale/game integration: NOT_TESTED.
- GITHUB HEAD CI / independent P0-A review: NOT_TESTED.
- Outcome: standalone keyless **source-intake helper candidate** only. Do not bypass P0-A/CAS, main, merge, publish or payment restrictions. Do not install incompatible cleanroom/original scale implementation concurrently.
