"""
Costing module: deterministic should-cost estimate for an everyday manufactured object.

The vision model only supplies physical facts (parts, materials, masses, processes);
every rupee is computed here from the tables below:

    per component  = qty · (m · price_kg · scrap + Σ_process (inr_per_part + m · inr_per_kg))
                     + Σ_process tooling · √(m / 100 g) / (units_per_year · TOOL_LIFE_YEARS)
    assembly       = manual labour, grows with the number of parts to join
    packaging      = max(floor, fraction · subtotal)
    overhead       = factory overhead + factory profit, a fixed fraction of the subtotal

Method follows standard should-cost / activity-based costing practice
(Ulrich & Eppinger, "Product Design and Development", ch. on design for manufacturing;
Swift & Booker, "Manufacturing Process Selection Handbook"; Boothroyd, Dewhurst & Knight,
"Product Design for Manufacture and Assembly").

All prices are indicative 2025–26 bulk purchase / mass-production rates for India and
China, in INR, rounded to order-of-magnitude values. They are meant to be believable to an
engineer (right within roughly ±30 %), not quotations.
"""

import math
import re

PRICE_NOTE = "indicative bulk price, 2025–26"

# id -> label, inr_per_kg, density_g_cm3, family, note
MATERIALS = {
    # ---- plastics ---------------------------------------------------------------
    "pp": {"label": "Polypropylene (PP)", "inr_per_kg": 115, "density_g_cm3": 0.90, "family": "plastic",
           "note": f"Commodity resin, caps and containers; {PRICE_NOTE}"},
    "abs": {"label": "ABS", "inr_per_kg": 170, "density_g_cm3": 1.05, "family": "plastic",
            "note": f"Housings and toys; {PRICE_NOTE}"},
    "pet": {"label": "PET", "inr_per_kg": 120, "density_g_cm3": 1.38, "family": "plastic",
            "note": f"Bottle-grade resin; {PRICE_NOTE}"},
    "hdpe": {"label": "HDPE", "inr_per_kg": 115, "density_g_cm3": 0.95, "family": "plastic",
             "note": f"Jerry cans, milk bottles; {PRICE_NOTE}"},
    "ldpe": {"label": "LDPE", "inr_per_kg": 120, "density_g_cm3": 0.92, "family": "plastic",
             "note": f"Films, squeeze bottles; {PRICE_NOTE}"},
    "pc": {"label": "Polycarbonate (PC)", "inr_per_kg": 260, "density_g_cm3": 1.20, "family": "plastic",
           "note": f"Clear, tough engineering plastic; {PRICE_NOTE}"},
    "pmma": {"label": "Acrylic (PMMA)", "inr_per_kg": 230, "density_g_cm3": 1.18, "family": "plastic",
             "note": f"Clear lenses and displays; {PRICE_NOTE}"},
    "nylon_pa6": {"label": "Nylon PA6", "inr_per_kg": 250, "density_g_cm3": 1.14, "family": "plastic",
                  "note": f"Gears, clips, glass-filled structural parts; {PRICE_NOTE}"},
    "pvc": {"label": "PVC", "inr_per_kg": 95, "density_g_cm3": 1.38, "family": "plastic",
            "note": f"Pipes, cable sheath, cheap soles; {PRICE_NOTE}"},
    "tpu": {"label": "TPU", "inr_per_kg": 330, "density_g_cm3": 1.20, "family": "plastic",
            "note": f"Flexible phone cases, straps; {PRICE_NOTE}"},
    "silicone": {"label": "Silicone rubber", "inr_per_kg": 450, "density_g_cm3": 1.15, "family": "plastic",
                 "note": f"Seals, gaskets, soft-touch parts (HTV/LSR); {PRICE_NOTE}"},
    "eva_foam": {"label": "EVA foam", "inr_per_kg": 220, "density_g_cm3": 0.20, "family": "plastic",
                 "note": f"Midsoles, slippers, padding; {PRICE_NOTE}"},
    "rubber_natural": {"label": "Natural rubber", "inr_per_kg": 190, "density_g_cm3": 0.93, "family": "plastic",
                       "note": f"Compounded for outsoles, grips, bands; {PRICE_NOTE}"},
    "pu_foam": {"label": "Polyurethane foam", "inr_per_kg": 260, "density_g_cm3": 0.04, "family": "plastic",
                "note": f"Cushions, ear pads, insulation; {PRICE_NOTE}"},
    # ---- metals -----------------------------------------------------------------
    "steel_mild": {"label": "Mild steel", "inr_per_kg": 65, "density_g_cm3": 7.85, "family": "metal",
                   "note": f"Cold-rolled sheet / bar; {PRICE_NOTE}"},
    "stainless_304": {"label": "Stainless steel 304", "inr_per_kg": 240, "density_g_cm3": 8.00, "family": "metal",
                      "note": f"18/8 austenitic sheet, food contact; {PRICE_NOTE}"},
    "aluminium_6061": {"label": "Aluminium 6061", "inr_per_kg": 290, "density_g_cm3": 2.70, "family": "metal",
                       "note": f"Wrought sheet / extrusion / bar; {PRICE_NOTE}"},
    "aluminium_die_cast": {"label": "Aluminium die-cast alloy (ADC12)", "inr_per_kg": 240, "density_g_cm3": 2.74,
                           "family": "metal", "note": f"Casting ingot, often recycled content; {PRICE_NOTE}"},
    "zinc_die_cast": {"label": "Zinc die-cast alloy (Zamak)", "inr_per_kg": 300, "density_g_cm3": 6.60,
                      "family": "metal", "note": f"Hardware, buckles, handles; {PRICE_NOTE}"},
    "copper": {"label": "Copper", "inr_per_kg": 860, "density_g_cm3": 8.96, "family": "metal",
               "note": f"LME-linked, volatile; {PRICE_NOTE}"},
    "brass": {"label": "Brass", "inr_per_kg": 600, "density_g_cm3": 8.50, "family": "metal",
              "note": f"Free-machining rod, fittings; {PRICE_NOTE}"},
    "titanium": {"label": "Titanium (grade 2/5)", "inr_per_kg": 2500, "density_g_cm3": 4.50, "family": "metal",
                 "note": f"Premium cookware, watches, eyewear; {PRICE_NOTE}"},
    # ---- glass & ceramic --------------------------------------------------------
    "glass_soda_lime": {"label": "Soda-lime glass", "inr_per_kg": 30, "density_g_cm3": 2.50, "family": "glass_ceramic",
                        "note": f"Container / tableware glass, batch + melt energy; {PRICE_NOTE}"},
    "glass_borosilicate": {"label": "Borosilicate glass", "inr_per_kg": 120, "density_g_cm3": 2.23,
                           "family": "glass_ceramic", "note": f"Heat-resistant tubing and labware; {PRICE_NOTE}"},
    "ceramic_stoneware": {"label": "Stoneware ceramic", "inr_per_kg": 30, "density_g_cm3": 2.30,
                          "family": "glass_ceramic", "note": f"Clay body + glaze, before firing; {PRICE_NOTE}"},
    # ---- textiles & leather -----------------------------------------------------
    "cotton_fabric": {"label": "Cotton fabric", "inr_per_kg": 400, "density_g_cm3": 1.54, "family": "textile",
                      "note": f"Knitted jersey / woven, dyed; {PRICE_NOTE}"},
    "polyester_fabric": {"label": "Polyester fabric", "inr_per_kg": 280, "density_g_cm3": 1.38, "family": "textile",
                         "note": f"Sportswear, linings, bag shells; {PRICE_NOTE}"},
    "nylon_fabric": {"label": "Nylon fabric", "inr_per_kg": 450, "density_g_cm3": 1.14, "family": "textile",
                     "note": f"Ripstop / Cordura-type bag and jacket fabric; {PRICE_NOTE}"},
    "leather": {"label": "Leather", "inr_per_kg": 1500, "density_g_cm3": 0.90, "family": "textile",
                "note": f"Finished cow/buffalo hide (usually sold per sq ft); {PRICE_NOTE}"},
    "synthetic_leather": {"label": "Synthetic leather (PU/PVC)", "inr_per_kg": 350, "density_g_cm3": 1.10,
                          "family": "textile", "note": f"Coated fabric for shoes and bags; {PRICE_NOTE}"},
    # ---- wood & paper -----------------------------------------------------------
    "wood_hard": {"label": "Hardwood", "inr_per_kg": 100, "density_g_cm3": 0.70, "family": "wood_paper",
                  "note": f"Sawn rubberwood / sheesham / acacia; {PRICE_NOTE}"},
    "plywood": {"label": "Plywood", "inr_per_kg": 85, "density_g_cm3": 0.60, "family": "wood_paper",
                "note": f"Commercial grade sheet; {PRICE_NOTE}"},
    "mdf": {"label": "MDF", "inr_per_kg": 45, "density_g_cm3": 0.75, "family": "wood_paper",
            "note": f"Flat-pack furniture board; {PRICE_NOTE}"},
    "paper_board": {"label": "Paperboard", "inr_per_kg": 60, "density_g_cm3": 0.70, "family": "wood_paper",
                    "note": f"Duplex / corrugated board; {PRICE_NOTE}"},
    "paper": {"label": "Paper", "inr_per_kg": 75, "density_g_cm3": 0.80, "family": "wood_paper",
              "note": f"Printing / writing paper; {PRICE_NOTE}"},
    # ---- electronics ------------------------------------------------------------
    "pcb_fr4_populated": {"label": "Populated PCB (FR4)", "inr_per_kg": 5000, "density_g_cm3": 1.90,
                          "family": "electronics",
                          "note": "Assembled board incl. typical low-cost components, priced per kg of board; "
                                  "indicative, varies hugely with chips"},
    "lithium_cell": {"label": "Lithium-ion cell", "inr_per_kg": 1500, "density_g_cm3": 2.50, "family": "electronics",
                     "note": f"Pouch / cylindrical cell, ~₹60-80 per 18650; {PRICE_NOTE}"},
    "led_chip": {"label": "LED chip", "inr_per_kg": 20000, "density_g_cm3": 3.00, "family": "electronics",
                 "note": "SMD LED packages (~₹0.3-0.5 each); per kg only so mass maths stays uniform"},
    "magnet_neodymium": {"label": "Neodymium magnet (NdFeB)", "inr_per_kg": 4500, "density_g_cm3": 7.50,
                         "family": "electronics", "note": f"Sintered, Ni-plated; speakers, motors, clasps; {PRICE_NOTE}"},
    "wire_copper_insulated": {"label": "Insulated copper wire", "inr_per_kg": 650, "density_g_cm3": 3.50,
                              "family": "electronics", "note": f"Copper + PVC/TPE jacket, blended; {PRICE_NOTE}"},
    # ---- fallbacks --------------------------------------------------------------
    "generic_plastic": {"label": "Plastic (unspecified)", "inr_per_kg": 150, "density_g_cm3": 1.10, "family": "plastic",
                        "note": "Fallback: average commodity/engineering resin"},
    "generic_metal": {"label": "Metal (unspecified)", "inr_per_kg": 200, "density_g_cm3": 7.00, "family": "metal",
                      "note": "Fallback: between mild steel and aluminium"},
    "generic": {"label": "Material (unspecified)", "inr_per_kg": 150, "density_g_cm3": 1.50, "family": "other",
                "note": "Fallback when the material is not recognised"},
}

