# GQ470 FB-015 | Ground-contact matte art | A PREP only

> **実装あり／正式RC未統合／ART・MOBILE・FUN・OWNERすべてNO_GO。**
> 本フォルダは `rc/p0d-s1-kids-rc01` を更新しません。#220認証済みBだけが選別統合できます。

## 独立レーン（他作者と非重複）
- 変更対象：本フォルダ＋専用CIのみ。正式REAL69既存69本のソース差分ゼロ。
- 新しい候補LocalScript：`StarterPlayer/StarterPlayerScripts/EGGRUMBLE_GroundMotionFX`。
- 原本：正式RC HEAD `e80973c354f14a0d0088577f3cc1a875454f0f8f`、公式Private REAL69 Place `798390B`、SHA256 `fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934`。
- 他レーン：#965 ART13、#963 城兵＋門HP、#960 ミニマップ、#962 武神、#959 遠景空、#943 技モーション等とソースパス非重複。
- CLAIM：[#218 comment 7054199078](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7054199078) はソフト申告であり承認済みCLAIMや採用決定ではない。

## 見た目の意図
1. 草・砂・地面に立って移動中、接地地点に薄いSmoothPlasticの楔形パルス（砂ぼこり）を短く発生。
2. Terrain水面近くで実際のSwim状態のとき、Raycast結果が**Water**の場合にだけ青灰色の薄い水面パルスを発生。水中・橋下などで水面検出不可なら描画しない。
3. タッチ端末1片／PC2片／同時最大6片。0.32秒間隔、0.38秒Tweenの短命アート。カメラ78stud超ではスキップ。Partは衝突／Touch／Query／影／Neon無し。常駐HUD、Remote、Combat、Egg、Store等への介入ゼロ。
4. Humanoid.Running/Swimmingはイベント使用で毎フレーム監視しない。死亡・キャラ消去でイベントを解除、保留タスクは世代番号で無効化。

## 人間のStudio受入（未実施・テスター用）
- PRIVATE候補PlaceをStudioで**先にオフライン／Privateで**起動。正式配信や公開Placeには使用しない。
- Grass/Sand/Groundを走って薄い足元パルスが見えること。停止、ジャンプ、落下、死亡時に不要なパルスが残らないこと。
- Terrain Waterへ入り、浅い水面で泳いだときだけ水面パルスが出ること。深い水中や地形/橋でRaycastが水面を確認できない場合には出ないこと。
- カメラを78studより離したときに描画を止め、近付ければ再開すること。
- PC通常とスマホ初回操作を比較し、指やHUD、城・卵・敵視認性を阻害しないこと。実端末で発熱／ラグ／描画込みコストを計測すること。
- 旧新8シーン×PC/Android×2=32画像を**実際に撮影**し、#420の人間評価PC目標4.5/5、Android4.0/5を計測すること。Android低性能15分の中央値30fps/p10 25fpsなどと子どもの初回3分FUN4/5も実測。
- 観測未実施時は `ART_NO_GO/MOBILE_NO_GO/FUN_NO_GO/OWNER_ACCEPTED=0` と記録。

## 検査・統合手順
- dedicated Actionsはソース安全契約/変異負例、69 OFF＋70 ON実Luauコンパイル、Pinned Rojo ON70、OFF69完全バイト一致、B220向けソース1本／SHA manifest、旧新32画像欠損の正直な `ART_CHECK_REPORT.json` を確認。
- source-only CI成功 ≠ Studio ENGINE PASS / 人間 ART GO。候補ZIP≠正式RC全体ZIP。
- #910の「職→出撃→卵獲得→納入→得点→城勝敗→任意再戦」のP0修復と#250の候補選別決定を優先する。
- #220だけが **fresh official expected SHA → source-select → nonforce CAS → 同HEAD公式CI → full ZIP/Place容量 → 実機再試遊** まで進める。A側からはRCへのforce push、PR全体merge、main編集、Roblox公開・課金をしない。
- 旧新検証で要件未達なら同じFB-015でREOPENし、原作者ACK待ちだけをブロッカーにしない。

所有者受入まで**完了率100%や発売可**とは言わない。
