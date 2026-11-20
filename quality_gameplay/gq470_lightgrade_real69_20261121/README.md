# GQ470 FB-015 — REAL69 海中・雷雨の軽量カラートーン（A候補）

**状態:** SOURCE_WIP / not in official RC / Studio・Android・ART・FUNは未検証。

## プレイヤーに届く改善

既存の陸海空クライアント `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_RealmBattleControls` にだけ、海中 SUBSEA・戦闘機の THUNDER/WIND の状況に応じた控えめな色調を追加する。既存 `RealmWeather` と `currentKind` に従うだけで、天候の実制御、移動・攻撃・HP・城・卵・スコアに触れない。初回ロビーと通常徒歩中は効果なし、視界を塞ぐHUDもなし。

- 実体: `patch_realm_color69.py` が現在の正式REAL69ソースを一度だけ差し替える **既存1ソース・69本中68本完全一致** の候補を生成。
- 描画負荷上限: 状態が必要な時だけ `ColorCorrectionEffect` を最大1つ生成。新規Part/Remote/RenderStepped接続 0。既存0.13秒間隔の処理へ統合。Studio以外での一般公開や課金は別ゲート。
- 時間・モード境界: SUBSEA/THUNDER/WIND を抜けたら即無効化。LocalScript破棄時に自身のEffectを破棄。他班名のEffect、Atmosphere、Lighting.ClockTime、カメラ/他UIを変更しない。
- 旧アート方向性の再利用: PR #377 の淡い気象色の意図をREAL69の現行ステートに合わせて一箇所へ縮退。樹木・城・海のPart追加はしない。
- 試遊設計: 同じ視点・天候で旧新PC/Android画像を比較。海中の対象識別、雷雨の敵/卵/城の視認性・低性能端末のFPS低下を #420 で人間採点する。不合格ならOFF。

## 再現可能な正本ソース検証

固定する正式RC: `e80973c354f14a0d0088577f3cc1a875454f0f8f`。同HEADの公式Actions `44695199140`、artifact `14610422120`。対象オリジナル SHA256 `8a7473f348bfe834fc8c6f5018822608903845c89796ce4976eea04fe9a95e6f`。

```sh
python3 -B quality_gameplay/gq470_lightgrade_real69_20261121/patch_realm_color69.py --artifact official-real69.zip --out candidate69
REAL69_ARTIFACT=official-real69.zip python3 -B -m unittest discover -s quality_gameplay/gq470_lightgrade_real69_20261121 -p 'test_*.py' -v
```

強制条件: 元artifactのREAL69全69ルート/全SHA/official HEAD検証、対象1ソースだけの実パッチ、逆変換で元Source完全復元、負例6件、持続ループ/3D追加・表示権威の拡大なし。generated candidateは **公式RCでも実Placeでもない**。CI成功でもLuau Native/Rojo ON/OFF/実機PASSの代替にならない。

## RCへの統合

#218 scoped claim request [lighting](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7050610576) / [existing REAL69 realm client](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7050692761)。
#910 P0-A/B遊べる一戦より先に本候補で統合枠を奪わない。#250が ADOPT した時のみ、#220認証Bが最新正式HEADを再取得し、対象 **既存1クライアントのソースのみ** を採用、fresh expected SHA / force=false CAS。新正式HEAD同一のLuau Native、Rojo ON/OFF、Place/ZIP、旧17/48保全・SourceLock、OFF復元、#420画像比較を行う。PR丸ごとmerge禁止。最新HEAD変化時は元ハッシュ・衝突を再検査する。

**未達ゲート:** real Studio Solo/2client=NOT_TESTED; 32枚画像=0/32; Android15分=NOT_TESTED; Human Art=NOT_TESTED; KID FUN=NOT_TESTED; OWNER_ACCEPTED=0; PRODUCT/ART/MOBILE/FUN_NO_GO。
