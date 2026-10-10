"""
Fasteners module: ISO metric screw threads and bolted-joint calculations.

Geometry is computed from the ISO 68-1 basic profile (not a lookup table), so it is
exact for any diameter/pitch combination:
    d2 = d - 0.649519·P        (pitch diameter)
    d3 = d - 1.226869·P        (minor diameter, external thread)
    D1 = d - 1.082532·P        (minor diameter, internal thread)
    As = π/4 · ((d2 + d3)/2)²  (tensile stress area, ISO 898-1)

References: ISO 68-1, ISO 261, ISO 262, ISO 724, ISO 898-1, ISO 4032 (hex nuts),
ISO 273 (clearance holes), VDI 2230 (tightening torque).
"""

import math

# ISO 261 / 262 preferred coarse pitches (mm)
COARSE_PITCH = {
    1.6: 0.35, 2: 0.4, 2.5: 0.45, 3: 0.5, 4: 0.7, 5: 0.8, 6: 1.0, 8: 1.25, 10: 1.5,
    12: 1.75, 14: 2.0, 16: 2.0, 20: 2.5, 24: 3.0, 30: 3.5, 36: 4.0, 42: 4.5, 48: 5.0,
}
# ISO 262 common fine pitches
FINE_PITCH = {
    8: [1.0], 10: [1.25, 1.0], 12: [1.5, 1.25], 14: [1.5], 16: [1.5], 20: [1.5, 2.0],
    24: [2.0], 30: [2.0], 36: [3.0], 42: [3.0], 48: [3.0],
}
# Hex width across flats s (ISO 4032 / ISO 4014) and medium clearance hole dh (ISO 273), mm
HEX_AF = {1.6: 3.2, 2: 4, 2.5: 5, 3: 5.5, 4: 7, 5: 8, 6: 10, 8: 13, 10: 16, 12: 18, 14: 21,
          16: 24, 20: 30, 24: 36, 30: 46, 36: 55, 42: 65, 48: 75}
CLEARANCE_MEDIUM = {1.6: 1.8, 2: 2.4, 2.5: 2.9, 3: 3.4, 4: 4.5, 5: 5.5, 6: 6.6, 8: 9, 10: 11,
                    12: 13.5, 14: 15.5, 16: 17.5, 20: 22, 24: 26, 30: 33, 36: 39, 42: 45, 48: 52}

# ISO 898-1 property classes for bolts, screws and studs (MPa).
# Rm = min tensile strength, Re = min lower yield ReL or 0.2% proof Rp0.2, Sp = proof load stress.
PROPERTY_CLASSES = {
    "4.6": {"Rm": 400, "Re": 240, "Sp": 225, "material": "Low/medium carbon steel"},
    "4.8": {"Rm": 420, "Re": 340, "Sp": 310, "material": "Low/medium carbon steel"},
    "5.6": {"Rm": 500, "Re": 300, "Sp": 280, "material": "Medium carbon steel"},
    "5.8": {"Rm": 520, "Re": 420, "Sp": 380, "material": "Low/medium carbon steel"},
    "6.8": {"Rm": 600, "Re": 480, "Sp": 440, "material": "Low/medium carbon steel"},
    "8.8": {"Rm": 800, "Re": 640, "Sp": 580, "material": "Medium carbon steel, quenched & tempered",
            "note": "d > 16 mm: Rm 830, Rp0.2 660, Sp 600"},
    "9.8": {"Rm": 900, "Re": 720, "Sp": 650, "material": "Medium carbon steel, Q&T (d ≤ 16 mm only)"},
    "10.9": {"Rm": 1040, "Re": 940, "Sp": 830, "material": "Alloy / boron steel, quenched & tempered"},
    "12.9": {"Rm": 1220, "Re": 1100, "Sp": 970, "material": "Alloy steel, quenched & tempered"},
}

