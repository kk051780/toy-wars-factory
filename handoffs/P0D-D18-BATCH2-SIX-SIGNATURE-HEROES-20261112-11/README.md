# P0-D D18｜第2波・6職別オリジナル3D看板キャラ（PUBLIC_SOURCE_V1）

**Source-only / Game integration NONE / Native Luau / Studio / mobile NOT TESTED.**

P0-D 企画室、別担当の機能と重複しない固有の 6 ID をイミュータブルな元帳から制作。前回共通生成エンジンのAPIと入力検証方式を再利用し、新しい造形を個別に著作した。**既存の18体は書き換えない**。

- Source canon: `TRAP_RAIDERS_COLLECTION_ATLAS_648_v8.xlsx`, SHA256 `cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01` (原本Excelそのものは改変・同梱しない)。
- Source predecessor immutable Git commit: `9cfa08c6abb4babdef7a3fbb8f680de55855e45c`.
- Soft claim: https://github.com/kk051780/toy-wars-factory/issues/219#issuecomment-6813408820

| ID | 名称 | 独自造形・遠景で残す特徴 |
|---|---|---|
| TRCA-BE-009 | ほうき星ドラ | ひび星石、長い三筋の彗星尾、片側だけ高い角 |
| TRCA-SP-018 | 森のこだま | 上が開いた葉輪、吊り下げきのこ灯、左の二重こだま玉 |
| TRCA-VE-027 | 千年歯輪観測車 | 片側巨大8歯輪、上向き望遠鏡、前の開いた運転席 |
| TRCA-WE-036 | 冬銀ホルン | 銀色の曲がる吹奏管、六角氷章、ぶら下がる氷鈴 |
| TRCA-ZO-045 | 天鼓の旗振り兵 | 二色に割れた旗、傾く羽帽子、左右の長さが違う靴 |
| TRCA-TR-054 | さざなみ跳ね台 | 二重波紋、後ろに上がるしぶき、天面の大矢印 |

### ファイルと標準

- `data/six_pilot_geometry.json` 6体の**手作業で個別設計**した near/far/pose/色/配置。
- `data/archetype_rules.json` 6体別の造形型・遠景必須の3特徴名。
- `data/flagship72_registry.json` 全72正本データ（直前の固定成果から**byte-exactコピー**）。
- `data/batch_claims.json` 過去18+新規6のソフトクレーム。
- `data/next54_source_queue.json` 過去のファイル名を継承した互換キュー。**実内容は未制作48体**、6分類×8。現時点で自動請負はしない。
- `tools/generate_catalog.py` 入力の厳格検査と確定Luau出力。`src/D18BatchFactory.luau` は前回と byte-exact 同一。
- `src/DisabledPilotDemo.client.luau` は `ENABLED=false` で自動実行しない。

### 自分で検証

```bash
python tools/generate_catalog.py --check
python -m unittest discover -s tests -v
python tools/verify_pack.py
```

`Factory.Build(parent,id,CFrame)` の parent は **WorldModel 専用**、展示ローカルのみに限定。4姿勢、near/far、45度回転、Destroyを持つが、実際のゲームへは未接続。

**非機能・非実装：** 自動収集、レア抽選、実ダメージ、罠発動、ジャンプ、武器攻撃、Datastore永続保存、課金、Reel/YouTube実査、S1統合、Windows Codex/Studio検証、子どもの反応計測、ゲーム公開。