# id -> label, scene, inr_per_part (amortised machine + labour), inr_per_kg (mass-dependent part), note
PROCESSES = {
    # ---- polymer moulding -------------------------------------------------------
    "injection_moulding": {"label": "Injection moulding", "scene": "machining", "inr_per_part": 1.0, "inr_per_kg": 40,
                           "note": "Cycle 20-60 s, multi-cavity steel mould"},
    "blow_moulding": {"label": "Blow moulding", "scene": "machining", "inr_per_part": 2.5, "inr_per_kg": 15,
                      "note": "Extrusion / stretch blow for bottles and containers"},
    "extrusion": {"label": "Extrusion", "scene": "machining", "inr_per_part": 0.5, "inr_per_kg": 25,
                  "note": "Continuous profiles, tubes, cable jackets, film"},
    "thermoforming": {"label": "Thermoforming", "scene": "machining", "inr_per_part": 1.0, "inr_per_kg": 30,
                      "note": "Heated sheet vacuum-formed; trim scrap is high"},
    "rotational_moulding": {"label": "Rotational moulding", "scene": "machining", "inr_per_part": 40, "inr_per_kg": 60,
                            "note": "Large hollow parts (tanks, kayaks); slow cycles"},
    "compression_moulding": {"label": "Compression moulding", "scene": "machining", "inr_per_part": 1.5,
                             "inr_per_kg": 30, "note": "Rubber, silicone and thermoset parts"},
    # ---- metal casting & forming ------------------------------------------------
    "die_casting": {"label": "Die casting", "scene": "machining", "inr_per_part": 4.0, "inr_per_kg": 60,
                    "note": "High-pressure Al/Zn casting, expensive dies"},
    "sand_casting": {"label": "Sand casting", "scene": "machining", "inr_per_part": 20, "inr_per_kg": 50,
                     "note": "Cheap patterns, rough finish, heavy parts"},
    "investment_casting": {"label": "Investment casting", "scene": "machining", "inr_per_part": 25,
                           "inr_per_kg": 300, "note": "Lost-wax; precise, labour-intensive"},
    "forging": {"label": "Forging", "scene": "machining", "inr_per_part": 6.0, "inr_per_kg": 40,
                "note": "Closed-die hot forging, flash trimmed"},
    "cnc_machining": {"label": "CNC machining", "scene": "machining", "inr_per_part": 40, "inr_per_kg": 120,
                      "note": "Milling from bar/plate; slow and wasteful"},
    "turning": {"label": "Turning", "scene": "machining", "inr_per_part": 10, "inr_per_kg": 60,
                "note": "Lathe / Swiss-type turning of round parts"},
    "sheet_metal_stamping": {"label": "Sheet metal stamping", "scene": "machining", "inr_per_part": 1.0,
                             "inr_per_kg": 10, "note": "Progressive-die blanking and forming"},
    "deep_drawing": {"label": "Deep drawing", "scene": "machining", "inr_per_part": 6.0, "inr_per_kg": 20,
                     "note": "Multi-stage draws for cups, cans, bottle shells"},
    "grinding_polishing": {"label": "Grinding & polishing", "scene": "machining", "inr_per_part": 8.0,
                           "inr_per_kg": 60, "note": "Edge grinding, sharpening, buffing to finish"},
    "heat_treatment": {"label": "Heat treatment", "scene": "thermal", "inr_per_part": 2.0, "inr_per_kg": 30,
                       "note": "Batch hardening / tempering / annealing in a furnace"},
    "bending": {"label": "Bending", "scene": "machining", "inr_per_part": 1.5, "inr_per_kg": 5,
                "note": "Press-brake / wire / tube bending"},
    # ---- joining ----------------------------------------------------------------
    "welding_arc": {"label": "Arc welding", "scene": "welding", "inr_per_part": 10, "inr_per_kg": 10,
                    "note": "TIG/MIG seam, often automated for round seams"},
    "spot_welding": {"label": "Spot welding", "scene": "welding", "inr_per_part": 1.0, "inr_per_kg": 2,
                     "note": "Resistance spot welds on sheet"},
    "brazing": {"label": "Brazing", "scene": "welding", "inr_per_part": 5.0, "inr_per_kg": 20,
                "note": "Torch / furnace brazing with filler alloy"},
    "soldering": {"label": "Soldering", "scene": "welding", "inr_per_part": 2.0, "inr_per_kg": 0,
                  "note": "Hand / selective soldering of wires and leads"},
    # ---- textiles ---------------------------------------------------------------
    "sewing_cut_and_sew": {"label": "Cut & sew", "scene": "studio", "inr_per_part": 20, "inr_per_kg": 30,
                           "note": "Cutting + stitching labour, ~10 min SMV at Indian wages"},
    "knitting": {"label": "Knitting", "scene": "studio", "inr_per_part": 5.0, "inr_per_kg": 80,
                 "note": "Flat / circular knitting of yarn into panels or uppers"},
    # ---- electronics ------------------------------------------------------------
    "pcb_assembly_smt": {"label": "PCB assembly (SMT)", "scene": "design", "inr_per_part": 3.0, "inr_per_kg": 300,
                         "note": "Placement, reflow and test (parts priced in the board material)"},
    # ---- glass & ceramic --------------------------------------------------------
    "glass_blowing": {"label": "Glass blowing", "scene": "thermal", "inr_per_part": 3.0, "inr_per_kg": 25,
                      "note": "Automatic blow-blow / press-blow (hand-blown costs far more)"},
    "glass_pressing": {"label": "Glass pressing", "scene": "thermal", "inr_per_part": 2.0, "inr_per_kg": 20,
                       "note": "Pressed tableware, lenses, jars"},
    "ceramic_firing": {"label": "Ceramic forming & firing", "scene": "thermal", "inr_per_part": 15, "inr_per_kg": 50,
                       "note": "Jiggering/slip casting, glazing and kiln firing (energy heavy)"},
    # ---- decoration & finishing -------------------------------------------------
    "printing": {"label": "Printing", "scene": "design", "inr_per_part": 5.0, "inr_per_kg": 0,
                 "note": "Screen / pad / heat-transfer print, per print area"},
    "laser_engraving": {"label": "Laser engraving", "scene": "design", "inr_per_part": 4.0, "inr_per_kg": 0,
                        "note": "Logos and markings"},
    "anodising": {"label": "Anodising", "scene": "thermal", "inr_per_part": 3.0, "inr_per_kg": 60,
                  "note": "Aluminium oxide layer, dyed"},
    "powder_coating": {"label": "Powder coating", "scene": "thermal", "inr_per_part": 4.0, "inr_per_kg": 40,
                       "note": "Electrostatic powder + oven cure"},
    "electroplating": {"label": "Electroplating", "scene": "thermal", "inr_per_part": 4.0, "inr_per_kg": 50,
                       "note": "Ni/Cr/Cu plating, or electropolish on stainless"},
    "painting": {"label": "Painting", "scene": "thermal", "inr_per_part": 3.0, "inr_per_kg": 40,
                 "note": "Spray paint / lacquer"},
    # ---- other ------------------------------------------------------------------
    "assembly_manual": {"label": "Manual assembly", "scene": "studio", "inr_per_part": 4.0, "inr_per_kg": 0,
                        "note": "Sub-assembly labour step on this part"},
    "3d_printing": {"label": "3D printing", "scene": "design", "inr_per_part": 20, "inr_per_kg": 2000,
                    "note": "FDM/SLA machine time; no tooling but slow"},
    "woodworking": {"label": "Woodworking", "scene": "machining", "inr_per_part": 30, "inr_per_kg": 100,
                    "note": "Sawing, routing, sanding, finishing"},
    "generic": {"label": "Forming (unspecified)", "scene": "machining", "inr_per_part": 3.0, "inr_per_kg": 30,
                "note": "Fallback when the process is not recognised"},
}

