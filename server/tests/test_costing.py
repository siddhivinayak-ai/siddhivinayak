"""Sanity tests for the teardown costing engine.

Run:  venv/Scripts/python.exe -m pytest server/tests/test_costing.py -q
      (add -s to see the scenario table)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402

from brain.engineering.costing import (  # noqa: E402
    MATERIALS, PROCESS_GROUPS, PROCESSES, build_markup, catalog_for_prompt, estimate_cost, verdict,
)

SCENES = {"studio", "welding", "fasteners", "fluids", "thermal", "machining", "design"}


def C(name, material, mass, processes, qty=1):
    return {"name": name, "material_id": material, "mass_g": mass, "process_ids": processes, "qty": qty}


# name -> (components, low INR, high INR)
SCENARIOS = {
    "1 L SS vacuum bottle": ([
        C("Inner + outer wall", "stainless_304", 300, ["deep_drawing", "welding_arc", "electroplating"]),
        C("Cap", "pp", 40, ["injection_moulding"]),
        C("Seal", "silicone", 5, ["compression_moulding"]),
    ], 120, 300),
    "Cotton T-shirt": ([
        C("Body", "cotton_fabric", 170, ["sewing_cut_and_sew", "printing"]),
    ], 80, 220),
    "PP phone case 30 g": ([
        C("Case", "pp", 30, ["injection_moulding"]),
    ], 10, 40),
    "Ceramic mug 350 g": ([
        C("Mug", "ceramic_stoneware", 350, ["ceramic_firing"]),
    ], 40, 120),
    "Wired earphones": ([
        C("Cable", "wire_copper_insulated", 12, ["extrusion"]),
        C("Ear housings", "abs", 3, ["injection_moulding"], qty=2),
        C("Driver magnets", "magnet_neodymium", 1, ["generic"], qty=2),
        C("Inline remote PCB", "pcb_fr4_populated", 2, ["pcb_assembly_smt", "soldering"]),
        C("Jack", "brass", 2, ["turning", "electroplating"]),
        C("Ear tips", "silicone", 1, ["compression_moulding"], qty=2),
    ], 30, 200),
    "9 W LED bulb": ([
        C("Diffuser", "pc", 12, ["injection_moulding"]),
        C("Heat sink", "aluminium_die_cast", 15, ["die_casting"]),
        C("Driver board", "pcb_fr4_populated", 6, ["pcb_assembly_smt"]),
        C("LED chips", "led_chip", 0.05, [], qty=12),
        C("B22 cap", "aluminium_6061", 4, ["sheet_metal_stamping"]),
        C("Housing", "pc", 10, ["injection_moulding"]),
    ], 30, 150),
    "Ballpoint pen": ([
        C("Barrel", "pp", 4, ["injection_moulding"]),
        C("Cap", "pp", 1, ["injection_moulding"]),
        C("Refill", "ldpe", 1, ["extrusion"]),
    ], 3, 15),
    "Kitchen knife": ([
        C("Blade", "stainless_304", 90, ["sheet_metal_stamping", "heat_treatment", "grinding_polishing", "laser_engraving"]),
        C("Handle", "pp", 30, ["injection_moulding"]),
    ], 50, 200),
}


def _total(components, **kw):
    return estimate_cost(components, **kw)["total"]


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_scenario_ranges(name):
    comps, lo, hi = SCENARIOS[name]
    total = _total(comps)
    assert lo <= total <= hi, f"{name}: {total} outside {lo}-{hi}"


def test_cost_object_shape_and_sums():
    cost = estimate_cost(SCENARIOS["1 L SS vacuum bottle"][0])
    for k in ("currency", "materials", "processing", "assembly", "packaging", "overhead", "total",
              "breakdown", "warnings", "components"):
        assert k in cost
    assert cost["currency"] == "INR" and cost["warnings"] == []
    parts = cost["materials"] + cost["processing"] + cost["assembly"] + cost["packaging"] + cost["overhead"]
    assert abs(parts - cost["total"]) < 0.11
    bsum = sum(b["amount"] for b in cost["breakdown"])
    assert abs(bsum - (cost["materials"] + cost["processing"])) < 0.5
    assert {b["kind"] for b in cost["breakdown"]} <= {"material", "process"}
    assert cost["breakdown"][0]["label"] == "Stainless steel 304"   # sorted, biggest first
    assert len(cost["components"]) == 3
    assert cost["components"][0]["process_labels"] == ["Deep drawing", "Arc welding", "Electroplating"]
    for v in (cost["total"], *(b["amount"] for b in cost["breakdown"])):
        assert round(v, 1) == v


def test_tables_are_well_formed():
    assert len(MATERIALS) >= 40 and len(PROCESSES) >= 30
    for m in MATERIALS.values():
        assert set(m) == {"label", "inr_per_kg", "density_g_cm3", "family", "note"}
        assert m["inr_per_kg"] > 0 and m["density_g_cm3"] > 0
    for p in PROCESSES.values():
        assert set(p) == {"label", "scene", "inr_per_part", "inr_per_kg", "note"}
        assert p["scene"] in SCENES
    grouped = [p for ids in PROCESS_GROUPS.values() for p in ids]
    assert sorted(grouped) == sorted(PROCESSES)


def test_unknown_ids_fall_back_with_warnings():
    cost = estimate_cost([C("Thing", "unobtainium", 50, ["teleportation"]),
                          C("Frame", "weird steel alloy", 100, ["bending"])])
    assert cost["components"][0]["material_label"] == MATERIALS["generic"]["label"]
    assert cost["components"][0]["process_labels"] == [PROCESSES["generic"]["label"]]
    assert cost["components"][1]["material_label"] == MATERIALS["generic_metal"]["label"]
    w = " ".join(cost["warnings"])
    assert "unobtainium" in w and "teleportation" in w and "weird steel alloy" in w
    assert cost["total"] > 0


def test_aliases_and_spellings_resolve_silently():
    cost = estimate_cost([C("Case", "Polypropylene", 30, ["Injection Molding"]),
                          C("Board", "pcb_fr4", 5, ["SMT"])])
    assert cost["warnings"] == []
    assert cost["components"][0]["material_label"] == "Polypropylene (PP)"
    assert cost["components"][1]["material_label"] == "Populated PCB (FR4)"


def test_bad_mass_and_qty_are_clamped():
    cost = estimate_cost([C("A", "pp", -5, ["injection_moulding"]), C("B", "pp", 0, ["injection_moulding"]),
                          C("C", "pp", "heavy", ["injection_moulding"], qty=0)])
    assert len(cost["warnings"]) >= 4
    assert all(c["cost"] > 0 for c in cost["components"])
    assert estimate_cost([])["total"] == 0


def test_volume_and_region_effects():
    comps = SCENARIOS["PP phone case 30 g"][0]
    assert _total(comps, units_per_year=1_000) > 3 * _total(comps)  # tooling dominates at low volume
    assert _total(comps, units_per_year=1_000_000) < _total(comps)
    assert estimate_cost(comps, region="CN")["warnings"] == []
    assert estimate_cost(comps, region="MARS")["warnings"]


def test_qty_scales_cost():
    one = estimate_cost([C("Screw", "steel_mild", 2, ["turning"])])["components"][0]["cost"]
    ten = estimate_cost([C("Screw", "steel_mild", 2, ["turning"], qty=10)])["components"][0]["cost"]
    assert 8 * one < ten < 10.5 * one


def test_verdict_buckets():
    assert verdict(1.0) == "Fair deal"
    assert verdict(1.99) == "Fair deal"
    assert verdict(2.0) == "Normal retail"
    assert verdict(3.9) == "Normal retail"
    assert verdict(4.0) == "Brand premium"
    assert verdict(8.0) == "Premium brand"
    assert verdict(19.9) == "Premium brand"
    assert verdict(20) == "Mostly marketing"
    assert verdict(None) is None


def test_build_markup():
    m = build_markup(146.7, 1499)
    assert m == {"price_used": 1499, "multiple": 10.2, "verdict": "Premium brand",
                 "where_the_money_goes": [{"label": "Making it", "amount": 146.7},
                                          {"label": "Shipping, retail, brand, profit, tax", "amount": 1352.3}]}
    cheap = build_markup(100, 80)
    assert cheap["verdict"] == "Fair deal" and cheap["where_the_money_goes"][1]["amount"] == 0
    none = build_markup(100, None)
    assert none["multiple"] is None and none["verdict"] is None and none["price_used"] is None


def test_catalog_for_prompt_is_compact_and_complete():
    text = catalog_for_prompt()
    assert len(text) < 1500, len(text)
    for k in list(MATERIALS) + list(PROCESSES):
        assert k in text


def test_print_scenario_table():
    print("\n{:<24}{:>9}{:>9}{:>9}{:>8}{:>8}{:>9}   range".format(
        "scenario", "material", "process", "assembly", "pack", "ovh", "TOTAL"))
    for name, (comps, lo, hi) in SCENARIOS.items():
        c = estimate_cost(comps)
        print(f"{name:<24}{c['materials']:>9}{c['processing']:>9}{c['assembly']:>9}{c['packaging']:>8}"
              f"{c['overhead']:>8}{c['total']:>9}   {lo}-{hi}")