# Typical nut factor K for T = K·F·d (indicative; always confirm with supplier/test)
NUT_FACTOR = {
    "dry_plain": 0.20, "zinc_plated": 0.20, "lightly_oiled": 0.18,
    "lubricated_mos2": 0.12, "ptfe_coated": 0.10, "hot_dip_galvanized": 0.25,
}


def thread_geometry(d: float, pitch: float | None = None) -> dict:
    """ISO metric thread dimensions. pitch=None → coarse pitch."""
    if pitch is None:
        if d not in COARSE_PITCH:
            raise ValueError(f"No standard coarse pitch for M{d}; give pitch explicitly. Known: {sorted(COARSE_PITCH)}")
        pitch = COARSE_PITCH[d]
    d2 = d - 0.649519 * pitch
    d3 = d - 1.226869 * pitch
    D1 = d - 1.082532 * pitch
    As = math.pi / 4 * ((d2 + d3) / 2) ** 2
    out = {
        "designation": f"M{d:g}" + ("" if pitch == COARSE_PITCH.get(d) else f"x{pitch:g}"),
        "nominal_d_mm": d, "pitch_mm": pitch,
        "series": "coarse" if pitch == COARSE_PITCH.get(d) else "fine",
        "pitch_diameter_d2_mm": round(d2, 3),
        "minor_diameter_external_d3_mm": round(d3, 3),
        "minor_diameter_internal_D1_mm": round(D1, 3),
        "tensile_stress_area_As_mm2": round(As, 2),
        "thread_depth_external_h3_mm": round(0.613435 * pitch, 3),
        "tap_drill_mm": round(d - pitch, 2),
        "lead_angle_deg": round(math.degrees(math.atan(pitch / (math.pi * d2))), 3),
    }
    if d in HEX_AF:
        out["hex_across_flats_mm"] = HEX_AF[d]
    if d in CLEARANCE_MEDIUM:
        out["clearance_hole_medium_mm"] = CLEARANCE_MEDIUM[d]
    if d in FINE_PITCH:
        out["available_fine_pitches_mm"] = FINE_PITCH[d]
    return out


def bolt_strength(d: float, property_class: str = "8.8", pitch: float | None = None) -> dict:
    """Proof load, yield load and minimum ultimate tensile load for a bolt."""
    pc = PROPERTY_CLASSES.get(property_class)
    if not pc:
        raise ValueError(f"Unknown property class {property_class}. Known: {list(PROPERTY_CLASSES)}")
    Rm, Re, Sp = pc["Rm"], pc["Re"], pc["Sp"]
    if property_class == "8.8" and d > 16:
        Rm, Re, Sp = 830, 660, 600
    g = thread_geometry(d, pitch)
    As = g["tensile_stress_area_As_mm2"]
    return {
        "bolt": f"{g['designation']} class {property_class}",
        "material": pc["material"],
        "Rm_MPa": Rm, "Re_MPa": Re, "proof_stress_Sp_MPa": Sp,
        "tensile_stress_area_mm2": As,
        "proof_load_kN": round(Sp * As / 1000, 2),
        "yield_load_kN": round(Re * As / 1000, 2),
        "min_ultimate_load_kN": round(Rm * As / 1000, 2),
        "reading_the_class": f"{property_class}: first number ×100 = Rm ≈ {int(property_class.split('.')[0]) * 100} MPa; "
                             f"second number ÷10 = yield/tensile ratio ≈ 0.{property_class.split('.')[1]}",
    }


