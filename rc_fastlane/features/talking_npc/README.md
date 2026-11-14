# P0D-TALKING-NPC-V1: しゃべるAI生命体 / PREP source-only

- Owner idea: #333 ; umbrella #219 ; adoption gate #250 ; sole canonical RC writer #220.
- Current status: **SOURCE candidate only**. NOT wired to official RC, Studio, TTS, UI, models, or saved data. DO NOT mark PREP_READY.
- New pure Luau: TalkingNPCDirector.luau. Direct deterministic announcements for NAVI/ALLY, TRICK/ENEMY, ORACLE/NEUTRAL.
- Security: no raw coordinates, no raw player speech or free-form prompts; team-observed facts only (caller responsibility). Secret hints are explicitly unlocked. All data defaults closed.
- Backwards compatibility: no changes to existing Game, Remote, Store, combat, rewards, saves, or RC build. OFF = do not require or invoke this module.
- Next implement by A: server event adapter reading existing Game visibility and match facts, per-player bounded dispatch with 25s normal/5s urgent cooldown, subtitles, AudioTextToSpeech, mobile controls, scene-attached 3D. Resolve Japanese TTS voice support and quota. LLM optional future phase only.
- Caution: Roblox child-friendly content. No unbounded AI chat; long conversation or session-memory generative AI may require Restricted 18+ rating. No unverified AI runtime promises.
- Test gates: Luau syntax, server authorization and hidden enemy/secret non-disclosure, nil/OFF, bad enums, TTS fail to caption, event spam, 2-client, Android, Studio. None completed here.
- Fixed BASE_RC at branch creation: 44b2df61e8452790dc491466d3efbab5e7fb2e8e. Rebase when formal RC HEAD changes.
- No copy of Minecraft Verity voice/character/style assets. Distinct P0D characters.
