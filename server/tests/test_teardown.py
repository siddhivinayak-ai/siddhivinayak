"""
Unit tests for brain.teardown — no network: the vision call and costing engine are stubbed.

Run:  venv\\Scripts\\python -m pytest server/tests -q
"""

import io
import json
import re
import sys
import types
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brain import teardown as td  # noqa: E402

GOOD = {
    "object": {"name": "Ceramic coffee mug (350 ml)", "category": "drinkware",
               "description": "Glazed stoneware mug.", "confidence": 0.9},
    "estimated_retail_inr": 399,
    "components": [
        {"name": "Body", "material_id": "ceramic_stoneware", "mass_g": 300, "qty": 1,
         "process_ids": ["ceramic_firing"], "notes": "Slip cast"},
        {"name": "Glaze", "material_id": "glass_soda_lime", "mass_g": 15, "qty": 1,
         "process_ids": ["painting"], "notes": ""},
    ],
    "assumptions": ["Standard 350 ml size"],
    "fun_fact": "Mugs shrink about 12% in the kiln.",
}


# ── stub costing (shape of the real contract) ────────────────────────

def _stub_costing():
    procs = {"ceramic_firing": {"label": "Ceramic firing", "scene": "thermal"},
             "painting": {"label": "Painting", "scene": "studio"},
             "cnc_machining": {"label": "CNC machining", "scene": "machining"}}
    mats = {"ceramic_stoneware": {"label": "Stoneware"}, "glass_soda_lime": {"label": "Soda-lime glass"}}

    def estimate_cost(components, units_per_year=100_000, region="IN"):
        comps = [{"name": c["name"], "cost": c["mass_g"] * 0.1,
                  "material_label": mats.get(c["material_id"], {}).get("label", "Generic"),
                  "process_labels": [procs.get(p, {}).get("label", p) for p in c["process_ids"]]}
                 for c in components]
        total = round(sum(c["cost"] for c in comps) * 1.3, 1)
        return {"currency": "INR", "materials": 10.0, "processing": 15.0, "assembly": 2.0, "packaging": 3.0,
                "overhead": 4.0, "total": total,
                "breakdown": [{"label": "Stoneware", "kind": "material", "amount": 10.0},
                              {"label": "Painting", "kind": "process", "amount": 2.0},
                              {"label": "Ceramic firing", "kind": "process", "amount": 13.0}],
                "warnings": [], "components": comps}

    def build_markup(total, price_used):
        m = round(price_used / total, 1)
        return {"price_used": price_used, "multiple": m, "verdict": "x",
                "where_the_money_goes": [{"label": "Making it", "amount": total},
                                         {"label": "Shipping, retail, brand, profit, tax",
                                          "amount": round(price_used - total, 1)}]}

    return types.SimpleNamespace(MATERIALS=mats, PROCESSES=procs, estimate_cost=estimate_cost,
                                 build_markup=build_markup, catalog_for_prompt=lambda: "MATERIAL ids: ...")


@pytest.fixture(autouse=True)
def stubs(monkeypatch, tmp_path):
    monkeypatch.setattr(td, "_costing", _stub_costing)
    monkeypatch.setattr(td, "TEARDOWN_DIR", tmp_path)
    monkeypatch.setattr(td, "vision_chain", lambda: [("groq", "qwen/qwen3.8-27b")])


def _jpeg(size=(1600, 900), fmt="JPEG"):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buf, fmt)
    return buf.getvalue()


# ── JSON extraction ──────────────────────────────────────────────────

def test_extract_plain():
    assert td.extract_json(json.dumps(GOOD))["estimated_retail_inr"] == 399


def test_extract_fenced_with_prose_and_think():
    text = "<think>hmm {not json}</think>Sure! Here:\n```json\n" + json.dumps(GOOD) + "\n```\nHope it helps."
    assert td.extract_json(text)["object"]["name"].startswith("Ceramic")


def test_extract_trailing_commas():
    text = '{"a": [1, 2, ], "b": {"c": 3,},}'
    assert td.extract_json(text) == {"a": [1, 2], "b": {"c": 3}}


def test_extract_failure():
    with pytest.raises(ValueError):
        td.extract_json("I cannot see the image.")


# ── validation / clamping ────────────────────────────────────────────