def tightening_torque(d: float, property_class: str = "8.8", pitch: float | None = None,
                      preload_fraction: float = 0.75, mu_thread: float = 0.12, mu_head: float = 0.12,
                      nut_factor: float | None = None) -> dict:
    """
    Preload and assembly torque.
    - Preload: Fi = preload_fraction · Sp · As  (Shigley: 0.75 reusable, 0.90 permanent)
    - Torque (VDI 2230): T = Fi · (0.16·P + 0.58·μG·d2 + μK·Dkm/2), Dkm = (s + dh)/2
    - Also reported: short-form T = K·Fi·d
    """
    s = bolt_strength(d, property_class, pitch)
    g = thread_geometry(d, pitch)
    P, d2 = g["pitch_mm"], g["pitch_diameter_d2_mm"]
    Fi = preload_fraction * s["proof_stress_Sp_MPa"] * g["tensile_stress_area_As_mm2"]  # N
    out = {
        "bolt": s["bolt"], "preload_fraction_of_proof": preload_fraction,
        "preload_Fi_kN": round(Fi / 1000, 2),
    }
    if d in HEX_AF and d in CLEARANCE_MEDIUM:
        Dkm = (HEX_AF[d] + CLEARANCE_MEDIUM[d]) / 2
        T_vdi = Fi * (0.16 * P + 0.58 * mu_thread * d2 + mu_head * Dkm / 2) / 1000  # N·m
        out.update({
            "torque_VDI2230_Nm": round(T_vdi, 1),
            "assumptions": f"μ_thread={mu_thread}, μ_head={mu_head}, Dkm={Dkm:.2f} mm (hex head, medium clearance hole)",
            "torque_split": {
                "thread_pitch_%": round(100 * 0.16 * P / (0.16 * P + 0.58 * mu_thread * d2 + mu_head * Dkm / 2)),
                "thread_friction_%": round(100 * 0.58 * mu_thread * d2 / (0.16 * P + 0.58 * mu_thread * d2 + mu_head * Dkm / 2)),
                "head_friction_%": round(100 * mu_head * Dkm / 2 / (0.16 * P + 0.58 * mu_thread * d2 + mu_head * Dkm / 2)),
            },
        })
    K = nut_factor if nut_factor is not None else 0.2
    out["torque_short_form_Nm"] = round(K * Fi * d / 1000, 1)
    out["short_form_K"] = K
    out["warning"] = ("Indicative values. Friction scatter (±20-30%) dominates torque-controlled preload; "
                      "for critical joints follow VDI 2230 fully or the fastener supplier's torque chart.")
    return out


def bolt_joint_check(d: float, property_class: str, axial_load_kN: float = 0.0, shear_load_kN: float = 0.0,
                     n_bolts: int = 1, preload_fraction: float = 0.75, joint_stiffness_C: float = 0.25,
                     friction_coeff_interface: float = 0.2, n_shear_planes: int = 1) -> dict:
    """
    Simple bolted-joint check (Shigley approach):
      bolt load   Fb = Fi + C·P      (C = kb/(kb+km), joint stiffness constant)
      separation  n0 = Fi / (P·(1-C))
      yield       np = Sp·As / Fb
      slip        Fs_cap = μ·Fi·n_planes  vs shear per bolt
    """
    s = bolt_strength(d, property_class)
    As = s["tensile_stress_area_mm2"]
    Sp = s["proof_stress_Sp_MPa"]
    Fi = preload_fraction * Sp * As / 1000  # kN
    P = axial_load_kN / n_bolts
    V = shear_load_kN / n_bolts
    Fb = Fi + joint_stiffness_C * P
    res = {
        "bolt": s["bolt"], "n_bolts": n_bolts, "preload_per_bolt_kN": round(Fi, 2),
        "axial_load_per_bolt_kN": round(P, 3), "shear_load_per_bolt_kN": round(V, 3),
        "bolt_force_kN": round(Fb, 2),
        "proof_load_safety_factor": round(Sp * As / 1000 / Fb, 2) if Fb else None,
    }
    if P > 0:
        res["separation_safety_factor"] = round(Fi / (P * (1 - joint_stiffness_C)), 2)
    if V > 0:
        clamp = max(Fi - (1 - joint_stiffness_C) * P, 0)
        cap = friction_coeff_interface * clamp * n_shear_planes
        res["slip_resistance_per_bolt_kN"] = round(cap, 2)
        res["slip_safety_factor"] = round(cap / V, 2)
    res["assumptions"] = (f"C={joint_stiffness_C}, interface μ={friction_coeff_interface}, "
                          f"preload {preload_fraction:.0%} of proof load. Fatigue not checked.")
    return res
