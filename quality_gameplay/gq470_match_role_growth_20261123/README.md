# GQ470 / P0D033 S1A：試合内のB1–B3成長

この候補は、中立KOから導出した試合内の覚醒BとXPを、既存の戦闘・HUD・頭上表示・結果表示へつなぐものです。企画PR #1025 の `c09670984f8f1f418f4dce3fc1a68018cc55bc37` に基づく **S1Aの限定実装**です。永久Lv・XPの接続、B4/B5、PvP成長、巨大化・スキル変更を含むS1全体の完成ではありません。

## ゲーム内の変更

| 中立KO | この試合の覚醒 | この試合のXP |
|---:|---|---:|
| 0 | B1 | 0 |
| 1–3 | B2 | KO×10 |
| 4–7 | B3 | KO×10 |
| 8以上 | B3 | 80 |

唯一の加算元は既存Swarmの `kills` です。追加のKO/XP台帳やRemote、保存処理はありません。死亡では累積値を保持し、終了・退役時にその試合が所有する一時公開値を解除します。旧 `BattleLevel=min(50,1+floor(KO/25))`、Combo、MUSOU、ダメージ計算、移動、順位と得点は保持します。

- Swarmは具体的なPlayer、現在のmembership、試合固有の公開tokenを確認します。重複Diedを消費済みとして拒否し、FINISHED後や旧試合の遅延通知からcredit・新試合の属性を書き換えません。純読取りgetterは属性解除後も既存の最終KOを返します。
- Heroは `この試合 B3｜中立KO4` の単一タグを表示します。距離上限72、AlwaysOnTop=falseです。死亡・隠密・終了・退出・帰還前は非表示とし、実Hostが現在のアバターを実arenaへ戻したことを確認します。Head交換・旧callback・古い隠密timerを世代で遮断し、旧5接続と新しい所有接続を退出時に解除します。役職の装飾と部品数は変更しません。
- HUDは既存status幅、y43–55に `覚醒B2 XP10/80` を追加します。既存の0.16秒更新処理を使い、新規購読は0です。拡大map・探索toast中は追加行だけを隠し、HP/Buffs・MUSOU・mounted544・既存LegacyExploreの3接続を保存します。
- 結果は既存の2行・94px・8秒表示を維持してBを追記します。順位・報酬・再表示retry・KOスナップショットは変更しません。

## 入力・差分・権限の境界

正式入力はRC `93a1147561a531610ac1609ebc68cc0ecf546623`、成功run `45106580546`、artifact `14787568439` です。ZIP、project、69ソース全体を固定しています。変更はSwarmCombat、HeroSilhouetteArt、HudIntelRuntime、MatchResultServiceの4本、残り65本はバイト一致します。

登録claimは `P0D-GQ033-MATCH-GROWTH-20261123-817BC984`、registry commit `30baf9dcad1eb86b34a06a3eb050eba9a0e11c8e` です。9個の追加repository pathと4個の生成sourceだけが対象です。作者は別の実SOURCE lease epoch679を取得して作成しています。これらの記録は作成時の来歴であり、期限後の書込み権限を与えません。登録・lease・ローカル試験は独立SOURCE承認やRC書込み許可の代わりにはなりません。

`apply_growth.py` はすべての入力を検証してから、新しい出力ディレクトリだけへ書きます。既存出力・入力との重なり・symlink・余分なsource・4本以外の変化を拒否します。各hunkは一意で、逆適用により69ソースとprojectを元に戻します。公式artifact内の過去PASSレポートは候補出力へコピーしません。

```bash
python3 -B quality_gameplay/gq470_match_role_growth_20261123/apply_growth.py \
  --input /absolute/path/to/official-h93 --out /absolute/path/to/new-on
python3 -B quality_gameplay/gq470_match_role_growth_20261123/apply_growth.py \
  --input /absolute/path/to/new-on --out /absolute/path/to/new-off --reverse
```

## 再実行可能な品質ゲート

専用workflow `gq470-match-role-growth.yml` は実PR headをcheckoutし、公式run/artifact/ZIPを検証してON/OFFを生成します。次に固定Luau source commit `f46d879e28302a430029304f7f6a162aed66f103` の全2,336 tracked fileとtreeを確認し、新しいbuild directoryでReplとCompile CLIを構築します。任意のprebuilt Replは受け入れません。