def test_clamping():
    raw = json.loads(json.dumps(GOOD))
    raw["object"]["confidence"] = 85
    raw["estimated_retail_inr"] = "₹1,299"
    raw["components"] = [
        {"name": "Huge", "material_id": "Stainless 304!", "mass_g": 999999, "qty": 1000, "process_ids": "deep_drawing, welding_arc"},
        {"name": "Zero", "material_id": "pp", "mass_g": 0, "qty": 1, "process_ids": []},
        {"name": "Neg qty", "material_id": "pp", "mass_g": "12 g", "qty": -3, "process_ids": ["injection_moulding"]},
        "garbage",
    ]
    v = td.validate(raw)
    assert v["object"]["confidence"] == 0.85
    assert v["estimated_retail_inr"] == 1299
    assert len(v["components"]) == 2
    huge, small = v["components"]
    assert 0 < huge["mass_g"] < 50_000 and huge["qty"] == 100
    assert huge["material_id"] == "stainless_304"
    assert huge["process_ids"] == ["deep_drawing", "welding_arc"]
    assert small["mass_g"] == 12 and small["qty"] == 1


def test_unknown_ids_are_kept():
    raw = json.loads(json.dumps(GOOD))
    raw["components"][0]["material_id"] = "unobtainium"
    assert td.validate(raw)["components"][0]["material_id"] == "unobtainium"


def test_no_components_rejected():
    with pytest.raises(ValueError):
        td.validate({"object": {"name": "x"}, "components": []})


# ── vision + repair retry ────────────────────────────────────────────

