# Teardown feature — shared contract

"Point at anything → your engineer twin reveals what it really costs to make."

Three parts are built in parallel against this contract. **Do not change a shape here without updating this file.**

```
photo ──▶ POST /api/teardown ──▶ teardown.py ── vision LLM (physical estimates only: parts, materials, mass, processes)
                                      │
                                      └──▶ engineering/costing.py  (deterministic ₹ maths from material/process tables)
                                      │
                                      └──▶ response JSON (below) ──▶ TeardownCard (React) + twin narration + scene
```

Rule: **the LLM never outputs money for manufacturing cost.** It estimates physical facts and a retail price guess; Python computes the cost.

---

## 1. Costing engine — `server/brain/engineering/costing.py`

```python
MATERIALS: dict[str, dict]
#  id -> {"label": str, "inr_per_kg": float, "density_g_cm3": float, "family": str, "note": str}
#  ids are snake_case, e.g. "pp", "abs", "pet", "hdpe", "silicone", "nylon_pa6", "steel_mild",
#  "stainless_304", "aluminium_6061", "copper", "brass", "glass_soda_lime", "cotton_fabric",
#  "polyester_fabric", "leather", "eva_foam", "rubber_natural", "pcb_fr4", "lithium_cell", "paper_board", "wood_hard", ...

PROCESSES: dict[str, dict]
#  id -> {"label": str, "scene": str, "inr_per_part": float, "inr_per_kg": float, "note": str}
#  scene is one of: studio | welding | fasteners | fluids | thermal | machining | design
#  ids e.g. "injection_moulding", "blow_moulding", "extrusion", "die_casting", "sand_casting", "forging",
#  "cnc_machining", "sheet_metal_stamping", "deep_drawing", "welding_arc", "spot_welding", "brazing",
#  "sewing_cut_and_sew", "pcb_assembly_smt", "glass_blowing", "printing", "anodising", "powder_coating",
#  "electroplating", "painting", "assembly_manual", "thermoforming", "3d_printing", ...

def estimate_cost(components: list[dict], *, units_per_year: int = 100_000, region: str = "IN") -> dict:
    """
    components: [{"name": str, "material_id": str, "mass_g": float, "process_ids": [str], "qty": int}]
    Unknown material/process ids fall back to a sensible "generic" entry and are reported in "warnings".
    Returns the `cost` object of the response schema (section 3), plus an extra key
    "components": [{"name", "cost", "material_label", "process_labels"}] in input order,
    which teardown.py moves onto components[i] and drops from the public `cost` object.
    """

def build_markup(total: float, price_used: float) -> dict:   # → the `markup` object
def verdict(multiple: float) -> str:                         # bucket text (section 3 field rules)

def catalog_for_prompt() -> str:
    """Compact text list of material ids and process ids (with labels) to paste into the vision prompt."""
```

---

## 2. HTTP API — `server/brain_server.py`

| Method | Path | Body / query | Returns |
|---|---|---|---|
| POST | `/api/teardown` | multipart: `image` (jpg/png/webp, ≤ 8 MB), optional `price_paid` (number), `currency` (default `INR`), `hint` (text, e.g. "Stanley cup 1.2 L") | Teardown JSON (section 3) |
| GET | `/api/teardown/<id>` | — | Teardown JSON |
| GET | `/api/teardown/<id>/image` | — | the uploaded image |
| GET | `/api/teardowns` | `?limit=20` | `{"items": [summary...]}`, newest first; summary = `{id, object.name, cost.total, price.paid or price.estimated_retail, markup.multiple, created_at}` |

Errors: `{"error": "human readable"}` with 400 (bad input) / 502 (vision model failed) / 429 (rate limited — include `"retry_after_s"`).

Vision model: env `VISION_PROVIDER` / `VISION_MODEL`, default `groq` / `qwen/qwen3.8-27b` (confirmed to accept images on our key). Also support `google_genai` and `anthropic`.

---

## 3. Teardown JSON

```json
{
  "id": "td_20261011_153012_ab12",
  "created_at": "2026-10-11T15:30:12",
  "object": {
    "name": "Insulated stainless steel water bottle (1 L)",
    "category": "drinkware",
    "description": "Double-wall vacuum-insulated bottle with a PP screw cap and silicone seal.",
    "confidence": 0.82
  },
  "price": { "paid": 1499, "estimated_retail": 1299, "currency": "INR" },
  "components": [
    { "name": "Inner + outer wall", "material_id": "stainless_304", "material_label": "Stainless steel 304",
      "mass_g": 290, "qty": 1, "process_ids": ["deep_drawing", "welding_arc", "electroplating"],
      "process_labels": ["Deep drawing", "Arc welding", "Electroplating"],
      "cost": 112.4, "notes": "Two drawn shells joined at the neck, vacuum between walls." }
  ],
  "processes": [
    { "id": "deep_drawing", "label": "Deep drawing", "scene": "machining" }
  ],
  "cost": {
    "currency": "INR",
    "materials": 70.1,
    "processing": 48.3,
    "assembly": 6.0,
    "packaging": 9.0,
    "overhead": 13.3,
    "total": 146.7,
    "breakdown": [
      { "label": "Stainless steel 304", "kind": "material", "amount": 61.5 },
      { "label": "Deep drawing", "kind": "process", "amount": 18.0 }
    ],
    "warnings": []
  },
  "markup": {
    "price_used": 1499,
    "multiple": 10.2,
    "verdict": "Premium brand",
    "where_the_money_goes": [
      { "label": "Making it", "amount": 146.7 },
      { "label": "Shipping, retail, brand, profit, tax", "amount": 1352.3 }
    ]
  },
  "assumptions": [
    "Made in India/China at ~100k units per year",
    "Material prices are 2025–26 bulk averages",
    "Excludes R&D, marketing, retailer margin and GST"
  ],
  "fun_fact": "The vacuum gap is only a few millimetres, yet it cuts heat transfer by over 90%.",
  "narration": "This bottle costs about ₹147 to make. You paid ₹1,499, so roughly ten times what it costs the factory. Most of the money is the brand and the shop, not the steel.",
  "scene": "machining",
  "model": "groq/qwen/qwen3.8-27b"
}
```

Field rules
- `price.paid` is `null` if the user gave none; then `markup.price_used = price.estimated_retail`.
- `markup.verdict` buckets by `multiple`: `< 2` "Fair deal", `2–4` "Normal retail", `4–8` "Brand premium", `8–20` "Premium brand", `≥ 20` "Mostly marketing".
- `narration` ≤ 280 characters, spoken by the twin, built from the numbers by a template (no second LLM call).
- `scene` = the scene of the most expensive process.
- All money rounded to 1 decimal place in JSON; the UI rounds for display.

A full example used by the UI for development lives at `src/components/teardown/fixture.json`.