# One-off tooling cost (INR) per process, amortised over TOOL_LIFE_YEARS of production.
TOOLING_INR = {
    "injection_moulding": 600_000, "blow_moulding": 400_000, "extrusion": 150_000, "thermoforming": 150_000,
    "rotational_moulding": 300_000, "compression_moulding": 250_000, "die_casting": 1_500_000,
    "sand_casting": 50_000, "investment_casting": 300_000, "forging": 800_000, "sheet_metal_stamping": 500_000,
    "deep_drawing": 800_000, "bending": 50_000, "welding_arc": 50_000, "spot_welding": 30_000, "brazing": 20_000,
    "soldering": 10_000, "glass_blowing": 400_000, "glass_pressing": 300_000, "ceramic_firing": 100_000,
    "printing": 5_000, "woodworking": 20_000, "generic": 100_000,
}
TOOL_LIFE_YEARS = 3
TOOL_REF_MASS_G = 100  # tooling cost above is for a ~100 g part; scaled by sqrt(mass), clamped
TOOL_SCALE_MIN, TOOL_SCALE_MAX = 0.3, 5.0

# Material bought ÷ material in the finished part (runners, trim, chips, offcuts, rejects).
SCRAP_FACTOR = {
    "injection_moulding": 1.03, "blow_moulding": 1.05, "extrusion": 1.03, "thermoforming": 1.15,
    "rotational_moulding": 1.03, "compression_moulding": 1.08, "die_casting": 1.08, "sand_casting": 1.15,
    "investment_casting": 1.10, "forging": 1.15, "cnc_machining": 1.60, "turning": 1.40,
    "sheet_metal_stamping": 1.20, "deep_drawing": 1.25, "grinding_polishing": 1.05, "sewing_cut_and_sew": 1.15, "knitting": 1.05,
    "glass_blowing": 1.10, "glass_pressing": 1.08, "ceramic_firing": 1.10, "3d_printing": 1.05,
    "woodworking": 1.40, "generic": 1.10,
}
DEFAULT_SCRAP = 1.05