def test_repair_retry(monkeypatch):
    calls = []

    def fake(content):
        calls.append(content)
        return "Here you go: {broken json" if len(calls) == 1 else json.dumps(GOOD)

    monkeypatch.setattr(td, "call_vision", fake)
    out = td.analyse_image(_jpeg(), hint="mug")
    assert len(calls) == 2
    assert isinstance(calls[0], list) and calls[0][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert 'User hint about the object: "mug"' in calls[0][0]["text"]
    assert isinstance(calls[1], str)  # repair is text only (no second image upload)
    assert out["components"][0]["material_id"] == "ceramic_stoneware"


def test_repair_fails_gives_502(monkeypatch):
    monkeypatch.setattr(td, "call_vision", lambda c: "no idea")
    with pytest.raises(td.TeardownError) as e:
        td.analyse_image(_jpeg())
    assert e.value.status == 502


def test_rate_limit_maps_to_429(monkeypatch):
    class RateLimitError(Exception):
        status_code = 429

    class Boom:
        def invoke(self, _):
            raise RateLimitError("Rate limit reached ... Please try again in 7.66s. Need more tokens?")

    monkeypatch.setattr(td, "_make_llm", lambda p, m: Boom())
    with pytest.raises(td.TeardownError) as e:
        td.call_vision("hi")
    assert e.value.status == 429 and e.value.retry_after_s == 7.7


def test_request_too_large_is_502(monkeypatch):
    class RateLimitError(Exception):
        status_code = 429

    class Boom:
        def invoke(self, _):
            raise RateLimitError("Request too large for model ... (OTPM): Limit 1000, Requested 1195.")

    monkeypatch.setattr(td, "_make_llm", lambda p, m: Boom())
    with pytest.raises(td.TeardownError) as e:
        td.call_vision("hi")
    assert e.value.status == 502


def test_falls_back_to_next_model(monkeypatch):
    class Overloaded(Exception):
        pass

    class Busy:
        def invoke(self, _):
            raise Overloaded("503 UNAVAILABLE. This model is currently experiencing high demand.")

    class Ok:
        def invoke(self, _):
            return types.SimpleNamespace(content='{"ok": true}', usage_metadata={})

    monkeypatch.setattr(td, "vision_chain", lambda: [("google_genai", "gemini-3.5-flash"), ("groq", "qwen/qwen3.8-27b")])
    monkeypatch.setattr(td, "_make_llm", lambda p, m: Busy() if p == "google_genai" else Ok())
    assert td.call_vision("hi") == '{"ok": true}'
    assert td.served_model() == "groq/qwen/qwen3.8-27b"


def test_all_models_busy_reports_shortest_retry(monkeypatch):
    class RateLimitError(Exception):
        status_code = 429

    waits = {"a": "try again in 20s", "b": "try again in 5s"}

    class Limited:
        def __init__(self, m):
            self.m = m

        def invoke(self, _):
            raise RateLimitError(f"Rate limit reached. Please {waits[self.m]}.")

    monkeypatch.setattr(td, "vision_chain", lambda: [("groq", "a"), ("groq", "b")])
    monkeypatch.setattr(td, "_make_llm", lambda p, m: Limited(m))
    with pytest.raises(td.TeardownError) as e:
        td.call_vision("hi")
    assert e.value.status == 429 and e.value.retry_after_s == 5.0


def test_times_rounding():
    assert td._times(2.5) == "three times" and td._times(1.4) == "1.4 times"


def test_retry_after_minutes():
    assert td._retry_after(Exception("Please try again in 1m2.5s")) == 62.5


# ── image prep ───────────────────────────────────────────────────────

def test_prepare_image_downscales():
    from PIL import Image

    out = td.prepare_image(_jpeg((3000, 1500), "PNG"))
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG" and max(img.size) == 1024


def test_prepare_image_rejects():
    for bad in (b"", b"not an image", b"x" * (td.MAX_IMAGE_BYTES + 1)):
        with pytest.raises(td.TeardownError) as e:
            td.prepare_image(bad)
        assert e.value.status == 400


# ── narration, scene, id, assembly ───────────────────────────────────

def test_inr_format():
    assert td.inr(1499) == "₹1,499"
    assert td.inr(146.7) == "₹147"
    assert td.inr(149999) == "₹1,49,999"
    assert td.inr(4.25) == "₹4.2" or td.inr(4.25) == "₹4.3"


@pytest.mark.parametrize("multiple", [0.6, 1.4, 3.0, 6.0, 10.2, 45.0])
@pytest.mark.parametrize("paid", [True, False])
def test_narration_length(multiple, paid):
    name = "Extremely long product name with many many words describing a vacuum insulated bottle " * 3
    text = td.make_narration(name, 146.7, 146.7 * multiple, paid, multiple, "Stainless steel 304")
    assert 0 < len(text) <= 280
    assert "₹147" in text


def test_narration_varies_with_verdict():
    a = td.make_narration("Mug", 30, 45, True, 1.5, None)
    b = td.make_narration("Mug", 30, 900, True, 30, None)
    assert a != b and "You paid ₹45" in a


def test_narration_plural():
    assert td.make_narration("Running Sneakers", 400, 4000, True, 10, None).startswith("These running sneakers cost about")
    assert td.make_narration("Glass", 40, 100, False, 2.5, None).startswith("This glass costs")


def test_scene_from_most_expensive_process():
    procs = _stub_costing().PROCESSES
    cost = {"breakdown": [{"label": "Painting", "kind": "process", "amount": 2.0},
                          {"label": "CNC machining", "kind": "process", "amount": 9.0},
                          {"label": "Stoneware", "kind": "material", "amount": 99.0}]}
    assert td.pick_scene([], cost, procs) == "machining"
    assert td.pick_scene([{"process_ids": ["ceramic_firing"], "cost": 5}], {"breakdown": []}, procs) == "thermal"
    assert td.pick_scene([{"process_ids": ["nope"], "cost": 5}], {}, procs) == "studio"


def test_id_format():
    i = td.new_id(datetime(2026, 10, 11, 15, 30, 12))
    assert re.fullmatch(r"td_20261011_153012_[0-9a-f]{4}", i)
    assert td.ID_RE.match(i)


def test_build_and_persist(monkeypatch):
    monkeypatch.setattr(td, "call_vision", lambda c: json.dumps(GOOD))
    out = td.run_teardown(_jpeg(), price_paid=None, hint="")
    assert td.ID_RE.match(out["id"])
    assert out["price"] == {"paid": None, "estimated_retail": 399, "currency": "INR"}
    assert out["markup"]["price_used"] == 399
    assert "components" not in out["cost"]
    c0 = out["components"][0]
    assert {"name", "material_id", "material_label", "mass_g", "qty", "process_ids", "process_labels",
            "cost", "notes"} <= set(c0)
    assert out["processes"][0] == {"id": "ceramic_firing", "label": "Ceramic firing", "scene": "thermal"}
    assert out["scene"] == "thermal"
    assert out["model"] == "groq/qwen/qwen3.8-27b"
    assert all(a in out["assumptions"] for a in td.STANDARD_ASSUMPTIONS)
    assert len(out["narration"]) <= 280
    # persisted + listed
    assert td.get(out["id"])["id"] == out["id"]
    assert td.image_path(out["id"]).exists()
    items = td.list_teardowns(5)
    assert items[0]["id"] == out["id"] and items[0]["cost"]["total"] == out["cost"]["total"]
    assert td.get("../etc/passwd") is None


def test_price_paid_and_currency(monkeypatch):
    monkeypatch.setattr(td, "call_vision", lambda c: json.dumps(GOOD))
    out = td.run_teardown(_jpeg(), price_paid=10, currency="usd")
    assert out["price"]["paid"] == 840 and out["markup"]["price_used"] == 840
    with pytest.raises(td.TeardownError):
        td.run_teardown(_jpeg(), price_paid=10, currency="XYZ")
