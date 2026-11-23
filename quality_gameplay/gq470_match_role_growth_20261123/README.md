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
- Heroは `この試合 B3｜中立KO4` の単一タグを表示します。距離上限72、AlwaysOnTop=falseです。死亡・隠密・終了・退出・帰還前は非表示とし、実Hostが現在のアバターを実arenaへ戻したことを確認します。Head交換・旧callback・古い隠密timerを世代で遮断し、旧5接続と新しい所有接続を退出時に解除します。役職の装飾と部品数は変更しません。既存deferと0.35秒delayは、同じ登録record・Players配下・現在Characterの3条件を満たす場合だけ装飾を作り、退出後の予約から復活させません。
- HUDは既存status幅、y43–55に `覚醒B2 XP10/80` を追加します。既存の0.16秒更新処理を使い、新規購読は0です。拡大map・探索toast中は追加行だけを隠し、HP/Buffs・MUSOU・mounted544・既存LegacyExploreの3接続を保存します。
- 結果は既存の2行・94px・8秒表示を維持してBを追記します。順位・報酬・再表示retry・KOスナップショットは変更しません。

## 入力・差分・権限の境界

固定する過去の正式入力はRC `93a1147561a531610ac1609ebc68cc0ecf546623`、成功run `45106580546`、artifact `14787568439` です。ZIP、project、69ソース全体を固定しています。変更はSwarmCombat、HeroSilhouetteArt、HudIntelRuntime、MatchResultServiceの4本、残り65本はバイト一致します。

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
| 入力の拒否・復元 | 実H93を使う原10試験と、歴史capsule専用の3試験。source root自体のsymlinkと、入力sourceの別名へ向けた出力も、書込み前に拒否する。同classのInstance間でSourceを交換したPlaceも拒否する。改変Host、改変対象source、余分なsource、symlink、既存出力、重なり、改変project、二重適用を拒否し、全文逆適用を確認。capsuleは不正な全入力、使用した展開rootの改変、canonical treeを含まないown9だけのGit環境を別に検証 |
| 既存回帰 | 元の固定combined10件とobjective7件を、H93の元4fixtureで2実行し、追加SERVER_ENGINE境界のH93/ON/OFFで6実行する。計8プログラム・68 CASE。追加境界でも元case全文と実28 bodyを使い、旧fixture・case・lockは編集しない |
| server | 28個の完全な実body。16固定経路でKO閾値・25KO旧Lv・重複Died・真の致死通知の終了後配送・旧Player/旧試合・実Host respawn・Immediate/DeferredのDestroy/detach/reattach/abandon・偽Player/観戦者を検証 |
| AI補助 | ONだけ30個の完全な実body。BotPathRouter/BotActorsを追加し、実初期AI・実退出takeover・元loopからの中立KOと元得点、同UserId新Playerへの書込み0を確認。seed11を実body読込前に固定し、製品と同じLOS条件で4方向×3studの接近候補を調べる。全候補blockedは失敗する |
| UI | 31個の完全な実body。固定213期待値・12 CASEのID/順序/statusとNative exitをすべて照合。元194のID/順序/status投影を保持し、実効Adornee、footerの可視祖先、第二の実NINJA Bの自然期限、退出後のdefer/delay、同UserIdの別Player、遅着Torsoと所有接続の後片付けを19項目追加。7役職、14画面、帰還、結果も確認 |
| 負例 | H93とOFFも同じcandidate-green UI条件で実行。88 RED /111 NOT_REACHED /14 PASS（元194は82 RED /106 NOT_REACHED /6 PASSを保持）、最終CASE FAIL、Native exit1と正確な失敗理由が必要。serverはON16経路、H93/OFFは各1経路で実開始時の欠落を確認。H93/OFFの残り15経路は同じ初期欠落で停止するため本CIの実行対象・合格件数へ含めない |
| compile・Rojo | H93/ON/OFFの69本を各compile。固定Rojo7.7.1で3 Placeを構築し、69 embedded source bytesと75 instanceの非Source構造を検査。OFF/H93 Placeは元artifactの828,658 bytesとSHAまで完全一致 |

固定実行数は旧回帰8＋server19（H93=1、ON=17、OFF=1）＋UI3の計30 Nativeプログラムです。Replの新規buildが成功した直後にbuild receiptを保存するため、後続の失敗時にもビルド成功と試験失敗を別々に追跡できます。全試験後のbinary不変確認は、全必須検査が終わった場合だけ記録します。

