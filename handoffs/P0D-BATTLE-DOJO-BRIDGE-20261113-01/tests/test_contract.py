from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"src"/"NextStepAdvisor.lua").read_text(encoding="utf-8")
def test_pure_table_interface():
    assert "function Advisor.build(" in s
    assert "return Advisor" in s
def test_no_mutating_authority():
    for tok in ("SetAsync", "UpdateAsync", "FireServer", "FireClient", "InvokeServer", "GetService", "DataStoreService", "MarketplaceService", "Robux"):
        assert tok not in s
def test_h1_default_only_real_pads():
    assert '{ "beast", "weapon" }' in s
    assert 'magic = true' in s
def test_safe_data_bounds():
    assert "v ~= v" in s and "math.clamp" in s
    assert "numberOrZero(match.eggsScored, 100)" in s
def test_priority_order():
    a=s.index('if progress.canEvolve == true')
    b=s.index('elseif progress.canHatch == true')
    c=s.index('VIEW_TRAINING')
    d=s.index('PLAY_AGAIN')
    assert a < b < c < d
def test_nonblocking_ui():
    assert "autoDismissSeconds = 7" in s and "dismissible = true" in s
def test_no_paid_random():
    assert "rand(" not in s and "math.random" not in s
def test_friend_only_display():
    assert "friendBonusVisible = opts.sameServerFriendBonus == true" in s
def test_readonly_marking():
    assert "readOnly = true" in s