| 検証 | 実行内容と合格条件 |
|---|---|
| 入力の拒否・復元 | 実H93を使う8試験。同classのInstance間でSourceを交換したPlaceも拒否する。改変Host、改変対象source、余分なsource、symlink、既存出力、重なり、改変project、二重適用を拒否し、全文逆適用を確認 |
| 既存回帰 | 元の固定combined10件とobjective7件をH93・ON・OFFで全実行。旧fixture、旧case、旧lockは編集しない |
| server | 28個の完全な実body。16固定経路でKO閾値・25KO旧Lv・重複Died・真の致死通知の終了後配送・旧Player/旧試合・実Host respawn・Immediate/DeferredのDestroy/detach/reattach/abandon・偽Player/観戦者を検証 |
| AI補助 | ONだけ30個の完全な実body。BotPathRouter/BotActorsを追加し、実初期AI・実退出takeover・元loopからの中立KOと元得点、同UserId新Playerへの書込み0を確認 |
| UI | 31個の完全な実body。固定194期待値・12 CASEのID/順序/statusとNative exitをすべて照合。7役職、14画面、Head交換、隠密、帰還、退出、結果、callback数を確認 |
| 負例 | H93とOFFも同じcandidate-green UI条件で実行。82 RED /106 NOT_REACHED /6既存PASS、最終CASE FAIL、Native exit1と正確な失敗理由が必要。serverはON16経路、H93/OFFは各1経路で実開始時の欠落を確認。H93/OFFの残り15経路は同じ初期欠落で停止するため本CIの実行対象・合格件数へ含めない |
| compile・Rojo | H93/ON/OFFの69本を各compile。固定Rojo7.7.1で3 Placeを構築し、69 embedded source bytesと75 instanceの非Source構造を検査。OFF/H93 Placeは元artifactの828,658 bytesとSHAまで完全一致 |

各Nativeプログラムのbody全byte範囲、実行binary、全source、固定case、stdout/stderr、終了コードと最終HEADをreceiptへ記録します。実repositoryがcleanかつ指定HEADと一致することを開始前と終了後に検査します。候補は新S1A契約で審査し、改変したsourceが過去の未変更source契約を通ったとは記録しません。

## 残る確認と非対象

**ACTIVE_RUNTIME=rich51 / PRIVATE_COMPANION=REAL69_UNION22 / RUNTIME_UNIFIED=NO** を維持します。現パッケージは候補作成と検証用で、canonical producerや共有profileを変更せず、正式RCを更新しません。PREP_READY、正式SOURCE承認、RC採用はそれぞれ別途、実HEADに対して確認が必要です。

Nativeは実ソース全bodyを固定して実行しますが、エンジン境界はfixtureです。選択した信号だけをDeferred化しており、実Robloxの全scheduler・物理・ネットワークを証明しません。UIは寸法演算で、実フォント幅、折返し、safe area、遮蔽、アニメーション、タッチは未確認です。MapIntelとmounted Realmは明示した表示入力です。core server28には従来のBotActors stubが残り、実AI/takeoverは別30-body補助試験として実行します。補助試験のPathfindingは利用不可の境界入力で、元bot loopをschedulerで1 tickずつ進めるため、実ナビゲーション・物理の保証は含みません。

追加の平面CFrame逆変換は実無回転arenaのengine API補完だけです。製品の入場・B・XP判定はfixtureへ移していません。Heroの到着監視は正式Hostによる明示CFrame代入に対応し、一般の物理移動通知を保証しません。

既存の320×260拡大mapとstatusの重なり、永久Lv/XPの未接続、上位Bや巨大化の未実装は残ります。既存 #815 の移動・#825 のMUSOUとのsource合成は別途検証しても、相手の実装所有権やRC採用許可を取得したことにはなりません。正式統合には既存ownerとのexact-source intakeと再審査が必要です。

**Studio=NOT_TESTED / Android=NOT_TESTED / ART_NO_GO / FUN=NOT_TESTED。** ここでのPASSはsource・Native・Rojoの範囲に限定されます。
