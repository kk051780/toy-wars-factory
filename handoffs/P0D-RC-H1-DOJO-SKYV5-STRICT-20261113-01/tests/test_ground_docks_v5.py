#!/usr/bin/env python3
"""Exact isolated original-source / V5 low-dock geometry QA. NOT an engine proof."""
import hashlib,math,os,pathlib,re,unittest

root=pathlib.Path(os.environ["P0D_DOCK_CANDIDATE"])
old=pathlib.Path(os.environ["P0D_DOCK_ORIGINAL"])
newworld=(root/"src/server/H1FunWorld.server.luau").read_text()
prevworld=(old/"src/server/H1FunWorld.server.luau").read_text()
maptext=(root/"src/server/MapBuilder.luau").read_text()
regex=re.compile(r'path\("(SKY_[A-Z_]+)",Vector3\.new\(([^)]*)\),Vector3\.new\(([^)]*)\),([0-9]+),')
def paths(src):
    return {name:(tuple(map(float,a.split(","))),tuple(map(float,b.split(","))),float(w)) for name,a,b,w in regex.findall(src)}
n=paths(newworld);p=paths(prevworld)
expected={"SKY_GROUND_BOOT_RED","SKY_GROUND_BOOT_BLUE","SKY_SCORE_DOCK_RED","SKY_SCORE_DOCK_BLUE"}
def top_y(a,b,point):
    return point[1]+math.hypot(b[0]-a[0],b[2]-a[2])/math.dist(a,b)
class ActualSource(unittest.TestCase):
    def test_source_sha(self):
        s=(root/"src/server/H1FunWorld.server.luau").read_bytes()
        b=hashlib.sha1(b"blob "+str(len(s)).encode()+b"\0"+s).hexdigest()
        self.assertEqual(b,"7a90affd4eb7eebcdfba39d833a2875ff665d5cf")
    def test_four_added_only(self):
        self.assertEqual(set(n)-set(p),expected)
        self.assertEqual(len(p),7)
    def test_seven_prior_paths_unchanged(self):
        for k in p:self.assertEqual(n[k],p[k],k)
    def test_one_world(self):
        self.assertEqual(newworld.count('local world=Instance.new("Folder")'),1)
        self.assertIn('assert(not arena:FindFirstChild("H1_FUN_WORLD")',newworld)
    def test_studio_guard(self):
        self.assertIn('if not RunService:IsStudio() then',newworld)
    def test_no_duplicate_authority(self):
        for token in ('OnServerEvent:Connect(', 'Instance.new("RemoteEvent")','DataStoreService','MarketplaceService'):
            self.assertNotIn(token,newworld,token)
    def test_ground_surface_genuine(self):
        self.assertIn('"GrassArena", Vector3.new(250, 4, 142), Vector3.new(0, -3, 0)',maptext)
    def test_ground_ends_match(self):
        for key in expected:
            a,b,w=n[key]
            self.assertLess(abs(top_y(a,b,a)+1),.06,key)
    def test_docks_touch_exacts(self):
        pairs=[
          ("SKY_GROUND_BOOT_RED","SKY_RAMP_RED",0),
          ("SKY_GROUND_BOOT_BLUE","SKY_RAMP_BLUE",1),
          ("SKY_SCORE_DOCK_RED","SKY_FORT_ESCAPE_RED",1),
          ("SKY_SCORE_DOCK_BLUE","SKY_FORT_ESCAPE_BLUE",1)]
        for key,oldname,j in pairs:
            a,b,w=n[key];c,d,_=n[oldname]
            x=(c,d)[j]
            self.assertEqual(b,x,key)
            self.assertLess(abs(top_y(a,b,b)-top_y(c,d,x)),.16,key)
    def test_symmetric_red_blue(self):
        for stem in ("SKY_GROUND_BOOT","SKY_SCORE_DOCK"):
            a,b,w=n[stem+"_RED"];c,d,ww=n[stem+"_BLUE"]
            self.assertEqual(w,ww)
            self.assertEqual(a[0],-c[0])
            self.assertEqual(b[0],-d[0])
            self.assertEqual(a[1:],c[1:])
            self.assertEqual(b[1:],d[1:])
    def test_docks_are_low_gradient(self):
        for name in expected:
            a,b,w=n[name];h=math.hypot(b[0]-a[0],b[2]-a[2])
            self.assertLessEqual(abs(b[1]-a[1])/h,.13,name)
    def test_all_path_contract(self):
        for name,(a,b,w) in n.items():
            self.assertGreaterEqual(math.dist(a,b),12,name)
            self.assertLess(math.dist(a,b),220,name)
            self.assertLessEqual(abs(b[1]-a[1])/math.hypot(b[0]-a[0],b[2]-a[2]),.55,name)
    def test_no_wall_pillar_crossing(self):
        for name in expected:
            a,b,w=n[name]
            for i in range(101):
                t=i/100
                x=(1-t)*a[0]+t*b[0];z=(1-t)*a[2]+t*b[2]
                self.assertLess(abs(x)+w/2,125)
                self.assertLess(abs(z)+w/2,69)
                self.assertFalse(83-w/2<=abs(x)<=123+w/2 and (abs(z-44)<=w/2+2.5 or abs(z+44)<=w/2+2.5),name)
                self.assertFalse(abs(abs(x)-40)<3.5+w/2 and abs(z-32)<3.5+w/2,name)
    def test_scene_budget_marker(self):
        self.assertIn('assert(count<=85',newworld)
        self.assertIn('world:SetAttribute("GroundDocksPhysical",4)',newworld)
    def test_no_second_sky_island(self):
        self.assertEqual(newworld.count('local fort=box("FLOATING_SKY_ISLAND"'),1)
    def test_negative_high_step_rejected(self):
        a,b,w=n["SKY_GROUND_BOOT_RED"]
        self.assertGreater(abs(top_y(a,b,a)+1+2),.06)
    def test_negative_steep_step_rejected(self):
        a,b,w=n["SKY_SCORE_DOCK_BLUE"]
        self.assertGreater(abs(12-a[1])/math.hypot(b[0]-a[0],b[2]-a[2]),.55)
    def test_negative_broken_symmetry_rejected(self):
        a,b,w=n["SKY_GROUND_BOOT_RED"];c,d,_=n["SKY_GROUND_BOOT_BLUE"]
        self.assertNotEqual(a[0],-c[0]+1)
    def test_original_egg_authority_preserved(self):
        game=(root/"src/server/Game.server.luau").read_text()
        self.assertEqual(game.count('remote.OnServerEvent:Connect('),1)
        self.assertIn("match.scores[team] += 1",game)
        self.assertIn('scorePrompt.Triggered:Connect',game)
    def test_no_game_overwrite(self):
        for x in ("Game.server.luau","MusouHorde.luau"):
            self.assertEqual((root/"src/server"/x).read_bytes(),(old/"src/server"/x).read_bytes())
    def test_no_paid_speed_effects(self):
        for s in ("PromptProductPurchase","Humanoid.WalkSpeed","TeleportService"):
            self.assertNotIn(s,newworld)
if __name__=="__main__":unittest.main(verbosity=2)