# Region multipliers on (material prices, labour/machine rates).
REGIONS = {"IN": {"material": 1.00, "labour": 1.00}, "CN": {"material": 0.95, "labour": 1.10}}

ASSEMBLY_BASE_INR = 1.0          # final inspection / handling of the finished product
ASSEMBLY_PER_COMPONENT_INR = 1.0  # each additional distinct component to join
ASSEMBLY_PER_EXTRA_QTY_INR = 0.3  # each repeated identical part (screws, rivets…)
PACKAGING_FRACTION = 0.04
PACKAGING_FLOOR_INR = 2.0
OVERHEAD_FRACTION = 0.12          # factory overhead + factory profit
MIN_MASS_G, MAX_MASS_G, DEFAULT_MASS_G = 0.1, 500_000, 50.0
MAX_QTY = 10_000

# Common spellings an LLM might use instead of our ids.
SMALL_PART_G = 10.0          # below this mass, per-part process charges scale down linearly
SMALL_PART_MIN_FACTOR = 0.1

ALIASES = {
    "pcb_fr4": "pcb_fr4_populated", "pcb": "pcb_fr4_populated", "fr4": "pcb_fr4_populated",
    "polypropylene": "pp", "polycarbonate": "pc", "acrylic": "pmma", "nylon": "nylon_pa6", "pa6": "nylon_pa6",
    "rubber": "rubber_natural", "eva": "eva_foam", "foam": "pu_foam", "pu": "pu_foam",
    "steel": "steel_mild", "mild_steel": "steel_mild", "carbon_steel": "steel_mild",
    "stainless": "stainless_304", "stainless_steel": "stainless_304", "ss304": "stainless_304", "ss": "stainless_304",
    "aluminium": "aluminium_6061", "aluminium_alloy": "aluminium_6061", "zinc": "zinc_die_cast", "zamak": "zinc_die_cast",
    "glass": "glass_soda_lime", "borosilicate": "glass_borosilicate", "ceramic": "ceramic_stoneware",
    "porcelain": "ceramic_stoneware", "stoneware": "ceramic_stoneware",
    "cotton": "cotton_fabric", "polyester": "polyester_fabric", "wood": "wood_hard", "hardwood": "wood_hard",
    "cardboard": "paper_board", "plastic": "generic_plastic", "metal": "generic_metal",
    "battery": "lithium_cell", "li_ion": "lithium_cell", "led": "led_chip", "magnet": "magnet_neodymium",
    "wire": "wire_copper_insulated", "cable": "wire_copper_insulated", "faux_leather": "synthetic_leather",
    "pu_leather": "synthetic_leather",
    # processes
    "moulding": "injection_moulding", "casting": "die_casting", "machining": "cnc_machining",
    "milling": "cnc_machining", "stamping": "sheet_metal_stamping", "welding": "welding_arc",
    "tig_welding": "welding_arc", "mig_welding": "welding_arc", "sewing": "sewing_cut_and_sew",
    "cut_and_sew": "sewing_cut_and_sew", "smt": "pcb_assembly_smt", "pcb_assembly": "pcb_assembly_smt",
    "assembly": "assembly_manual", "grinding": "grinding_polishing", "polishing": "grinding_polishing",
    "sharpening": "grinding_polishing", "hardening": "heat_treatment", "annealing": "heat_treatment", "screen_printing": "printing", "pad_printing": "printing",
    "anodizing": "anodising", "plating": "electroplating", "coating": "painting", "firing": "ceramic_firing",
    "kiln_firing": "ceramic_firing", "slip_casting": "ceramic_firing", "glazing": "ceramic_firing",
    "vulcanization": "compression_moulding", "vulcanisation": "compression_moulding",
    "braiding": "knitting", "weaving": "knitting", "embroidery": "sewing_cut_and_sew", "additive_manufacturing": "3d_printing", "carpentry": "woodworking",
}

