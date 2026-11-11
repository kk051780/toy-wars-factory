# TRAP RAIDERS — D18 六分類共通3D生成基盤＋新規6体（鍵なし）

**分類**：企画室 #219 / isolated optional D18 original-source asset lane. **目的**：残り60看板キャラの3D制作を安全に高速化し、固有シルエットを犠牲にしない。**実際の増分**：新しいオリジナル3Dソース6体、合計12→18/72＝25.00%。**未制作**：54体（このパックには存在しない）。これら54体は自動生成・公開されたとは主張しない。

## 今回の原本照合済み6体

| ID | 分類 | 原本名 | 固有形状 | 近景/遠景Parts |
| --- | --- | --- | --- | --- |
| TRCA-BE-027 | 魔獣 | 大歯輪ガメ | 欠けた大歯車甲羅／真鍮片眼鏡／右歯車靴 | 24 / 18 |
| TRCA-SP-036 | 魔法 | 永久晶のまもり | 不揃い六角結晶／ひび／小さな出口 | 21 / 15 |
| TRCA-VE-045 | 乗り物 | 天鼓の空見台 | 左片翼／地面を向く望遠鏡／三角吊り台 | 13 / 11 |
| TRCA-WE-054 | 武器 | 貝鳴りホルン | Y字二連巻貝／ひび／真珠 | 18 / 11 |
| TRCA-ZO-009 | ゾンビ | 星鐘の案内兵 | 逆向き矢印の帽子／長さ違いの靴／胸鈴 | 13 / 11 |
| TRCA-TR-018 | 罠 | つぼみ跳ね台 | 折れた片葉／木製ボタン／枝ばね | 13 / 10 |

**実体**：`src/D18BatchCatalog.luau` は `data/six_pilot_geometry.json` と定義検証から機械生成。`src/D18BatchFactory.luau` は WorldModel 専用、Anchored / CanCollide=false / CanTouch=false / CanQuery=false / CastShadow=false の安全なプレゼンテーション生成器。`Build`, `SetPose`, `SetLod`, `SetYaw`, `GetStatus`, `Destroy`。デモOFF。**ゲーム内戦闘・所有権・罠発動・課金・報酬・データ保存には未接続**。

**次の並列作業を容易にする仕組み**：`data/flagship72_registry.json` は原本の72固定ID＋名称・世界・希少度・輪郭メモ。`data/next54_source_queue.json` は未3Dの54体を6分類×9体に割り振り、`SOFT_CLAIM=NONE` で管理。新着の台帳優先で衝突確認してから個別IDを確保する。新しいモデルには手作業の特徴的な3種のシルエットタグを必須とし、18パーツ以内の遠景で全タグが残ることを検証する。無数の色違いクローン量産は禁止。

## 納品・検証

`python tools/generate_catalog.py --check`

`python -m unittest discover -s tests -v`

`python tools/verify_pack.py`

READMEとカタログ・モデル・元本レジストリ・54体キュー・形状仕様・テスト・SHA-256マニフェストを plaintext として同梱。`BUILD_MANIFEST.json` は自己ハッシュを持たない。デモは他チャットのS1正式RCへ自動結合しない。

**S1全体の公式監査点**は#220のみが更新する。前回 #220 記録75/100点（実機Studio・スマホ2client・人間試遊・公開権限は別）。本パックの受入率100%はゲーム完成100%ではない。
