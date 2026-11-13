# P0D D18 Batch10｜正規看板72/72 3Dソース全体を制作完了（未公開）

既存の66体に対し、公式Atlas72の最後の6体をオリジナル3Dソースとして追加。**72/72はモデルのソース制作率100%**を意味し、実ゲーム出現率や正式ゲームの完成率を意味しない。モデルの実機レンダリング・Android操作・子どもの楽しさは別ゲート。

## 今回の最終6体
- TRCA-BE-108 七鈴の王獣｜暁鐘の王城
- TRCA-SP-063 一番星の火輪｜火輪の熔炉
- TRCA-VE-081 祭りの大荷車｜黄金麦の丘
- TRCA-WE-063 炉鈴ホルン｜火輪の熔炉
- TRCA-ZO-081 収穫の旗振り兵｜黄金麦の丘
- TRCA-TR-090 時砂跳ね台｜砂時計の迷宮

正規Atlas SHA256: cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01。既存Batch1〜9は変更なし。今回のオリジナル81 Roblox Partsは各3つの遠景シルエット特徴、4ポーズ、近景/遠景の表示切替を持つ。

## 手元のStudioで確認する
このディレクトリの `default.project.json` をRojoでローカルの新しい非公開Placeへ変換し、Roblox StudioからPlay。Studio専用`D18StudioGallery.client.luau`が6体を独立したViewportFrameに並べて見せる。カードをタップすると idle→tap→win→loss を巡り、角度も変化。一般公開環境では RunService:IsStudio() 以外で起動しない。別のDisabledPreviewも無効のまま。

モデル生成FactoryはWorldModel以外の親を拒否し、12体上限、全PartがAnchored、CanCollide/CanQuery/CanTouch=false。ゲーム本体への召喚・攻撃・トラップ・レア出現・所持アイテム・報酬・広告・保存・課金は含まない。独立キャラクター資料だけを更新する。

## 実際の試合に取り込む設計（まだ未実装）
`design/CHARACTER_CARDS.md` に6体それぞれの集めたい動きと、将来の職業に対応した戦術/カウンター条件を記載。最初に比較するのは「七鈴の王獣」と「時砂跳ね台」の2体まで。S1に実際に登場する職業はRAIDER/GUARDIANだけ、7職の実装完了とは主張しない。

A/B運用はH1の2人Studio実プレー→モデルギャラリーで3秒判別・15秒触り心地テスト→独立性能監査→#220唯一の正式RC採用判断。人間の評価未実施なのでFUN_GATEはNO_GOを維持。

CLAIM #271。第9弾ベースSHA ae04e2e1bf4666acb012da49c5b289cb6ffc2c5c。他チャット・元Batch1-9・main/保護RC/公開・有料機能・Windows Codex/P0ABC/CAS/5 Automationsには変更なし。
