"""Execute the EXACT original Book, QAPlan, HUD Luau (outside Engine API doubles).
This never claims Roblox Studio or real 2-client physics execution.
"""
from pathlib import Path
import argparse
R=Path(__file__).resolve().parents[1]
S={
 "book":(R/"src/RareDiscoveryBook.luau").read_text("utf-8"),
 "plan":(R/"src/RareDiscoveryQAPlan.luau").read_text("utf-8"),
 "hud":(R/"src/RareDiscoveryHUD.luau").read_text("utf-8"),
}
MOCKS=r'''
local function vec(x,y,z) return {X=x,Y=y,Z=z} end
Vector3={new=vec}
Vector2={new=function(x,y)return {X=x,Y=y} end}
Color3={fromRGB=function(r,g,b)return {R=r,G=g,B=b} end}
UDim={new=function(a,b)return {Scale=a,Offset=b} end}
UDim2={fromOffset=function(x,y)return {X=x,Y=y} end,
       fromScale=function(x,y)return {X=x,Y=y} end,
       new=function(a,b,c,d)return {xs=a,xo=b,ys=c,yo=d} end}
Enum={TextXAlignment={Left="Left"},TextYAlignment={Center="Center"},
      Font={GothamBold="GothamBold",Gotham="Gotham"}}
local function InstanceObj(kind)
    local data={ClassName=kind,Name=kind,_children={}}
    local obj
    obj=setmetatable({},{
        __index=function(_,key)
            if key=="FindFirstChild" then
                return function(self,name)
                    for _,child in ipairs(data._children) do
                        if child.Name==name then return child end
                    end
                    return nil
                end
            elseif key=="FindFirstChildOfClass" then
                return function(self,cl)
                    for _,child in ipairs(data._children) do
                        if child.ClassName==cl then return child end
                    end
                    return nil
                end
            elseif key=="GetChildren" then
                return function(self)return data._children end
            elseif key=="Destroy" then
                return function(self)self.Parent=nil end
            else return data[key] end
        end,
        __newindex=function(_,key,value)
            if key=="Parent" then
                if data.Parent then
                    for i,v in ipairs(data.Parent._children) do
                        if v==obj then table.remove(data.Parent._children,i);break end
                    end
                end
                data.Parent=value
                if value then table.insert(value._children,obj) end
            else data[key]=value end
        end
    })
    return obj
end
Instance={new=InstanceObj}
'''
TESTS=r'''
local n=0
local function ok(cond,msg)
    n+=1
    assert(cond,"RARE_BOOK_NATIVE_ORIGINAL_FAIL #"..tostring(n).." "..msg)
end
local valid,reason=Book.validate()
ok(valid,"Book valid "..tostring(reason))
local planOK,planWhy=Plan.validate()
ok(planOK,"Plan valid "..tostring(planWhy))
ok(Book.VERSION=="P0D_RARE_SESSION_BOOK_V1","version")
ok(Plan.VERSION=="P0D_RARE_2CLIENT_STUDIO_QA_BENCH_V1","bench version")
ok(#Book.ORDER==4 and #Plan.ORDER==4,"4 types exact")
ok(Plan.SLOT_SECONDS==26,"26s each test slot")
ok(Plan.EXPOSURE_SECONDS==23,"23 seconds visible")
ok(Plan.PROMPT_DELAY_SECONDS==2,"two seconds visible before button")
ok(Book.progress(Book.fresh())=="発見ずかん 0/4","starts at 0/4")
local p1=Instance.new("Player")
local p2=Instance.new("Player")
local p1Gui=Instance.new("PlayerGui");p1Gui.Parent=p1
local p2Gui=Instance.new("PlayerGui");p2Gui.Parent=p2
local a=Book.fresh()
local b=Book.fresh()
ok(a~=b and a.found~=b.found,"books independent by session player")
ok(HUD.mount(p1,a)~=nil,"source HUD real original Roblox UI built player1")
ok(HUD.mount(p2,b)~=nil,"source HUD real original Roblox UI built player2")
local f1=p1Gui:FindFirstChild("RareDiscoverySessionBook")
local f2=p2Gui:FindFirstChild("RareDiscoverySessionBook")
ok(f1 and f2 and f1~=f2,"two independent ScreenGui instances")
ok(f1.ResetOnSpawn==false and f2.ResetOnSpawn==false,"UI survives avatar reset")
ok(f1:FindFirstChild("NotebookPanel")~=nil,"actual panel exists")
ok(f1:FindFirstChild("NotebookPanel"):FindFirstChild("Title").Text=="発見ずかん 0/4",
    "first player starts uncollected")
for i,id in ipairs(Book.ORDER) do
    local at=Plan.at((i-1)*Plan.SLOT_SECONDS)
    ok(at==id,"correct deterministic realm next")
    local p=Plan.point(id)
    ok(p~=nil and math.abs(p.X)==25 and math.abs(p.Z)==25,
        "all QA observations are within safe home plaza")
    local notYet,invalid=Book.accept(a,"WRONG",i)
    ok(invalid=="INVALID" and notYet==a,"cannot register unknown creature")
    local before=a
    a,result=Book.accept(a,id,i)
    ok(result=="NEW" and a~=before,"pure immutable progression")
    ok(a.count==i and a.lastSerial==i,"count and serial advance strictly")
    ok(Book.has(a,id)==true,"new item recorded in server-held book")
    ok(HUD.update(p1,a),"source UI refresh player1 success")
    local title=f1:FindFirstChild("NotebookPanel"):FindFirstChild("Title")
    ok(title.Text=="発見ずかん "..tostring(i).."/4",
        "actual GUI visible count correct")
    local rows=Book.list(a)
    ok(#rows==4 and rows[i].found and rows[i].id==id,
        "display row is exact creature")
    local same,repeatEvent=Book.accept(a,id,i)
    ok(same==a and repeatEvent=="REPEAT","repeat event same serial rejected")
    local sameLater,repeatLater=Book.accept(a,id,i+1)
    ok(sameLater==a and repeatLater=="ALREADY_SEEN","same creature can't double count")
end
ok(a.count==4,"full notebook only after four distinct finds")
ok(b.count==0 and not Book.has(b,"SPACE"),"p1 progress never leaks to p2")
ok(f2:FindFirstChild("NotebookPanel"):FindFirstChild("Title").Text=="発見ずかん 0/4",
    "second player UI still truly at zero")
for i,id in ipairs(Book.ORDER) do
    b,outcome=Book.accept(b,id,i)
    ok(outcome=="NEW" and b.count==i,"p2 independently discovers each")
    ok(HUD.update(p2,b),"p2's source UI independently refreshed")
end
ok(f1:FindFirstChild("NotebookPanel"):FindFirstChild("Title").Text=="発見ずかん 4/4",
    "first GUI 4/4")
ok(f2:FindFirstChild("NotebookPanel"):FindFirstChild("Title").Text=="発見ずかん 4/4",
    "second GUI 4/4")
ok(Book.fresh().count==0,"disconnect/rejoin has no persistence")
local old,stale=Book.accept(a,"SPACE",3)
ok(old==a and stale=="STALE","stale serial rejected")
local badSerial,badEvent=Book.accept(Book.fresh(),"SPACE",0/0)
ok(badSerial.count==0 and badEvent=="INVALID","NaN serial rejected")
local wrongSerial,wrongEvent=Book.accept(Book.fresh(),"SPACE",0)
ok(wrongEvent=="INVALID","zero serial rejected")
local wrongID,wEvent=Book.accept(Book.fresh(),"BAD_ID",1)
ok(wEvent=="INVALID","bad id rejected")
local empty=Book.fresh()
local one,out1=Book.accept(empty,"SPACE",1)
local other,out2=Book.accept(one,"ECLIPSE",1)
ok(other==one and out2=="STALE","second distinct creature cannot reuse a serial")
ok(Plan.at(4*Plan.SLOT_SECONDS)==nil,"test mode stops, no rolling forever")
ok(Plan.at(-1)==nil and Plan.at(0/0)==nil,"invalid benchmark time is safe")
ok(Plan.at(Plan.EXPOSURE_SECONDS)==nil,"interval gap empty")
ok(Plan.at(Plan.SLOT_SECONDS)=="CELESTIAL","second world after one slot")
ok(HUD.mount(p1,a)~=nil,"rebuilding GUI allowed for fresh SPAWN")
local count=0
for _,item in ipairs(p1Gui:GetChildren()) do
    if item.Name=="RareDiscoverySessionBook" then count+=1 end
end
ok(count==1,"mount never stacks HUD overlays")
print("RARE_BOOK_TRUE_ORIGINAL_NATIVE_PASS assertions="..tostring(n)..
    " two_independent_books=4/4 gui_screens=2")
'''
def orig(text,name,ending):
    if not text.startswith("--!strict\n") or not text.rstrip().endswith(ending):
        raise ValueError("Unknown exact original source: "+name)
    return text.replace("--!strict\n","",1)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    target=Path(args.output)
    target.mkdir(parents=True,exist_ok=True)
    srcbook=orig(S["book"],"book","return Book")
    srcplan=orig(S["plan"],"plan","return Plan")
    srchud=orig(S["hud"],"hud","return HUD")
    requires='local Book = require(script.Parent.RareDiscoveryBook)'
    if srchud.count(requires)!=1:raise ValueError("Unexpected require source")
    cases={
      "positive":(srcbook,srcplan,srchud),
      "BAD_DOUBLE_COUNT":(srcbook.replace("count=book.count+1","count=book.count+2",1),srcplan,srchud),
      "BAD_REUSE_SERIAL":(srcbook.replace("if serial==book.lastSerial then","if false then",1),srcplan,srchud),
      "BAD_MISSING_FOUND":(srcbook.replace("found[id]=true","found[id]=false",1),srcplan,srchud),
      "BAD_SESSION_START_4":(srcbook.replace("found={},count=0","found={},count=4",1),srcplan,srchud),
      "BAD_FOURTH_WORLD_SKIPPED":(srcbook,srcplan.replace("if slot>=4 then return nil,slot end","if slot>=3 then return nil,slot end",1),srchud),
      "BAD_NO_CUE":(srcbook,srcplan.replace("Plan.PROMPT_DELAY_SECONDS = 2","Plan.PROMPT_DELAY_SECONDS = 0",1),srchud),
      "BAD_UI_LIES_4":(srcbook,srcplan,srchud.replace("title.Text=Book.progress(book)",'title.Text="発見ずかん 4/4"',1)),
      "BAD_TWO_IDENTICAL_PANELS":(srcbook,srcplan,srchud.replace('if old then old:Destroy() end','if false then old:Destroy() end',1)),
    }
    if len({tuple(v) for v in cases.values()})!=len(cases):
        raise RuntimeError("one or more original Luau mutants did not change")
    for name,(bk,pl,hd) in cases.items():
        wrapped=(MOCKS+"\nlocal Book=(function()\n"+bk+"\nend)()\n"+
            "local Plan=(function()\n"+pl+"\nend)()\n"+
            "local HUD=(function()\n"+hd.replace(requires,"local Book = Book",1)+
            "\nend)()\n"+TESTS)
        path=target/(name+".luau")
        path.write_text(wrapped,encoding="utf-8")
        print("P0D_RARE_BOOK_NATIVE_CASE",name,path)
if __name__=="__main__":
    main()
