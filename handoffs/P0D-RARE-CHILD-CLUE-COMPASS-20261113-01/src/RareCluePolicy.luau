--!strict
-- Original, SERVER-DERIVED hint policy for the optional fantasy discovery book.
-- Never exposes hidden drop odds, real account data or gameplay rewards.
local Book = require(script.Parent.RareDiscoveryBook)
local Clue = {}
Clue.VERSION = "P0D_RARE_CHILD_CLUE_COMPASS_V1"
Clue.ORDER = {"SPACE","CELESTIAL","EMBER","ECLIPSE"}
Clue.WORLD = {
    SPACE = {
        short = "ほしの おしろ",
        hint = "むらさきの はしで、そらを みあげよう",
        landmark = "ほしくじら",
        path = "SPACE_STAR_BRIDGE",
    },
    CELESTIAL = {
        short = "そらの しんでん",
        hint = "きんいろの さかの うえを さがそう",
        landmark = "にじのペガサス",
        path = "SKY_GOLD_RAMP",
    },
    EMBER = {
        short = "あかい おしろ",
        hint = "あかい いわみちの そばを みよう",
        landmark = "マグマモグラ",
        path = "EMBER_STONE_BRIDGE",
    },
    ECLIPSE = {
        short = "ひかりと やみ",
        hint = "たいようと つきの まんなかを みよう",
        landmark = "ふたつのかおのげんじゅう",
        path = "ECLIPSE_SUN_PATH",
    },
}
Clue.STUDIO_HUB = "テスト: みどりの ひろばで そらをみよう"
Clue.ALL_DONE = "4/4！みつけたね。 べつの みちも あるいてみよう"
Clue.INVALID = "じぶんの ペースで さがしてね"

function Clue.next(book,mode:string)
    if mode~="WORLD" and mode~="TEST_HUB" then
        return {kind="INVALID",id=nil,title="じぶんの てがかり",text=Clue.INVALID}
    end
    if type(book)~="table" or type(book.found)~="table" or
       type(book.count)~="number" or book.count~=book.count or
       book.count<0 or book.count>#Clue.ORDER then
        return {kind="INVALID",id=nil,title="じぶんの てがかり",text=Clue.INVALID}
    end
    if book.count==#Clue.ORDER then
        return {kind="DONE",id=nil,title="ずかん かんせい！",text=Clue.ALL_DONE}
    end
    for _,id in ipairs(Clue.ORDER) do
        if not Book.has(book,id) then
            local data=Clue.WORLD[id]
            if mode=="TEST_HUB" then
                return {kind="HINT",id=id,title="つぎの ヒント",
                    text=Clue.STUDIO_HUB,scope="TEST_HUB"}
            end
            return {kind="HINT",id=id,title="つぎの ヒント",
                text=data.short.."： "..data.hint,scope="WORLD"}
        end
    end
    return {kind="INVALID",id=nil,title="じぶんの てがかり",text=Clue.INVALID}
end

function Clue.validate(): (boolean,string)
    if #Clue.ORDER~=4 then return false,"missing four world cues" end
    if #Clue.ALL_DONE<12 or #Clue.STUDIO_HUB<12 then
        return false,"child-readable complete and test hub cues required"
    end
    local seen={}
    for _,id in ipairs(Clue.ORDER) do
        local d=Clue.WORLD[id]
        if seen[id] or not d or d.landmark~=Book.NAMES[id] or
            #d.hint<15 or #d.short<5 or #d.path<8 then
            return false,"missing child-facing hint/route/name linkage"
        end
        seen[id]=true
    end
    local empty=Book.fresh()
    if Clue.next(empty,"WORLD").id~="SPACE" or
       Clue.next(empty,"TEST_HUB").text~=Clue.STUDIO_HUB then
        return false,"initial clue not consistent"
    end
    return true,"four contextual hints: honest Studio hub and optional world modes"
end
return Clue