MATERIAL_GROUPS = {
    "Plastics": "plastic", "Metals": "metal", "Glass/ceramic": "glass_ceramic", "Textiles": "textile",
    "Wood/paper": "wood_paper", "Electronics": "electronics",
}
PROCESS_GROUPS = {
    "Moulding": ["injection_moulding", "blow_moulding", "extrusion", "thermoforming", "rotational_moulding",
                 "compression_moulding"],
    "Metal": ["die_casting", "sand_casting", "investment_casting", "forging", "cnc_machining", "turning",
              "sheet_metal_stamping", "deep_drawing", "bending", "grinding_polishing", "heat_treatment"],
    "Joining": ["welding_arc", "spot_welding", "brazing", "soldering", "assembly_manual"],
    "Textile/electronics": ["sewing_cut_and_sew", "knitting", "pcb_assembly_smt"],
    "Glass/ceramic": ["glass_blowing", "glass_pressing", "ceramic_firing"],
    "Finishing": ["printing", "laser_engraving", "anodising", "powder_coating", "electroplating", "painting"],
    "Other": ["3d_printing", "woodworking", "generic"],
}


def _norm(x) -> str:
    s = re.sub(r"[\s\-/]+", "_", str(x or "").strip().lower())
    return s.replace("molding", "moulding").replace("aluminum", "aluminium")


