from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / "src" / "FeatureGatePolicy.luau").read_text(encoding="utf-8")

def test_pure_no_game_authority():
    for unsafe in ("FireServer", "FireClient", "SetAsync", "UpdateAsync", "GetService",
                   "MarketplaceService", "DataStoreService", "PublishAsync", "RemoteEvent"):
        assert unsafe not in src

def test_profile_distinction():
    assert "legacy21 =" in src and "rich47 =" in src and "rich51 =" in src
    assert src.count("V4_SIX_SKILL_SESSION = true") == 1

def test_no_false_hook_claim():
    assert "cannot switch any gameplay on its own" in src

def test_fail_closed_profile():
    assert 'return nil, "UNKNOWN_PROFILE"' in src

def test_fail_closed_feature():
    assert 'return nil, "UNKNOWN_FEATURE"' in src

def test_fail_closed_type():
    assert 'return nil, "NON_BOOLEAN"' in src

def test_no_feature_in_old_profile():
    assert 'return nil, "FEATURE_NOT_IN_PROFILE"' in src

def test_core_required():
    assert 'return nil, "CORE_REQUIRED"' in src

def test_dependency():
    assert 'return nil, "V4_REQUIRES_H1_DOJO"' in src

def test_immutable_result():
    assert src.count("table.freeze") >= 2

def test_no_user_or_network_io():
    for unsafe in ("HttpService", "UserId", "PlayerAdded", "task.wait", "task.spawn"):
        assert unsafe not in src
