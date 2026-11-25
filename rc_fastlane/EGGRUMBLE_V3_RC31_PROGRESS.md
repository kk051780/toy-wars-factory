# EGGRUMBLE V3｜正式RC31：統合・品質ゲート引継ぎ正本

- **OWNER 2026-11-16指示:** チャット上限で作者ACK待ちで中断しない。現担当が元作者の固定SHAを照合してそのまま統合責任を継続する。失敗する構文/同HEAD/一意Game・Remote・Store/破損リスクのREDは止める。main・Publish・課金・OWNER実機受入は別ゲート。
- **正式RCブランチ:** `rc/p0d-s1-kids-rc01`。この記録の基礎となる真正同HEAD確認済コミット `935e50f6e590c3bd783e2dc8aac947627f57fd5f`。
- **構成:** `rc_fastlane/ACTIVE.json.source_profiles.eggrumble_v3_31` と `rc_fastlane/EGGRUMBLE_V3_ACTIVE.json`、ビルドworkflow `.github/workflows/p0d-rc-eggrumble-v3-31.yml`。旧S1デフォルト `rich51`・既存Game/Store/SCORE/sourceは不変。現在V3は**正式RCブランチ上の独立companion profile**であり、Studio公開先のprimaryに切り替え済みではない。
- **統合作者（実source、重複禁止）:** 原本7職/城/卵/アイテム/ロビー #482；AI/ルート #484；ART/地形 #485；SCORE/バランス #487；中立供給 #494、遭遇公平 #501、4HP melee #533、TEAM/BR上限 #528；Hostの参加確認 #531；Combatの魔法回復 #510、遅延DOT #516、安全ワープ #524、人間透明PvP #529、死者スキル拒否 #530、現役ユーザ判定 #535。1 Game、1 Combat、1 Host、1 Swarm、1 BotActors。元30の29本は byte-identical、唯一Combat合成＋元#516 StatusTickFenceで31本。
- **同HEAD正式Actions:** [#43852865328 SUCCESS](https://github.com/kk051780/toy-wars-factory/actions/runs/43852865328)、RC HEAD `935e50f6e590c3bd783e2dc8aac947627f57fd5f`。Luau ON31/31 OFF31/31、実7職84/84、参加14、neutral meleeと共通予算Native、Rojo7.7.1 ON31/31 OFF31/31完全一致。
- **実成果:** `EGGRUMBLE_V3_RC31_CANONICAL_STUDIO.rbxlx` **240,416B** SHA256 `3046052d9930d0d5285b86ec588f835cd57f780ac3990560dca2624dd5c45f6d`。OFF31 **240,256B**。GitHub Actions ZIP artifact **#14218746773 =147,803B**（Placeの容量ではない）。
- **今後の取込ルール:** #220唯一ブランチwriterとして毎回最新HEADをfetch、非force compare-and-swap（Expected SHA一致を厳格化）、同一HEAD CIとPlace/ZIP実バイトを検証。前HEADに対応したCI結果を新HEAD合格とみなさない。新しい作者候補には源SHA・既存職/城/卵/ITEM/ART/SCORE影響・OFF戻しを照合。新規本線に重複のCombatやGameを増やさない。
- **未実施/NO_GO:** Roblox StudioのTEAM/BR 2client・ソロ1+15AIで実動作確認、Android低性能15分、PC/Androidアート4.5/4.0、FUN最初3分、OWNER受入。CI成功は人間の面白さや公開承認を意味しない。
- **発行・main/課金:** 未承認・未実施。企画67件の全件完了とは判定しない（旧31/67はS1履歴値）。

- **2026-11-16 #551 RC候補（正式#547後）**：#547城/卵看板と#536移動、#555 AIを保持し、#551作者固定SHAから同一Hostの死亡通知ガードだけを追加。実Native7・全31 Native/Rojo・他30完全一致の同HEAD CI必須。正式CAS採用/Studio/Android/FUN/OWNERは未完了。
