# Fasteners Reference (Screws, Bolts, Nuts)

Sources summarised: ISO 68-1, ISO 261/262/724 (metric threads), ISO 898-1 (bolt property classes), ISO 898-2 (nuts), ISO 4014/4017 (hex bolts/screws), ISO 4032 (hex nuts), ISO 4762 (socket head cap screws), ISO 273 (clearance holes), ISO 7089 (washers), VDI 2230 (bolted joint design), ASME B1.1 (Unified inch threads).

## Thread terminology
- Major diameter d: the largest diameter of the thread; this is the nominal size (M10 → d = 10 mm).
- Pitch P: axial distance between adjacent threads. Lead = P × number of starts.
- Pitch diameter d2 = d − 0.6495·P: where thread thickness equals groove width; governs fit.
- Minor diameter d3 = d − 1.2269·P (external); D1 = d − 1.0825·P (internal).
- Flank angle: 60° for ISO metric and Unified; 55° for Whitworth (BSW/BSP); 29° for ACME; 30° for metric trapezoidal (Tr).
- Tensile stress area As = π/4·((d2+d3)/2)². Use As, not the nominal area, for bolt stress.
- Tap drill size ≈ d − P for metric coarse threads (gives ~75% thread engagement).

## Coarse vs fine threads
- Coarse (ISO 261 first choice): faster assembly, less cross-threading, more tolerant of dirt/damage, better in soft materials (aluminium, cast iron).
- Fine: larger As (stronger for the same d), finer adjustment, better vibration resistance due to smaller lead angle, thinner walls possible. More prone to galling and cross-threading.
- Common coarse pitches: M3×0.5, M4×0.7, M5×0.8, M6×1, M8×1.25, M10×1.5, M12×1.75, M16×2, M20×2.5, M24×3, M30×3.5.

## Thread tolerance classes
- ISO 965: 6g (external) / 6H (internal) is the general-purpose fit. 4h/5H fine; 8g/7H coarse.
- Lower-case letters = external threads (bolts); upper-case = internal threads (nuts).

## Bolt property classes (ISO 898-1)
- Marking X.Y: X × 100 = nominal tensile strength Rm (MPa); Y/10 = ratio of yield to tensile strength.
- 4.6: Rm 400, Re 240 MPa (mild steel, general low-load use).
- 8.8: Rm 800, Rp0.2 640 MPa (d ≤ 16) – the general engineering default, quenched & tempered medium carbon steel.
- 10.9: Rm 1040, Rp0.2 940 MPa – high strength structural (HSFG), automotive.
- 12.9: Rm 1220, Rp0.2 1100 MPa – socket head cap screws, high-stress machinery. Sensitive to hydrogen embrittlement: avoid electroplating without baking.
- Nuts (ISO 898-2): class 8 nut with 8.8 bolt, 10 with 10.9, 12 with 12.9. The nut should be stronger than the bolt so the bolt fails by fracture, not thread stripping.
- Stainless (ISO 3506): A2-70 (304), A4-80 (316). Number = Rm/10 (70 → 700 MPa). Lower strength than 8.8 in yield; gall easily – use anti-seize.

## Inch fasteners (SAE J429)
- Grade 2: low carbon, ~74 ksi. Grade 5: medium carbon Q&T, 120 ksi (3 radial lines on head). Grade 8: alloy Q&T, 150 ksi (6 radial lines).
- UNC = coarse, UNF = fine; designated like 1/2-13 UNC-2A (2A external / 2B internal class).

## Preload and tightening
- Joint works by clamp force (preload). Typical target preload Fi = 0.75 × proof load (reusable) or 0.90 × proof load (permanent).
- Short-form torque: T = K·F·d, K ≈ 0.2 dry steel, 0.15–0.18 lightly oiled, ≈0.12 with MoS2 paste.
- VDI 2230 torque: T = F·(0.16·P + 0.58·μG·d2 + μK·Dkm/2). Roughly 10% of torque goes into stretching the bolt; ~40% into thread friction and ~50% into head/nut friction.
- Tightening methods by preload scatter: torque wrench ±25%; angle-controlled (turn-of-nut) ±10%; yield-controlled ±8%; ultrasonic/bolt elongation measurement ±3–5%; hydraulic tensioning best for large bolts.

## Joint behaviour
- Joint stiffness constant C = kb/(kb+km); typically 0.15–0.35 for steel joints. Only fraction C of an external axial load adds to bolt force: Fb = Fi + C·P.
- Separation occurs when external load P reaches Fi/(1−C).
- Slip-critical (friction) joints carry shear by friction μ·Fi per plane. Bearing-type joints carry shear through the bolt shank.
- Fatigue: thread root is the critical location; rolled threads (after heat treatment) are better than cut threads. High preload greatly reduces stress amplitude.

## Locking methods
- Prestress (preload) is the primary locking method. Self-loosening is caused by transverse slip (Junker test, DIN 65151).
- Effective: wedge-locking washers (Nord-Lock type), prevailing-torque nuts (nylon insert ISO 7040, all-metal ISO 7042), anaerobic thread lockers (e.g. medium-strength blue, high-strength red), safety wire, castellated nut + split pin.
- Largely ineffective against vibration: plain spring (split) washers and serrated washers on hard surfaces (withdrawn from many standards, e.g. DIN 127 withdrawn).

## Screw types
- Machine screws: into tapped hole or nut. Cap screws: ISO 4762 socket head, ISO 4017 hex head fully threaded.
- Set screws (grub screws, ISO 4026–4029): flat, cone, dog and cup points; transmit small torque to shafts.
- Self-tapping screws (ISO 1481/7049): form threads in sheet metal. Thread-forming screws for plastics (e.g. 30° flank profiles).
- Self-drilling (Tek) screws: drill point + thread in one operation.
- Wood screws, lag screws: tapered, coarse threads.
- Studs: threaded both ends; used where frequent disassembly would wear a tapped hole.
- Power screws: square, ACME (29°) and trapezoidal (30°) threads for motion transmission; ball screws for high efficiency (>90%).

## Power screw formulas
- Raise load (square thread): T = F·dm/2 · (l + π·μ·dm)/(π·dm − μ·l) + collar friction F·μc·dc/2.
- Self-locking condition: μ > tan λ (lead angle λ), i.e. π·μ·dm > l.
- Efficiency e = F·l / (2π·T). Self-locking screws have efficiency below 50%.

## Common failure modes
- Loosening from transverse vibration (insufficient preload).
- Fatigue fracture at first engaged thread or thread run-out.
- Thread stripping (insufficient engagement length: aim ≥ 1×d in steel, 1.5×d in cast iron, 2×d in aluminium).
- Hydrogen embrittlement (≥10.9 and plated parts) – delayed fracture under preload.
- Galling (stainless on stainless) – use anti-seize, different alloys or coatings.
- Corrosion: galvanic coupling between stainless fasteners and aluminium/zinc parts.
