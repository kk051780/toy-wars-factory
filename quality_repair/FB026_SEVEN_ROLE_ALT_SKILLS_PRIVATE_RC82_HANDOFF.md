# FB026｜7職業ごとにサーバー実動作する補助技を追加（PRIVATE RC82）

**OWNER 2026-11-15 19:58 JST「つぎ」**。直前のFB025魔獣AI付きPrivate Placeを親に、追加のGame+HUD 2源を修正して7種の実技能を同一Placeへ累積。元Game/Game Remote/卵/勝敗/KO権威は再生成しない。

## 完成・配布した現物
- 元FB025 Place: 837563 B、SHA256 `0fdb6932be2d33eb1711d80d8b4a4c9a56be86b05f95faa818c482541e0c54df`。
- **新FB026 PRIVATE Place:** `TRAP_RAIDERS_RC82_FB026_SEVEN_ROLE_SKILLS_PLAYTEST.rbxlx` **853236 B**、SHA256 `df162246344f69a614763bf9eecfcad78340c3bee04a023c3c111e9810ccd318`。
- **USER配布ZIP:** `TRAP_RAIDERS_RC82_FB026_SEVEN_ROLE_SKILLS_PLAYTEST.zip` **239724 B**、SHA256 `ff08651c4f6ea7a76aa47f0435b85317933495203d2911e0b7914f567c7bee7d`。実Studio Place + byte-identical `SOURCE_PATCH.py` + 元Source受渡し `RECEIPT.json` を含む。公開repoに実Place・Game全源は未転載。
- 実82 Scriptのうち改造した源2本のみ:
  - `Game` blob `a2ebd9471d2ae4ceef7d4026b3c67b5fad68a460`→`5ed828ce4e3dc5d080165d17830d57b24aa19c9a`。
  - `TrapRaidersHUD` blob `6e667a0680aff26de3833a473512b228d1702377`→`79c5c12f1f36e755926f6b9c7b4f7dd605d4d351`。
  - 残80源全body byte-exact。旧FB020風走り/FB021持武器/FB022門内/FB023Tool/FB024物理出撃/FB025魔獣のソースを1バイトも巻き戻さない。
- **独立静的70/70 PASS**: parent hash pin、XML再読/82source inventory、80源一致、Game single Remote & Q保持、X PC/touch、7技実状態、チーム/フェーズ/承認済職/Server時間/CD/死亡/卵制限/ラウンドcleanup、既存AI/Gate/Loot/Lobby保持、ZIP bytes・パッチ再生同値・二重パッチ拒否。

## 補助技の実Luau追加（Q=既存、X=新規。スマホは小型ボタン）
| 職 | X実効果 | Server側の管理 |
|---|---|---|
| 戦士 | 5秒ForceField実ダメージ防御 | Healthをclient経由で書かず、タイマー終了で撤去 |
| 魔法使い | 22stud内の同チーム生存者を最大38HP回復 | Server Humanoid.Health/Team/範囲検証（蘇生は今回未実装） |
| 暗殺者（内部NINJA） | 6秒透明化、元Horde・野生魔獣の索敵除外 | Serverの実部品Alpha・元AI健康判定ラッパー、期限で復帰 |
| トラッパー | 最初のXでserver地面帰還点、2回目Xで実Root転移 | 24s anchor TTL/105stud上限、地面server Raycast/卵所持禁止 |
| 建築士 | 地面に本当の実体衝突壁（8.5×6×1.5） | objective 25stud禁止、他人への巻込み検査、同職1枚/死亡・試合終了cleanup |
| 魔獣使い | QのFOLLOW/GUARD/ATTACKを保持、Xで真正召喚か即ATTACK指示 | 元FB025Companion1体上限/本物Horde:hit |
| ゾンビ使い | 2体の3Dゾンビが19s移動・中立兵へ本物Horde:hit | 元Game0.5s tick内のみ/HP0→本物個人KO計上、Team/Job/epoch/退出cleanup |

## 安全/未完
- 実ゲームの入り口へ新しい `JOB_ALT_SKILL` action を**唯一の既存Remote**に分岐追加。サーバ職・TEAM・ACTIVE・生存・非卵運搬・非拘束・CDを検査。クライアントの標的/ダメージ/位置を信用しない。スマホ用ボタン88×51pxは戦闘時だけ表示し、旧ロビー常駐巨大UIは復活しない。新Heartbeatなし。
- **Native Luau compiler/Rojo/Roblox Studio1&2client/Android/本物のFUN/ART・OWNER受入すべて NOT_RUN**。これはPRIVATE `REAL_SOURCE_PATCH + STATIC_TEST_PASS`であり、製品合格や正式RC採用ではない。
- **原案全項目未達**。魔法の蘇生、建築士橋/門補修、暗殺者PvP背面効果、罠師設置罠の追加戦術、ゾンビ支配の完成は次の元設計照合・実機検査まで残す。別能力の追加で既存技の動作合格を偽装しない。
- 既存元作者 #297 / #366 / #376 / #373 にcurrent Game/HUDへの局所diffを非競合受渡し。公式RCは #220認証済みwriterのみが同HEAD native/Rojo/Source Lock確認後、非force CAS。YELLOWは負債管理して開発継続、RED（構文/多重authority/SourceLock/CAS）停止。main/無断merge/公開/課金/追加費用は禁止。

**次の最短バリデーション:** Studio開いて7職Q+X操作→実ダメージ/回復/AI/ワープ/防壁/移動→帰還・リスポーン・次試合clean。動かない機能があればFB026を直し、OWNER合格までCLOSEDにはしない。