def _resolve(raw, table: dict) -> str | None:
    key = _norm(raw)
    if key in table:
        return key
    key = ALIASES.get(key, key)
    return key if key in table else None


def _guess_material(raw) -> str:
    key = _norm(raw)
    if any(w in key for w in ("steel", "metal", "alu", "iron", "alloy", "chrome", "brass", "copper")):
        return "generic_metal"
    if any(w in key for w in ("plastic", "poly", "resin", "vinyl", "rubber")):
        return "generic_plastic"
    return "generic"


def _r1(x: float) -> float:
    return round(x + 0.0, 1)


def estimate_cost(components: list[dict], *, units_per_year: int = 100_000, region: str = "IN") -> dict:
    """
    Should-cost of one finished product, in INR.

    components: [{"name": str, "material_id": str, "mass_g": float, "process_ids": [str], "qty": int}]
    Unknown material/process ids fall back to a generic entry and are reported in "warnings".
    An electronics part with no process_ids is treated as bought-in (material price only).

    Returns the `cost` object of the teardown response (contract section 3):
        {"currency", "materials", "processing", "assembly", "packaging", "overhead", "total",
         "breakdown": [{"label", "kind": "material"|"process", "amount"}], "warnings": [str],
    plus one extra key for the caller to fill components[i].cost etc.:
         "components": [{"name", "cost", "material_label", "process_labels"}]}   # same order as input
    Component cost = its material + processing + amortised tooling (no assembly/packaging/overhead).
    Breakdown amounts sum to materials + processing (tooling is folded into its process).
    """
    warnings: list[str] = []
    reg = REGIONS.get(str(region or "IN").upper())
    if reg is None:
        warnings.append(f"Region '{region}' not modelled; used India rates.")
        reg = REGIONS["IN"]
    try:
        upy = int(units_per_year)
    except (TypeError, ValueError):
        upy = 100_000
    if upy < 100:
        warnings.append(f"units_per_year={units_per_year} too low to model; used 100.")
        upy = 100
    tool_parts = upy * TOOL_LIFE_YEARS

    mat_by_label: dict[str, float] = {}
    proc_by_label: dict[str, float] = {}
    out_components = []
    materials_total = processing_total = 0.0
    n_components = extra_qty = 0

    for i, c in enumerate(components or []):
        c = c if isinstance(c, dict) else {}
        name = str(c.get("name") or f"Part {i + 1}")

        mid = _resolve(c.get("material_id"), MATERIALS)
        if mid is None:
            mid = _guess_material(c.get("material_id"))
            warnings.append(f"{name}: unknown material '{c.get('material_id')}', priced as {MATERIALS[mid]['label']}.")
        mat = MATERIALS[mid]

        try:
            mass_g = float(c.get("mass_g"))
            if not math.isfinite(mass_g):
                raise ValueError
        except (TypeError, ValueError):
            warnings.append(f"{name}: mass missing or invalid, assumed {DEFAULT_MASS_G:g} g.")
            mass_g = DEFAULT_MASS_G
        if mass_g < MIN_MASS_G:
            warnings.append(f"{name}: mass {mass_g:g} g is not physical, clamped to {MIN_MASS_G:g} g.")
            mass_g = MIN_MASS_G
        elif mass_g > MAX_MASS_G:
            warnings.append(f"{name}: mass {mass_g:g} g is implausible, clamped to {MAX_MASS_G / 1000:g} kg.")
            mass_g = MAX_MASS_G
        m = mass_g / 1000

        try:
            qty = int(c.get("qty", 1) if c.get("qty") is not None else 1)
        except (TypeError, ValueError):
            warnings.append(f"{name}: qty '{c.get('qty')}' invalid, assumed 1.")
            qty = 1
        if qty < 1 or qty > MAX_QTY:
            warnings.append(f"{name}: qty {c.get('qty')} out of range, clamped.")
            qty = min(max(qty, 1), MAX_QTY)

        pids = []
        raw_pids = c.get("process_ids") or []
        if isinstance(raw_pids, str):
            raw_pids = [raw_pids]
        for raw in raw_pids:
            pid = _resolve(raw, PROCESSES)
            if pid is None:
                warnings.append(f"{name}: unknown process '{raw}', priced as generic forming.")
                pid = "generic"
            if pid not in pids:
                pids.append(pid)
        if not pids and mat["family"] != "electronics":
            warnings.append(f"{name}: no process given, assumed generic forming.")
            pids = ["generic"]
        # (electronics with no process = bought-in component, material price only)

        scrap = max([SCRAP_FACTOR.get(p, DEFAULT_SCRAP) for p in pids] or [1.0])
        tool_scale = min(max(math.sqrt(mass_g / TOOL_REF_MASS_G), TOOL_SCALE_MIN), TOOL_SCALE_MAX)
        # Tiny parts (eyelets, rivets, springs) are made many per cycle, so the per-part machine
        # charge shrinks with size instead of being paid in full for each piece.
        batch = min(max(mass_g / SMALL_PART_G, SMALL_PART_MIN_FACTOR), 1.0)
        mat_cost = qty * m * mat["inr_per_kg"] * reg["material"] * scrap
        comp_proc = 0.0
        for p in pids:
            pr = PROCESSES[p]
            amount = qty * (pr["inr_per_part"] * batch + m * pr["inr_per_kg"]) * reg["labour"]
            amount += TOOLING_INR.get(p, 0) * tool_scale / tool_parts
            comp_proc += amount
            proc_by_label[pr["label"]] = proc_by_label.get(pr["label"], 0.0) + amount
        mat_by_label[mat["label"]] = mat_by_label.get(mat["label"], 0.0) + mat_cost

        materials_total += mat_cost
        processing_total += comp_proc
        n_components += 1
        extra_qty += qty - 1
        out_components.append({
            "name": name, "cost": _r1(mat_cost + comp_proc), "material_label": mat["label"],
            "process_labels": [PROCESSES[p]["label"] for p in pids],
        })

    if n_components == 0:
        warnings.append("No components given; nothing to cost.")
        assembly = 0.0
    else:
        assembly = (ASSEMBLY_BASE_INR + ASSEMBLY_PER_COMPONENT_INR * (n_components - 1)
                    + ASSEMBLY_PER_EXTRA_QTY_INR * extra_qty) * reg["labour"]
    subtotal = materials_total + processing_total + assembly
    packaging = max(PACKAGING_FLOOR_INR, PACKAGING_FRACTION * subtotal) if n_components else 0.0
    overhead = OVERHEAD_FRACTION * (subtotal + packaging)

    parts = {"materials": _r1(materials_total), "processing": _r1(processing_total), "assembly": _r1(assembly),
             "packaging": _r1(packaging), "overhead": _r1(overhead)}
    breakdown = ([{"label": k, "kind": "material", "amount": _r1(v)} for k, v in mat_by_label.items()]
                 + [{"label": k, "kind": "process", "amount": _r1(v)} for k, v in proc_by_label.items()])
    breakdown.sort(key=lambda b: -b["amount"])
    return {
        "currency": "INR",
        **parts,
        "total": _r1(sum(parts.values())),
        "breakdown": breakdown,
        "warnings": warnings,
        "components": out_components,
    }