各Nativeプログラムのbody全byte範囲、実行binary、全source、固定case、stdout/stderr、終了コードと最終HEADをreceiptへ記録します。実repositoryがcleanかつ指定HEADと一致することを開始前と終了後に検査します。候補は新S1A契約で審査し、改変したsourceが過去の未変更source契約を通ったとは記録しません。

## 保守修正の来歴と試験起動

同PR #1028の保守取込みは、registry `ba990f45b28d2a03f5b56a185f1aeb48ae99f743` で元9 paths／4 resourcesの範囲に登録しました。metadata688は本人正常返却済みで、C1の実装には別SOURCE689、C2の2guardとUI受入拡張には別SOURCE692を取得しています。この記録はその実作業の来歴であり、期限後の書込み権限ではありません。H93を固定入力とする候補で、進行中の正式RCへの再結合・採用を示しません。

- [3BEの提案7093566582](https://github.com/kk051780/toy-wars-factory/pull/1028#issuecomment-7093566582)から、既存safe_root呼出し1行と2拒否試験を再利用しました。実作者は `CODEX_ROOT_3BE5DD5649C8:/root/planning_candidate` です。
- [9DBCの提案7093568289](https://github.com/kk051780/toy-wars-factory/pull/1028#issuecomment-7093568289)から有限LOS helperと呼出し置換を再利用しました。公開提案者は `CODEX_ROOT_9DBC77FA535A`、実コード作者のcontextは未明示です。seed11の固定は当817の追加で、元提案の作者へ帰属させていません。
- unittest discoveryで `GQ470_H93_ARTIFACT` が存在しない場合だけ、原10試験のclassは実artifact未提供を明示する `NOT_RUN` skipにします。空文字・空白・不正なpath・改変入力は失敗です。新しいcapsule3試験は別classで、artifact未提供のdiscoveryでも実行します。ファイルの直接実行では未指定も失敗し、専用workflowでは実artifactを指定して全13試験を実行します。

C1 `fe13d7e6e3bd5d35b72c5aa69b969c3cd9099a8c` は専用run45135503785で新規build・固定30 Native・207 compile・3 Placeを通過しました。これはそのHEADの履歴であり、後続C2の合格へは流用しません。

C2 `64bb83572123eb4d90b7dfa82b556e18a3a9d0ff` は[3575の2guard提案7093711079](https://github.com/kk051780/toy-wars-factory/pull/1028#issuecomment-7093711079)を取り込みました。実作者は `CODEX_ROOT_3575F3C03022:/root` で、原904 Bのsource差分と一致する2条件更新です。Heroは31183→31285 B、他3生成sourceは不変です。新しいtimer・購読・装飾部品は追加しません。専用run45139061950の固定30 Native・207 compile・3 Placeと、登録非作者の[当該HEAD限定SOURCE受入7092737271](https://github.com/kk051780/toy-wars-factory/pull/1028#issuecomment-7092737271)はC2の履歴です。C3以降のHEAD、current-RやRC採用への合格転用はしません。

新19項目は実行前に列挙し、元194項目のIDと相対順序を保持します。実効Adorneeとfooterの祖先条件は共通helperを厳密化するため、旧predicateの意味まで不変とは主張しません。NINJAは元early-clear検査に加え、実Bをもう一度実行し、属性の手動書換えやframe入力なしで自然期限を確認します。役職予約は実defer/delayの引数・thread・時刻を保持する観測だけを挟み、callbackを包む・手動呼出し・再予約することなく、元schedulerによる8予約の実配送を確認します。

[19943の札配置案7093537940](https://github.com/kk051780/toy-wars-factory/pull/1028#issuecomment-7093537940)は75°/Combo条件で重なりが悪化したためREWORKとし、元cameraY2.6・178×24の配置を保持します。C2は配置修復やStudioでの描画合格を含みません。

## C3：H93の歴史入力を現行repositoryから分離

この保守は既存677 grant・688の原9path保守・696の `original_s1a` partitionの範囲です。実SOURCE703を別に取得し、変更をREADME、native INPUT_LOCK／runner、既存test、既存workflowの5pathへ限定しています。原期限11:08:12.461550 UTCを延長する記録ではありません。03の永久プロフィール支援9path、共有canonical6、ゲーム4本文、patch／source lock／applier、growth_casesの9sectionsは変更しません。

旧runnerが直接読んでいたH93由来の入力を、既存 `native/INPUT_LOCK.json` の `historical_inputs` に原UTF-8本文とともに固定します。originはcommit `93a1147561a531610ac1609ebc68cc0ecf546623`／tree `ca7a6b532ff325ebf125423484dde1ee57ce219b` です。元helperが間接参照する `objective_full_cases.luau` も含め、対象は11本です。現在のcanonicalが変更されても、その本文へfallbackしません。

| 歴史入力 | 本数 |
|---|---:|
| 元 `run_profile.py` と `INPUT_LOCK.json` | 2 |
| 元のcombined／objectiveのclear-LOS caseと元objective case | 3 |
| 元fixtures配下のmanifest・case・4つのengine body | 6 |
| 合計 | 11 |

runnerは外側lockの固定SHAを検証し、全11memberの名前・path・field・origin・UTF-8・bytes・SHA256・Git blobを照合してから、一つの新しい `--historical-root` へ展開します。rootやancestor、memberのsymlink、既存root、余分なentryを拒否し、repository・公式入力・toolchain・build・outputとの重なりも展開前に拒否します。歴史Pythonのimport前に同じ物理11本を再確認します。

実行後は**実際に使った同じroot**を再検査し、本文だけでなくentry種別、観測したmode、root identityも初回snapshotと比較します。別rootへ正常な原本を展開し直して改変を隠すことはできません。modeはこの実行の観測値であり、元capsuleに無いH93 modeを既知値として作りません。

`repository_files_bound_to_head` は現在のown9の実Git HEAD／mode／bytesを記録し、歴史11本のH93 originは `historical_input_receipt.json` へ分けて記録します。旧 `repository_inputs` の歴史10本はこのcapsuleへ移り、現在のown3（applier／patch／source lock）の固定検査は残ります。現repositoryにH93のGit objectやcanonical treeが存在することを再現条件にしません。workflowは使用した歴史rootの11原物もartifactへ同梱します。

これは入力の所在と証拠の結合を変える保守です。UI213、元194の投影、12 UI CASE、30-program matrix、既存fixture／case、ゲーム4本文は維持します。C2 artifactにある全30生成program・source line／body byte範囲との一致を確認し、新HEADでfresh F46・全Native・compile／Rojoと登録非作者reviewを改めて通す必要があります。`original_contracts_modified=false` は原11入力が不変である意味で、変更された現canonicalを過去の原本として認める意味ではありません。

新current-R入口、現在RCへの履歴merge、共有producer変更、永久Lv5／20のHost接続やSOURCE／PREP／RCの新受入はC3の対象外です。

## 残る確認と非対象

**ACTIVE_RUNTIME=rich51 / PRIVATE_COMPANION=REAL69_UNION22 / RUNTIME_UNIFIED=NO** を維持します。現パッケージは候補作成と検証用で、canonical producerや共有profileを変更せず、正式RCを更新しません。PREP_READY、正式SOURCE承認、RC採用はそれぞれ別途、実HEADに対して確認が必要です。

Nativeは実ソース全bodyを固定して実行しますが、エンジン境界はfixtureです。選択した信号だけをDeferred化しており、実Robloxの全scheduler・物理・ネットワークを証明しません。UIは寸法演算で、実フォント幅、折返し、safe area、遮蔽、アニメーション、タッチは未確認です。MapIntelとmounted Realmは明示した表示入力です。core server28には従来のBotActors stubが残り、実AI/takeoverは別30-body補助試験として実行します。補助試験のPathfindingは利用不可の境界入力で、元bot loopをschedulerで1 tickずつ進めるため、実ナビゲーション・物理の保証は含みません。

追加の平面CFrame逆変換は実無回転arenaのengine API補完だけです。製品の入場・B・XP判定はfixtureへ移していません。Heroの到着監視は正式Hostによる明示CFrame代入に対応し、一般の物理移動通知を保証しません。

既存の320×260拡大mapとstatusの重なり、永久Lv/XPの未接続、上位Bや巨大化の未実装は残ります。既存 #815 の移動・#825 のMUSOUとのsource合成は別途検証しても、相手の実装所有権やRC採用許可を取得したことにはなりません。正式統合には既存ownerとのexact-source intakeと再審査が必要です。

**Studio=NOT_TESTED / Android=NOT_TESTED / ART_NO_GO / FUN=NOT_TESTED。** ここでのPASSはsource・Native・Rojoの範囲に限定されます。
