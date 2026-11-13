# P0D D18 Batch9 — 正規看板6体のオリジナル3DとStudio専用ギャラリー

看板72体の未制作12体から公式ID6体を選び、手作り低ポリ83 Parts／6体のオリジナル造形を追加。**制作済み3Dソース66/72（91.7%）、初回リリース新規追加は0体。**

## 今回の正規ID
- BE TRCA-BE-081 太陽の草竜
- SP TRCA-SP-090 砂時計の約束
- VE TRCA-VE-063 火輪の鍛造台
- WE TRCA-WE-108 音鳴りホルン
- ZO TRCA-ZO-027 大歯輪の見張り兵
- TR TRCA-TR-108 どんどん門玉

残り6体（Batch10候補）は BE108、SP063、VE081、WE063、ZO081、TR090。勝手に別IDを増やさない。

## 子どもに見せるStudio専用3Dギャラリー
`default.project.json` をRoblox Studioで未公開の新しいPlaceとして開き、Playすると**Studio限定**で6体のViewportFrameカードが並ぶ。`D18StudioGallery.client.luau` はRunService:IsStudio()以外で即終了。カードをタップすると`idle→tap→win→loss`の順に表情変化し、45°ずつモデルが回転する。閉じるとすべて破棄。最大12モデル、6体合計83アンカーPart、全てCollision/Touch/Query OFF、Remote/通信/報酬/保存/購入無し。

`DisabledPreview.client.luau` は従来通りENABLE=falseの非表示動作を保つ。StudioGalleryは別の検収用クライアントであり、本番S1にロードしない。

## 企画室が決めたゲームとしての意味
`design/CHARACTER_CARDS.md` に各キャラ固有3シルエット・収集したくなる導線・将来の職業×フィールド戦術・相手の対抗方法を記載。**能力は全部S2+の設計仮説であって実装ではない。** H1私的対戦の能力差・7職・課金やガチャは未変更。

source_atlas_sha256=cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01、以前の60体はGit SHA7bfb7bd5a4d4531ceaf2deaaf19f7591d3c218cdから検証。Claim #265。色/大小や読みやすさのStudio実機・スマホ・人間楽しさはNOT_TESTED。CIはあくまでソース構成とLuauコンパイルに限定。

main/保護RC/#220/過去Batch1-8/H1統合元/Roblox公開/課金/鍵/Windows Codex/P0ABC/CAS/既存automationsを変更しない。
