# EGG RAID RUMBLE — レベル上げを「もう1回遊びたい」体験にするUX試作

- Date: 2026-11-13 JST.
- owner feature: `P0D-LEVEL-JOURNEY-UX-20261113` / Issue [#284](https://github.com/kk051780/toy-wars-factory/issues/284).
- ブランド表示: **EGG RAID RUMBLE**、既存 internal game ID `TRAP_RAIDERS` / work ID `p0d-siege-v19` は不変更。
- SOURCE BASE: #281 **既存の本物の Luau XP エンジン** `cf2d99b3289c69a0f0e076fed6dccb2e4b261299`; own local `src/ProgressionRules.luau` は全バイト同一の参照コピー。Git blob `a72830b039a46ca02d02f6aab7d6a4805bec8860`。#281本人の原本は改造しない。
- Other owners: #279 = 2対戦モード, #280 = FREE孵化→所有→実機候補3D偵察魔獣, #282 = 永続DataStore, #220 = 唯一の公式RC統合担当。重複所有もGame/Remoteの二重発行もしない。

## 実装した新機能

`src/LevelJourneyView.luau` は #281の真正`ProgressionRules`を注入して使う純Luau SERVER-DTOビルダ。正規XP結果を**読み取り専用**に整形し、現在のLv1-50 / XP残量 / 次の報酬（Lv2,5,10,20,30,50） / その試合のFOCUS Lv1-3 / 現在装備した魔獣・魔法等の熟練Lv1-10 / その次の色・モーション・称号解放節目を表示する。多段飛びレベルアップの途中にまたがる節目もすべて`PREVIEW_ONLY`候補として表示。**本モジュール自身はXP・図鑑・Owned・装備・報酬・Robuxを一切付与しない。**

`demo/LevelJourneyHUD.client.luau` はスマホ横画面対応を意識した読み取り専用GUI。左上のレベル・XPゲージ・次の報酬・試合中フォーカス、隣の熟練度を表示し、試合後のみ短くレベルアップの喜びを表示する。`revision`単調増加を判定して二重演出と古い更新を無視。HUDのローカル演出は権威を持たず、ユーザーからXPを要求するRemoteを作らない。設定した色・位置・読みやすさは**実Androidや2clientで未評価**。

`demo/LevelJourneyPreview.server.luau` は**Studio ONLY**の簡単なUIシミュレータ。固有の隔離Remoteを**サーバー→クライアント表示専用**に作り、#281の`recordEvent`と`commit`を本当に呼ぶ。ただし行動イベントは物理的に卵を拾った実記録ではなく**演出サンプル**。デモが短く済むよう、`duration=60s`を仮想入力にしている。本当のMatch/Gameや持続XPとは絶対に混同しない。

### プレイヤー体験目標（未実証）
1. 1試合目：「卵を守った！＋XP」→「レベル2！」→歓迎バナー解放候補を表示
2. 2試合目：「あと少しで次のLv」→魔獣の偵察で熟練度が進む
3. 5試合・長期：巣の装飾、エモート、乗り物演出、城の旗、オーラ。**すべて能力値差ではなく、愛着・自己表現の報酬。**
4. 罠/魔法/ゾンビ/武器/乗物の六カテゴリの熟練度へデータ駆動で広げるのは、各カテゴリの「本物の実戦使用」の証拠が出てから。図鑑/Source previewは使える収集品と数えない。
5. 次の報酬は購入前提にせず表示。放置報酬、ログイン強要、確率を隠した課金、対人戦の恒久的HP/ダメージ/速度増強はしない。

### 実物テストと再現

```sh
# Python静的チェック（これはエンジン動作を証明しない）
python -m unittest discover -s tests -p 'test_project_static.py' -v

# GitHub Actionsで固定Luauコンパイラ・実行VMを利用。アーティファクトとログ参照のこと
python tests/run_native_level_journey.py --luau /path/to/luau --compiler /path/to/luau-compile

# Windows PC で Rojo 7.7.1 (予め正規導入) が利用可能な場合のみ
rojo build default.project.json -o EGG_RUMBLE_LEVEL_JOURNEY_PRIVATE.rbxlx
```

Studio Test 2client: 両者同一画面の読みやすさ、無操作視認性、エフェクトの重なり、MaxLv・多段レベル、次の目標、同じ更新の二重レベルアップ拒否、UIの見やすさ、低性能Android体感を実際に確認する。デモ本体は**別ワールド**、本体の卵/試合/リモートを差し替えたり自動統合したりしない。

### 実統合に必要な未完成作業

- #220 の唯一の本番Game担当が卵取得・納入・防衛・味方護衛・**本当にOwned/Equippedな使用**イベントのみを、シリアル化されたサーバー受理イベントとして#281に渡すこと。負けても真の貢献でXPが入る一方、AFK/キル稼ぎ/無限防衛判定は禁止。
- 同一UUID round（JobId＋matchEpoch）・同じGameサーバーの単一エンジン、サーバー正規結果`commit`後に本書のDTOを**既存のGameの1本のRemote**で配信。別のGame authorityを起動しない。
- #282と連携し、孵化報酬＋Owned/Equip＋XP＋item mastery＋claimedRoundIdsを**同一playerのDataStore `UpdateAsync`で実際にトランザクション保存**。メモリだけでは持続しない。`UpdateAsync` callbackはyieldしない、ネットワーク障害時に保存成功と報告しない。
- 実際の解放アイテムの権利と保存は別のサーバー処理を必要とする。`PREVIEW_ONLY`をそのままユーザーの`OWNED`に書き込んではいけない。
- 真のRoblox 2クライアント＋Android＋OWNERの90秒 FUN合格・リリース承認まで **NO_GO**。

## 成果の数え方

`SOURCE` 納品はゲーム体験完成ではない。純Luau+HUD/デモ/独立QAを固定コミットで納品できても、ライブGameのXP反映や本物のマイルストーン権利付与・永続保存・プレイ感は**未実装/未検証**と申告する。リリース全体の最後の唯一の公式値 #220 75/100 を勝手に増加させない。protected main/RC/他lane/PC/追加課金/自動化設定は禁止。
