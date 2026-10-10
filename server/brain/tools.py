"""
LangChain tools the agent can call. Calculators are deterministic Python —
the LLM decides *when* to use them, never invents the numbers.
"""

import json
import time
from typing import Optional

from langchain_core.tools import tool

from .config import KNOWLEDGE_DIR
from .engineering import fasteners, welding
from .store import kb


SNIPPET_CHARS = 800


def _fmt(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False)


@tool
def search_knowledge(query: str, module: Optional[str] = None, k: int = 4) -> str:
    """Search Siddhivinayak's learned knowledge (notes PDF, screws, welding, memory, any uploaded file).
    Use this for ANY engineering theory, definition, formula or fact before answering.
    module: one of the known modules (e.g. 'notes', 'screws', 'welding', 'memory') or omit for all.
    Returns passages with [file p.N] citations."""
    hits = kb.search(query, module=module, k=min(max(k, 1), 8))
    if not hits:
        return "No matching knowledge found."
    out = []
    for h in hits:
        out.append(f"[{h['file']} p.{h['page']}] (module={h['module']}, doc_id={h['doc_id']}) "
                   f"{h['heading']}\n{h['text'][:SNIPPET_CHARS]}")
    return "\n\n---\n\n".join(out)


@tool
def list_modules() -> str:
    """List the knowledge modules and how many files/chunks each has learned."""
    return _fmt(kb.modules())


@tool
def remember(fact: str, topic: str = "general") -> str:
    """Permanently learn a fact, preference, correction or experience the user teaches you
    (e.g. 'our plant uses 10.9 bolts for gearbox mounts'). It becomes searchable in module 'memory'."""
    f = KNOWLEDGE_DIR / "memory" / "learned.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {topic} ({time.strftime('%Y-%m-%d')})\n{fact.strip()}\n")
    kb.sync()
    return f"Learned and indexed under memory/{topic}."


@tool
def thread_data(nominal_diameter_mm: float, pitch_mm: Optional[float] = None) -> str:
    """ISO metric thread geometry (M-thread): pitch diameter, minor diameters, tensile stress area,
    tap drill, hex size, clearance hole. pitch_mm omitted = coarse pitch."""
    return _fmt(fasteners.thread_geometry(nominal_diameter_mm, pitch_mm))


@tool
def bolt_strength(nominal_diameter_mm: float, property_class: str = "8.8", pitch_mm: Optional[float] = None) -> str:
    """ISO 898-1 bolt proof load, yield load and ultimate load for a metric bolt of a property class
    (4.6, 4.8, 5.6, 5.8, 6.8, 8.8, 9.8, 10.9, 12.9)."""
    return _fmt(fasteners.bolt_strength(nominal_diameter_mm, property_class, pitch_mm))


@tool
def bolt_torque(nominal_diameter_mm: float, property_class: str = "8.8", pitch_mm: Optional[float] = None,
                preload_fraction: float = 0.75, mu_thread: float = 0.12, mu_head: float = 0.12,
                nut_factor: Optional[float] = None) -> str:
    """Recommended preload and tightening torque for a metric bolt (VDI 2230 formula plus T=K·F·d).
    preload_fraction of proof load: 0.75 reusable, 0.9 permanent."""
    return _fmt(fasteners.tightening_torque(nominal_diameter_mm, property_class, pitch_mm,
                                            preload_fraction, mu_thread, mu_head, nut_factor))


@tool
def bolted_joint_check(nominal_diameter_mm: float, property_class: str, axial_load_kN: float = 0.0,
                       shear_load_kN: float = 0.0, n_bolts: int = 1, joint_stiffness_C: float = 0.25,
                       friction_coeff_interface: float = 0.2) -> str:
    """Check a bolted joint: bolt force, proof-load safety factor, separation and slip safety factors."""
    return _fmt(fasteners.bolt_joint_check(nominal_diameter_mm, property_class, axial_load_kN, shear_load_kN,
                                           n_bolts, joint_stiffness_C=joint_stiffness_C,
                                           friction_coeff_interface=friction_coeff_interface))


@tool
def welding_process(name_or_number: str) -> str:
    """Look up a welding process by ISO 4063 number (e.g. 135, 141) or AWS name (SMAW, GMAW, GTAW, SAW, FSW...)."""
    return _fmt(welding.process_info(name_or_number))


@tool
def electrode_decode(code: str) -> str:
    """Decode an AWS A5.1 SMAW electrode classification such as E7018, E6013, E6010, E7018-1 H4R."""
    return _fmt(welding.decode_electrode(code))


@tool
def weld_heat_input(voltage_V: float, current_A: float, travel_speed_mm_min: float, process: str = "135") -> str:
    """Arc energy and heat input (kJ/mm) per EN 1011-1. process = ISO 4063 number (111, 121, 135, 141...)."""
    return _fmt(welding.heat_input(voltage_V, current_A, travel_speed_mm_min, process))


@tool
def carbon_equivalent(C: float, Mn: float = 0, Cr: float = 0, Mo: float = 0, V: float = 0,
                      Ni: float = 0, Cu: float = 0, Si: float = 0, B: float = 0) -> str:
    """Carbon equivalent (IIW CE) and Pcm of a steel from its composition in wt%, with weldability/preheat guidance."""
    return _fmt(welding.carbon_equivalent(C, Mn, Cr, Mo, V, Ni, Cu, Si, B))


@tool
def fillet_weld(load_kN: float, length_mm: float, leg_mm: Optional[float] = None,
                allowable_shear_MPa: float = 144.0, n_welds: int = 1) -> str:
    """Fillet weld throat-shear check (give leg_mm) or sizing (omit leg_mm). Default allowable 0.3×480 MPa (E70)."""
    return _fmt(welding.fillet_weld(load_kN, length_mm, leg_mm, allowable_shear_MPa, n_welds))


ALL_TOOLS = [search_knowledge, list_modules, remember, thread_data, bolt_strength, bolt_torque,
             bolted_joint_check, welding_process, electrode_decode, weld_heat_input,
             carbon_equivalent, fillet_weld]
