"""
Picks a 3D scene for the frontend from what the conversation is about.
The frontend maps each scene id to background, lighting and particles.
"""

import re

SCENES = {
    "welding": ["weld", "arc", "electrode", "tig", "mig", "mag", "smaw", "gmaw", "gtaw", "saw", "e7018",
                "haz", "heat input", "filler", "brazing", "soldering", "spot weld", "porosity", "spatter"],
    "fasteners": ["screw", "bolt", "nut", "thread", "torque", "preload", "fastener", "washer", "rivet",
                  "property class", "pitch", "m8", "m10", "m12", "m16", "m20", "stud", "joint"],
    "fluids": ["fluid", "flow", "bernoulli", "reynolds", "viscosity", "pump", "turbine", "pipe", "boundary layer",
               "hydraulic", "nozzle", "pressure head"],
    "thermal": ["heat transfer", "thermo", "entropy", "enthalpy", "boiler", "refrigeration", "conduction",
                "convection", "radiation", "otto", "diesel", "brayton", "rankine", "ic engine", "temperature"],
    "machining": ["machining", "lathe", "milling", "drilling", "cutting tool", "chip", "taylor", "casting",
                  "forging", "rolling", "extrusion", "ecm", "edm", "grinding", "sheet metal", "manufactur"],
    "design": ["stress", "strain", "beam", "shaft", "gear", "bearing", "spring", "fatigue", "design",
               "deflection", "column", "mohr", "theory of failure", "vibration", "mechanism", "cam"],
}
TOOL_SCENE = {
    "thread_data": "fasteners", "bolt_strength": "fasteners", "bolt_torque": "fasteners",
    "bolted_joint_check": "fasteners", "welding_process": "welding", "electrode_decode": "welding",
    "weld_heat_input": "welding", "carbon_equivalent": "welding", "fillet_weld": "welding",
}


def detect_scene(text: str, tools_used: list[str]) -> str:
    for t in tools_used:
        if t in TOOL_SCENE:
            return TOOL_SCENE[t]
    text = text.lower()
    scores = {s: sum(len(re.findall(r"\b" + re.escape(k), text)) for k in kws) for s, kws in SCENES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "studio"
