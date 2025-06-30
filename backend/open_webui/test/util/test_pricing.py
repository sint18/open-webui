# tests/test_pricing.py
import json, types, sys, pytest
from decimal import Decimal
from open_webui.utils.pricing import estimate_cost, _load_price_map, PRICE_URL
from utils.billing import calculate_cost


# ------------------------------------------------------------------
# 1️⃣  Helper to monkey-patch httpx.get so tests are offline-safe
# ------------------------------------------------------------------
class FakeResp:
    def __init__(self, text):
        self.text = text
    def raise_for_status(self):  # no-op in tests
        pass

@pytest.fixture(autouse=True)
def stub_httpx_get(monkeypatch):
    fake_json = {
        "gpt-4o": {"input_cost_per_token": 2.5e-6, "output_cost_per_token": 5e-6},
        "claude-3-haiku": {"input_cost_per_token": 8e-7, "output_cost_per_token": 4e-6},
    }
    def _fake_get(url, timeout=10):
        assert url == PRICE_URL
        return FakeResp(json.dumps(fake_json))
    monkeypatch.setitem(sys.modules, "httpx", types.ModuleType("httpx"))
    sys.modules["httpx"].get = _fake_get
    yield  # run test
    _load_price_map.cache_clear()  # reset cache between tests


# ------------------------------------------------------------------
# 2️⃣  Happy-path maths check
# ------------------------------------------------------------------
def test_cost_math():
    tot = estimate_cost("gemini-1.5-flash", 15, 17)
    assert tot == Decimal("6.225e-06")

def test_token_cost():
        tot = estimate_cost("gemini-1.5-flash", 3682, 168)
        cost = calculate_cost(float(tot))
        assert cost == 1

# ------------------------------------------------------------------
# 3️⃣  Unknown model should raise
# ------------------------------------------------------------------
def test_unknown_model():
    with pytest.raises(ValueError):
        estimate_cost("unknown-abc", 10, 10)

# ------------------------------------------------------------------
# 4️⃣  Cache behaviour: only one fetch
# ------------------------------------------------------------------
def test_single_fetch(monkeypatch):
    calls = {"n": 0}
    def _fake_get(url, timeout=10):
        calls["n"] += 1
        return FakeResp('{"gpt-4o":{"input_cost_per_token":1e-6,"output_cost_per_token":2e-6}}')
    import httpx
    monkeypatch.setattr(httpx, "get", _fake_get)
    _load_price_map.cache_clear()

    estimate_cost("gpt-4o", 1, 1)
    estimate_cost("gpt-4o", 10, 10)
    assert calls["n"] == 1, "JSON should be fetched exactly once"
