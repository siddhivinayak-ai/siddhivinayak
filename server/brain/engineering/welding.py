"""
Welding module: process data (ISO 4063), electrode classification (AWS A5.1),
heat input (EN 1011-1 / ISO/TR 17671-1), carbon equivalents and fillet-weld sizing.
"""

import math
import re

# ISO 4063 reference numbers with the AWS name used in the US.
PROCESSES = {
    "111": {"name": "Manual metal arc (MMA)", "aws": "SMAW", "k": 0.8, "shield": "Flux coating",
            "use": "Site work, structural, repair; all positions; tolerant of wind"},
    "114": {"name": "Self-shielded flux-cored arc", "aws": "FCAW-S", "k": 0.8, "shield": "Flux core only",
            "use": "Outdoor structural and pipeline work without gas"},
    "121": {"name": "Submerged arc, single wire", "aws": "SAW", "k": 1.0, "shield": "Granular flux",
            "use": "Thick plate, long straight seams, pressure vessels; flat/horizontal only"},
    "131": {"name": "MIG (inert gas)", "aws": "GMAW", "k": 0.8, "shield": "Ar / Ar-He",
            "use": "Aluminium and other non-ferrous metals"},
    "135": {"name": "MAG, solid wire (active gas)", "aws": "GMAW", "k": 0.8, "shield": "CO2 or Ar+CO2/O2",
            "use": "Carbon & low-alloy steel fabrication, high productivity"},
    "136": {"name": "MAG, flux-cored wire", "aws": "FCAW-G", "k": 0.8, "shield": "Ar+CO2 or CO2",
            "use": "Structural steel, positional welding with high deposition"},
    "138": {"name": "MAG, metal-cored wire", "aws": "GMAW-C", "k": 0.8, "shield": "Ar+CO2",
            "use": "High deposition, little slag, robotic welding"},
    "141": {"name": "TIG with solid filler", "aws": "GTAW", "k": 0.6, "shield": "Ar / Ar-He",
            "use": "Root passes, thin sheet, stainless, aluminium, highest quality"},
    "15": {"name": "Plasma arc welding", "aws": "PAW", "k": 0.6, "shield": "Ar plasma + shield gas",
           "use": "Keyhole welding of thin to medium sections, precision"},
    "21": {"name": "Resistance spot welding", "aws": "RSW", "k": None, "shield": "None",
           "use": "Sheet metal, automotive bodies"},
    "22": {"name": "Resistance seam welding", "aws": "RSEW", "k": None, "shield": "None",
           "use": "Leak-tight sheet seams, fuel tanks"},
    "311": {"name": "Oxy-acetylene welding", "aws": "OAW", "k": None, "shield": "Flame envelope",
            "use": "Repair, thin sheet, brazing"},
    "42": {"name": "Friction welding", "aws": "FRW", "k": None, "shield": "None (solid state)",
           "use": "Shafts, dissimilar metals, axle tubes"},
    "43": {"name": "Friction stir welding", "aws": "FSW", "k": None, "shield": "None (solid state)",
           "use": "Aluminium panels, aerospace, rail, battery trays"},
    "51": {"name": "Electron beam welding", "aws": "EBW", "k": None, "shield": "Vacuum",
           "use": "Deep narrow welds, aerospace, precision parts"},
    "52": {"name": "Laser beam welding", "aws": "LBW", "k": None, "shield": "Ar / He / N2",
           "use": "High speed, low distortion, automotive, e-mobility"},
    "72": {"name": "Electroslag welding", "aws": "ESW", "k": None, "shield": "Molten slag",
           "use": "Very thick vertical sections"},
    "783": {"name": "Drawn arc stud welding with ceramic ferrule", "aws": "SW", "k": None, "shield": "Ceramic ferrule",
            "use": "Shear studs on beams and decks"},
}

# AWS A5.1 last two digits → coating, current
AWS_COATING = {
    "10": ("High cellulose, sodium", "DCEP"),
    "11": ("High cellulose, potassium", "AC or DCEP"),
    "12": ("High titania, sodium", "AC or DCEN"),
    "13": ("High titania, potassium", "AC, DCEP or DCEN"),
    "14": ("Iron powder, titania", "AC, DCEP or DCEN"),
    "15": ("Low hydrogen, sodium", "DCEP"),
    "16": ("Low hydrogen, potassium", "AC or DCEP"),
    "18": ("Low hydrogen, potassium, iron powder", "AC or DCEP"),
    "19": ("Iron oxide, titania, potassium", "AC, DCEP or DCEN"),
    "20": ("High iron oxide", "AC, DCEP or DCEN"),
    "24": ("Iron powder, titania", "AC, DCEP or DCEN"),
    "27": ("High iron oxide, iron powder", "AC, DCEP or DCEN"),
    "28": ("Low hydrogen, potassium, iron powder", "AC or DCEP"),
    "48": ("Low hydrogen, potassium, iron powder", "AC or DCEP"),
}
AWS_POSITION = {
    "1": "All positions (flat, horizontal, vertical-up, overhead)",
    "2": "Flat and horizontal fillet only",
    "4": "Flat, horizontal, overhead, vertical-down",
}


