# BATTLE-HP-REGEN｜真正V3 31源→Host-owned 33源

## 課金なしの初期戦闘基盤
Issue #765 lane7。新しいパッシブ回復は無料基本機能。7職の初期HP案：戦士250、魔法使い195、暗殺者185、超能力者205、マッドサイエンティスト225、魔獣使い220、呪術師230（既存Role ID WARRIOR/MAGE/NINJA/TRAPPER/BUILDER/BEAST/ZOMBIEは絶対変更しない）。

本物の試合Hostに1回のrequireと既存の2か所の SevenRoleCombat.equip の直後フック、既存の終了処理を一切変更せず、Module側の死亡・離脱・world廃棄で接続を解除する方式を追加。既存30源byte same、31番目の元Host1本だけ差し替え＋新しいRegen Module2本の33 source。新Game/Combat/HP/Score/Store/Remoteを作らない。既存魔法使いの即時回復スキル／蘇生候補は触らない。既存Role HUDも上書きしない。

## 自然回復
最後にサーバーが観測したHumanoid.Healthの減少から7秒は回復しない。7秒経過後、毎秒MaxHPの0.7%が徐々に戻り、最大HPで停止。出血/燃焼(元属性 EGGRUMBLE_BurnUntil / DoTUntil)中は再生しない。ダメージ後の再生待機はPvP・AI・雷などのヒット元を区別しない。HP0・城陥落/脱落・旧アバター・旧試合・不正役職・別モードでは回復しない。

新試合/新アバターの装備時に1回だけ初期MaxHP・Healthをセット。同一アバター/試合の再装備時は全回復しない。再生Tick間隔0.25秒、接続を死亡・アバター交換・試合world廃棄・試合終了時に解除。クライアントがHPや回復を直接要求するRemoteなし。大きい回復や蘇生は別lane8のみ。

## REAL32検証
- compose_regen32.py --current31 REAL_SOURCE31.project.json --out REGEN33.project.json：**本物の31源から**Host最小パッチ＋Module1を出力。元Host以外30本をbyte完全同一。
- --off：元31本をbyte exactに復元、Source/Class照合。
- Python fixture QA、元Moduleソース由来のNative Luau実VM検査（7職、被弾、7秒、燃焼、終了、10倍回復 mutant RED）、最新成功済み正式RC31 Placeから抽出した同世代32 Native/Rojo、OFF31も照合。
- 元Hostのrequire/2 equip/清掃シグネチャが変わればRED停止。重複HP権限は作らない。

## 注意
これは公式31スクリプトV3 Companionの私的 Studio build候補であり、真のプレイヤー試遊や初回公開の承認ではない。既存HostにStudio-only gateがある場合は、その動作範囲を拡大しない。正式ゲームへ標準採用する前には#220唯一認証writerが単一正式RCを最新HEADにリベースし、真正Native/Rojo/OFFとStudio 2client / Android15分/初回3分 FUNの証拠を付ける。No main/publish/paid/force push。

## 非重複・先行作者再利用（追記）
- 10並列から重複した純Regen Policy候補 #771/#773/#774 を発見。**本PRは新しい政策作者ではなく、先行 #773 の純Policy SHA `c7fcc5e7b107529cb317e1e6f2d6bbbc6b49ee29`、Git Blob `23ccf84f88b2cb2901af33a563ff535e82d7a78f` を原文完全一致で再利用する正式Host接続PR**に変更。
- 33源 = 正式RC元31本からHost1本だけ改変 + 追加2本（既存#773純Policyと本PRの一意なruntime adapter）。元Combat/Role/Swarm/Item/SCORE/Storeは非変更。純Policyに役職HP・7秒・0.007・DoT・downedの決定を一本化して多重実装を避ける。
- CIは#773の純Policy blobを構成時に実検査し、一致しなければRED停止。元31本へのOFF復元はbyte exact。#771/#774は重複ポリシー実装として別途比較・整理対象で、無断変更しない。
