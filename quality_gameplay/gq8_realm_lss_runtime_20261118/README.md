# GQ8｜Realm34 × LSS32 通常サーバーでの海空戦・到達性ゲート

**非重複担当：GQ8_REALM_LSS_RUNTIME_REACHABILITY_20261118**／独立Source QA。#764 Realm、#772 LSS、#780/#782/#785 組合せ検査、#775 HP、#778 属性VFXの作者ソースは編集しない。canonical RC/mainにも書き込まない。

## 検証した事実（コード静的検査、Studio実機ではない）

- PR #764 RealmCoreはStudioガードなく起動し、FIGHTER戦闘機とSUBSEA潜水を自分で生成する。
- ただし艦砲SHIP、海獣SEA_BEAST、飛行獣SKY_BEAST、飛行艇AIRSHIPの4種は、PR #772 LSS側の車両生成に依存する。RealmCoreは4種の操縦・武器判定を持つが、4種の工場自体を生成しない。
- PR #772 LSSは冒頭に RunService:IsStudio() の実行制限を置く。元のLSS32をそのまま配置した場合は通常サーバーで4種の生成経路が閉じる。ただし正式Core36の生成工程はStudioガードを出力時に除去するため、完成品は別途検証する。Studio上での実動作は未確認。
- このQAは、通常環境の船・魔獣の機能を「RC統合済」と誤表示することを防ぐ。

| 機能 | 非Studio静的経路 | Studio静的経路 |
|---|---|---|
| FIGHTER：機銃/爆撃 | あり（動作未検証） | あり |
| SUBSEA：潜水攻撃 | あり（動作未検証） | あり |
| SHIP：艦砲 | なし／LSS Studio限定 | 候補あり |
| SEA_BEAST：ブレス | なし／LSS Studio限定 | 候補あり |
| SKY_BEAST：ブレス | なし／LSS Studio限定 | 候補あり |
| AIRSHIP：機銃 | なし／LSS Studio限定 | 候補あり |

## CIと証拠の扱い

- 2原作者PRの固定40桁HEADから実LuauをGitHub raw経由で取得し、Git blob SHA-1でSOURCE_LOCKを検証。変更があればFail Closed。
- 製造元、LSS依存、4種の名前、Studioガード、Realm単独生成を確認。出力REPORT.jsonの状態は LIVE_VEHICLE_REACHABILITY_BLOCKED。検査のCI成功は到達性検査成功であり、実ゲーム海空戦や美観の合格を意味しない。
- Studio制限削除、LSS機体参照削除、戦闘機工場削除の3変異は検査により破壊的変更として検知。
- 今回はゲームのソースそのものを修正していない。元31-script公式RCのbyteを変えず、追加のGame/Combat/HP/Score/Remote/Store authorityを作らない。

## 8領域への波及

キャラ：建築士/魔獣使いの騎乗; フィールド：海・空の到達経路; バトル：艦砲/ブレス/機銃; 城：城攻略ルート; 中立兵：既存Swarm非変更; アイテム：既存Item非変更; ロビー：既存Host非変更; バランス：陸海空の公平な経路数、Android描画負荷と所有数予算。これらは**検査・要受入**であり、ART/FUN/STUDIO合格ではない。

## 唯一B #220への統合条件・引継ぎ

船・飛行獣を通常ゲームに採用するときは、単にStudioガードを消すのではなく、実サーバー上で単一車両factory、操縦者と旧試合セッション遮断、既存25秒離席回収、180秒寿命、同時4体枠、海上・高度安全帰還、衝突/HP/ダメージ・OFF rollbackを検証する必要がある。正式RCの正しい固定HEAD取得→原作者Lua/新ルートのsource lock→同HEAD Native/Rojo/Source/Class/負例→認証済み唯一B writerの非force expected-SHA CAS→同HEAD公式Actions/ZIP/Place実測、という順序を守る。作者個別ACK待ちは不要。main/無断merge/Publish/課金/PC操作は禁止。

**現状：SOURCE QA制作中。正式RC追加採用0/1、Studio2client・Android15分・FUN・OWNER受入未実施。**

引継ぎキー: GQ8_REALM_LSS_RUNTIME_REACHABILITY_20261118。次のChatはこのREADME/PR/CI・#220最新HEADを再確認し、検査器の二重制作なしで正式B writerへの是正依頼を追う。

## 最新正式Core36（2026-11-18 UTC 03:41公式固定HEAD）との再照合

- 公式RC HEAD f77b4d4393d9e9b19b65566413432a7a9f13962b は、非公開V3 Core36 31+Realm3+Regen2を選択して同HEAD Actions 44232589275 が SUCCESS。これは正式RC内の非公開Studio試遊ソース採用であり、ゲーム公開や人間FUN合格ではない。
- 実際のCore36コンポーザは LSS を**正式RC branch側**から選んでいる。現HEADで選択されたLSS実Git blobは c4ca82218d985914ad98dead565f9f79f5374dcb。新しいPR #772 の改修blob f9ea61cc1ed4a4ec5edbc7078a619790b3181f61 ではない。
- 両LSS原本にはStudioガードがある。ただしCore36は元#764 compose_core34.pyにより生成LSSの該当ガードを1箇所除去しているため、原本だけでCore36の通常サーバーの4乗物を閉鎖と断定できない。#772が持つ**25秒離席回収は現Core36にはまだ入っていない**。検査器は固定RC blobと候補blobの差を必ずJSON報告する。これは入力原本の性質であって、正式Core36の出力実体そのものではない。
- したがって「Core36選択済」「#772実装採用済」「通常環境で船・飛行獣が動く」は別々の事実。後二者を現状の達成として扱わない。

## 追補：正式Core36の生成済Source検査（2026-11-18）

**前記の「通常サーバーで4乗物が必ず生成不能」という扱いを訂正。** PR #783で採用されたCore36のビルド手順は、PR #764固定コンポーザ compose_core34.py を実際に実行して、原本LSSのStudioガードを出力時に1箇所だけ除去する。PR #788の元のRAW-source監査はこの出力工程を観測していなかった。

既存PR #788内で作業範囲を統合し、次の独立検証を追加した。
- verify_composed_core.py: #764固定コンポーザを実行。ダミー31-source Rojo台から34-source生成 → 生成LSSガード除去 → SEA_BOAT / SEA_BEAST / AIRSHIP / SKY_BEASTの4つの実factory呼出が残ることを検証。OFF31はbyte一致、ガード+4 factory欠落の計5負例。
- GitHub Actions: #764固定HEADと正式Core36の固定HEAD f77b4d4393d9e9b19b65566413432a7a9f13962b から原作者原本を別々にcheckoutし、git blob不一致をRED扱い。
- REPORT.jsonはRAW sourceだけの結果、COMPOSED_REPORT.jsonがCore34 composer出力の静的到達性を表す。ソース上の到達経路が存在することは、Studio/非Studio実機での遊びや操作成功を意味しない。

**重要な残課題：** 実Core36は#772の25秒離席回収改修blobを採用していない。正式36-source .rbxlx はActions上で構築済みでも、実Robloxサーバーでの乗降、TEAM/BR、海空戦、低性能Android FPS、15分安定、子どもの面白さは未検収。新規Game/Combat/Remote権限を持たず、元作者/RC writerに対する重複実装は行わない。受入責任は #220 sole authenticated writerによる同HEAD CI＋Studio/Android/OWNERゲートを継続する。
