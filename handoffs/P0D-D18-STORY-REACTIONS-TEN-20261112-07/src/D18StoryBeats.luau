-- GENERATED from data/story_beats.json. Pure client-only narrative data.
-- No server awards, inventory, timers, networking or paid elements.
local BEATS = {
    ["TRCA-BE-018"] = {"森で小さな芽が雨にふるえていた。", "守ろうとした枝角が、光の道をふさいでしまう。", "そっと角をゆずると、芽にも友だちにも光が届いた。"},
    ["TRCA-ZO-054"] = {"灯りを持って、帰り道で友だちを待つ。", "大波の音で、道しるべが見えなくなった。", "貝ボタンを目印にして、みんなを水都へ案内できた。"},
    ["TRCA-BE-072"] = {"墓園の小さなおばけが、暗い道をこわがっていた。", "大きな月の冠までこわがられて、少ししょんぼり。", "片方の白い靴下を見せると、おばけが笑ってくれた。"},
    ["TRCA-SP-027"] = {"大きな歯車が止まり、みんな困っていた。", "力まかせの音では、小さな足踏みが聞こえない。", "三つの拍子がそろうと、歯車がやさしく動き出した。"},
    ["TRCA-VE-090"] = {"砂時計の船が、一人の旅人を乗せ忘れた。", "時計の針を戻そうとしても、時間は戻らない。", "船を引き返して、旅人と今の空を眺めた。"},
    ["TRCA-TR-009"] = {"星の台から、友だちを高く飛ばした。", "遠くへ行きすぎて、帰り道が分からなくなる。", "小さな帰還星を並べて、みんなで家まで帰れた。"},
    ["TRCA-WE-045"] = {"空庭のみんなを、大きな合図で励ましたかった。", "雷みたいな音に、小鳥がびっくりしてしまった。", "小さな一音を吹くと、小鳥が先頭で羽ばたいた。"},
    ["TRCA-SP-081"] = {"芽が出ない畑で、黄金の手は一粒を見つけた。", "冬が来ても、種のことを忘れなかった。", "春の朝、一番小さな芽を見つけて笑いあった。"},
    ["TRCA-VE-036"] = {"氷の鏡に、みんなの好きな景色を映そうとした。", "鏡が割れてしまい、だれにも見せたくなくなった。", "朝日が割れ目を照らし、新しい春の色が広がった。"},
    ["TRCA-ZO-108"] = {"七つの鈴を鳴らし、行進を始めようとした。", "ひとりの返事がなくて、隊長は立ち止まった。", "最後の友だちが帰るまで待つと、鈴がそろって鳴った。"},
}
local POSES = {"idle", "loss", "win"}
local Story = {}
function Story.get(id, chapter)
    if type(id) ~= "string" or type(chapter) ~= "number" or chapter % 1 ~= 0 or chapter < 1 or chapter > 3 then return nil end
    local lines = BEATS[id]
    if not lines then return nil end
    return { id = id, chapter = chapter, total = 3, text = lines[chapter], pose = POSES[chapter] }
end
function Story.next(chapter)
    if type(chapter) ~= "number" or chapter % 1 ~= 0 or chapter < 1 or chapter > 3 then return nil end
    return chapter % 3 + 1
end
function Story.count()
    local count = 0
    for _ in pairs(BEATS) do count += 1 end
    return count
end
return Story
