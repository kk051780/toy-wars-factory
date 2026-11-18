# GQ8 / Cross-lane compatibility rehearsal (2026-11-18)

**Scope:** independent verification of two *already owned* game features, not another runtime implementation. PR #764 owns RealmCore+land/sea/sky; PR #773 owns pure HP policy; PR #775 owns its Host integration. The single formal RC writer remains #220. This branch changes no old game source, no main, no official RC HEAD and no feature flags.

### Exact source composition

1. Retrieve a **genuine official successful same-HEAD** V3 31-script Rojo Place and receipt. Rehydrate its exact 31 Script/ModuleScript/LocalScript sources and class/route metadata.
2. Run original **PR #764 fixed head `c51de1ed4feb7a7500ada95d21282402053ef988` composer** for Realm34, with the current official LSS original source. It must preserve all 31 existing scripts byte-for-byte.
3. Run original **PR #775 fixed head `5b82f300e6dee08ea1ac20ccd1449db0cd73dbc3` composer**, including the exact #773 HP policy blob. That produces 33 scripts, changing precisely the original Host (one import plus two equip hooks) and adding two module sources.
4. This QA tool selects the 31 sources (Regen33 Host, other30 exact) plus the three **unchanged Realm34 addon sources**, for total **36**. It checks for five exact addon routes, no Game/Combat/Swarm replacement, no unknown Host change or extra authority, and exact SHA256 provenance of every source.
5. Synthetic negative tests catch realm-edit of an old source, regen-edit of Combat, a third HP hook, missing import and missing Realm module. **The real Actions workflow additionally compiles all 36 Luau scripts and runs actual Rojo36+OFF31 Source/Class exact comparison**. A missing or stale same-HEAD official31 source is RED.
6. Reverting the rehearsal simply omits all five added scripts and restores the official31 byte-identical selection. **Neither this rehearsal nor a green CI means source integration into the official RC or Studio/Android/FUN acceptance.**

### Integration risk addressed

Individually green PR #764 (31->34) and #775 (31->33) do not prove one compatible 36-source Studio Place. Both must be admitted as source components by the one #220 writer, with full rebase and one non-force expected-SHA CAS. This QA report gives that writer evidence before any formal write.

### Progress

- Local structural and mutation tests: CI pending.
- Genuine same-HEAD Source/Native36/Rojo36/OFF31: CI pending.
- Official 36 adoption: **NO**; #220 exclusive.
- Studio 2 clients, Android 15 min, ART/FUN, OWNER acceptance: **NOT_TESTED**.
- Feature implementation status is inherited only from the upstream original PRs, never counted as a new runtime feature.

Feature ID: `GQ8_CROSSLANE_REALM_REGEN_COMPOSITION_QA_20261118`.