def process_info(query: str) -> dict:
    q = query.strip().upper()
    for num, p in PROCESSES.items():
        if q in (num, p["aws"]) or q.lower() in p["name"].lower():
            return {"iso_4063": num, **p}
    return {"error": f"Unknown process '{query}'", "known": {k: f"{v['name']} ({v['aws']})" for k, v in PROCESSES.items()}}


def decode_electrode(code: str) -> dict:
    """Decode an AWS A5.1 carbon-steel SMAW electrode, e.g. E7018, E6013, E7018-1 H4R."""
    m = re.match(r"^E(\d{2})(\d)(\d)(.*)$", code.strip().upper().replace(" ", ""))
    if not m:
        return {"error": "Expected AWS A5.1 form EXXYZ, e.g. E7018"}
    strength, pos, last, suffix = m.groups()
    coating = AWS_COATING.get(pos + last) or AWS_COATING.get("1" + last) or ("Unknown", "?")
    out = {
        "electrode": code.upper(),
        "min_tensile_strength": f"{strength} ksi (~{round(int(strength) * 6.895)} MPa)",
        "position": AWS_POSITION.get(pos, "Unknown position digit"),
        "coating": coating[0], "current": coating[1],
        "low_hydrogen": "Low hydrogen" in coating[0],
    }
    extras = []
    if "-1" in suffix:
        extras.append("-1: improved impact toughness (Charpy at -46 °C)")
    hm = re.search(r"H(4|8|16)", suffix)
    if hm:
        extras.append(f"H{hm.group(1)}: diffusible hydrogen ≤ {hm.group(1)} mL/100 g weld metal")
    if suffix.endswith("R"):
        extras.append("R: moisture-resistant coating")
    if extras:
        out["suffixes"] = extras
    if out["low_hydrogen"]:
        out["handling"] = "Store in heated holding oven; re-bake per manufacturer when exposed (low-hydrogen)."
    return out


def heat_input(voltage_V: float, current_A: float, travel_speed_mm_min: float, process: str = "135") -> dict:
    """Arc energy E = U·I·60/(v·1000) kJ/mm; heat input Q = k·E (EN 1011-1)."""
    info = PROCESSES.get(str(process))
    k = info["k"] if info and info["k"] else 0.8
    E = voltage_V * current_A * 60 / (travel_speed_mm_min * 1000)
    Q = k * E
    band = "low (<1.0 kJ/mm): fast cooling, watch hardness/cracking" if Q < 1.0 else \
        "medium (1.0-2.5 kJ/mm): typical for structural steel" if Q <= 2.5 else \
        "high (>2.5 kJ/mm): slower cooling, watch toughness/grain growth and distortion"
    return {
        "process": f"{process} {info['name'] if info else ''}".strip(),
        "arc_energy_kJ_per_mm": round(E, 3), "thermal_efficiency_k": k,
        "heat_input_kJ_per_mm": round(Q, 3), "interpretation": band,
    }


def carbon_equivalent(C: float, Mn: float = 0, Cr: float = 0, Mo: float = 0, V: float = 0,
                      Ni: float = 0, Cu: float = 0, Si: float = 0, B: float = 0) -> dict:
    """IIW CE and Ito-Bessyo Pcm (all inputs in wt%)."""
    ce = C + Mn / 6 + (Cr + Mo + V) / 5 + (Ni + Cu) / 15
    pcm = C + Si / 30 + (Mn + Cu + Cr) / 20 + Ni / 60 + Mo / 15 + V / 10 + 5 * B
    if ce <= 0.35:
        guide = "Good weldability; preheat usually not needed for normal thicknesses."
    elif ce <= 0.45:
        guide = "Moderate; preheat may be needed for thick sections or high restraint. Use low-hydrogen consumables."
    elif ce <= 0.55:
        guide = "Hardenable; preheat (≈100-200 °C range) and low-hydrogen process generally required."
    else:
        guide = "Difficult; high preheat, controlled interpass, low-hydrogen consumables and often PWHT."
    return {"CE_IIW": round(ce, 3), "Pcm": round(pcm, 3), "guidance": guide,
            "note": "Rule-of-thumb only. Determine preheat with EN 1011-2 (CET method) or AWS D1.1 Annex H."}


def fillet_weld(load_kN: float, length_mm: float, leg_mm: float | None = None,
                allowable_shear_MPa: float = 0.3 * 480, n_welds: int = 1) -> dict:
    """
    Fillet weld throat shear: τ = F / (0.707·s·L·n).
    Default allowable = 0.3 × 480 MPa (AWS D1.1 ASD style for E70 filler).
    Give leg_mm to check, or omit it to size the weld.
    """
    F = load_kN * 1000
    if leg_mm is None:
        a_req = F / (allowable_shear_MPa * length_mm * n_welds)
        leg = a_req / 0.7071
        return {"required_throat_mm": round(a_req, 2), "required_leg_mm": round(leg, 2),
                "suggested_leg_mm": math.ceil(leg),
                "allowable_shear_MPa": allowable_shear_MPa,
                "note": "Also respect minimum fillet size for the thicker plate per your code."}
    a = 0.7071 * leg_mm
    tau = F / (a * length_mm * n_welds)
    return {"throat_mm": round(a, 2), "shear_stress_MPa": round(tau, 1),
            "allowable_shear_MPa": allowable_shear_MPa,
            "utilisation": round(tau / allowable_shear_MPa, 2),
            "ok": tau <= allowable_shear_MPa}
