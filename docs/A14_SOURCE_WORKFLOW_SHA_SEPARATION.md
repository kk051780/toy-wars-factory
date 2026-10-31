# A14 — source-vs-workflow SHA split for protected PR145

The accepted original game source commit remains pinned to e5deff4d5681bca4823a3da0f848e01bc089ae6e. A later independently reviewed main workflow has a different SHA. These are independent identities.

`XmlStageConfig.reviewed_workflow_sha` is a required SHA-shaped syntax value, while `source_main_sha` remains the exact original source pin. The host syntax checks `GITHUB_SHA` against reviewed workflow SHA; accepted game source pin against `TWF_ACCEPTED_GAME_SOURCE_SHA`; and independent reviewed workflow SHA against `TWF_REVIEWED_MAIN_SHA`. All environment variables are caller-controlled and do NOT constitute provider authentication, security approval, or a real main-installed protected workflow. The hosted host must authenticate the original GitHub run and private test target independently before a Saved-only Roblox request.

Parent PR145 must undergo exact-head CI and independent reviewer. Child PR148 must be restacked preserving ALL 41 original child test methods, strict XML root/Properties allowlist, unique referents, original Lua source checks, and append-only histories before protected integration. There is no engine or Roblox API operation in this change.