def verdict(multiple: float | None) -> str | None:
    """Contract buckets: <2 Fair deal, 2–4 Normal retail, 4–8 Brand premium, 8–20 Premium brand, ≥20 Mostly marketing."""
    if multiple is None:
        return None
    if multiple < 2:
        return "Fair deal"
    if multiple < 4:
        return "Normal retail"
    if multiple < 8:
        return "Brand premium"
    if multiple < 20:
        return "Premium brand"
    return "Mostly marketing"


def build_markup(total: float, price_used: float | None) -> dict:
    """The `markup` object: price_used, multiple (1 dp), verdict, where_the_money_goes."""
    total = _r1(max(float(total or 0), 0.0))
    try:
        price = float(price_used) if price_used is not None else None
    except (TypeError, ValueError):
        price = None
    if not price or price <= 0 or total <= 0:
        return {"price_used": price if price and price > 0 else None, "multiple": None, "verdict": None,
                "where_the_money_goes": [{"label": "Making it", "amount": total}]}
    multiple = round(price / total, 1)
    return {
        "price_used": _r1(price) if price != int(price) else int(price),
        "multiple": multiple,
        "verdict": verdict(multiple),
        "where_the_money_goes": [
            {"label": "Making it", "amount": total},
            {"label": "Shipping, retail, brand, profit, tax", "amount": _r1(max(price - total, 0.0))},
        ],
    }


def catalog_for_prompt() -> str:
    """Compact id list for the vision prompt (ids are self-describing; one line per group)."""
    lines = ["MATERIAL ids:"]
    for group, fam in MATERIAL_GROUPS.items():
        ids = [k for k, v in MATERIALS.items() if v["family"] == fam and not k.startswith("generic")]
        lines.append(f"{group}: {', '.join(ids)}")
    lines.append("Fallback: generic_plastic, generic_metal, generic")
    lines.append("PROCESS ids:")
    for group, ids in PROCESS_GROUPS.items():
        lines.append(f"{group}: {', '.join(ids)}")
    return "\n".join(lines)
