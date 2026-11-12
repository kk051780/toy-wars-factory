--!strict
-- Original server-owned, per-session ONLY discovery notebook.
-- No D18 collectible canon, DataStore, xp, currency, rarity payout or remotes.
local Book = {}
Book.VERSION = "P0D_RARE_SESSION_BOOK_V1"
Book.ORDER = {"SPACE", "CELESTIAL", "EMBER", "ECLIPSE"}
Book.NAMES = {
    SPACE="ほしくじら",
    CELESTIAL="にじのペガサス",
    EMBER="マグマモグラ",
    ECLIPSE="ふたつのかおのげんじゅう",
}
local function finite(n: number): boolean
    return type(n)=="number" and n==n and n>-math.huge and n<math.huge
end
function Book.fresh()
    return {found={},count=0,lastSerial=0,events=0}
end
function Book.has(book,id: string): boolean
    return book.found[id]==true
end
function Book.accept(book,id: string,serial: number)
    if not book or type(book)~="table" or type(book.found)~="table"
        or not finite(book.lastSerial) or not finite(book.count)
        or not Book.NAMES[id] or not finite(serial) or serial<1 or serial%1~=0 then
        return book,"INVALID"
    end
    if serial<book.lastSerial then return book,"STALE" end
    if serial==book.lastSerial then
        return book,Book.has(book,id) and "REPEAT" or "STALE"
    end
    if Book.has(book,id) then return book,"ALREADY_SEEN" end
    if book.count>=#Book.ORDER then return book,"FULL" end
    local found={}
    for key,value in pairs(book.found) do found[key]=value end
    found[id]=true
    return {found=found,count=book.count+1,
        lastSerial=math.max(book.lastSerial,serial),
        events=book.events+1},"NEW"
end
function Book.progress(book): string
    local n=book and book.count or 0
    return string.format("発見ずかん %d/4",n)
end
function Book.list(book)
    local list={}
    for _,id in ipairs(Book.ORDER) do
        table.insert(list,{
            id=id,
            found=Book.has(book,id),
            text=Book.has(book,id) and ("✓ "..Book.NAMES[id]) or "？ まだみつけていない"
        })
    end
    return list
end
function Book.validate(): (boolean,string)
    if #Book.ORDER~=4 then return false,"wrong count" end
    local seen={}
    for _,id in ipairs(Book.ORDER) do
        if seen[id] or not Book.NAMES[id] or #Book.NAMES[id]<4 then
            return false,"invalid four child-friendly names"
        end
        seen[id]=true
    end
    local empty=Book.fresh()
    if empty.count~=0 or Book.progress(empty)~="発見ずかん 0/4" then
        return false,"not fresh"
    end
    return true,"original per-session four-entry discovery book"
end
return Book
