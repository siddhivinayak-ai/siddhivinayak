# Welding Reference

Sources summarised: ISO 4063 (process numbers), ISO 2553 / AWS A2.4 (weld symbols), ISO 6947 (welding positions), AWS A3.0 (terms), AWS A5.1/A5.18/A5.20 (consumables), EN 1011-1/-2 (heat input, preheat), ISO 15614 / ASME IX (procedure qualification), ISO 9606 (welder qualification), ISO 5817 (quality levels B/C/D), AWS D1.1 (structural steel).

## Classification of welding processes
- Fusion welding: base metal melts. Arc (SMAW, GMAW, FCAW, GTAW, SAW, PAW), gas (oxy-fuel), high-energy beam (laser, electron beam), electroslag, thermit.
- Solid-state welding: no melting of base metal. Friction, friction stir, ultrasonic, diffusion, explosive, forge, cold pressure welding.
- Resistance welding: heat from I²R at the interface plus pressure. Spot, seam, projection, flash, upset.
- Brazing (filler above 450 °C) and soldering (below 450 °C): base metal does not melt; joint by capillary action.

## Arc welding processes
- SMAW / MMA (ISO 111): consumable flux-coated stick electrode. Cheap, portable, all positions, works outdoors. Low deposition rate, slag removal, frequent stops.
- GMAW (MIG 131 / MAG 135): continuous solid wire, shielding gas. High productivity, easy to automate. Short-circuit, globular, spray and pulsed transfer modes. Sensitive to wind.
- FCAW (136 gas-shielded, 114 self-shielded): tubular wire with flux core. High deposition, good positional welding, good on dirty steel.
- GTAW / TIG (141): non-consumable tungsten electrode, inert gas, separate filler. Highest quality, precise, thin material, root passes, stainless, aluminium (AC for Al to break oxide), titanium. Slow.
- SAW (121): arc buried under granular flux. Very high deposition and deep penetration, no visible arc. Flat/horizontal only. Pressure vessels, pipes, ship panels.
- PAW (15): constricted arc, keyhole mode. Deep, narrow welds with good control.
- Electroslag (72) / electrogas: thick vertical sections in a single pass.

## Polarity
- DCEP (DC electrode positive, reverse polarity): standard for GMAW and low-hydrogen SMAW electrodes; stable spray transfer, good penetration and cathodic cleaning of oxides. In GTAW, DCEP overheats the tungsten, so it is rarely used there.
- DCEN (straight polarity): ~70% heat into the work in GTAW, so TIG of steel uses DCEN. Tungsten stays cool.
- AC: used for TIG of aluminium/magnesium (oxide cleaning on the EP half cycle) and to reduce arc blow.

## Metal transfer in GMAW
- Short-circuit (dip): low current/voltage, thin sheet, all positions, risk of lack of fusion.
- Globular: intermediate current, spatter, mostly CO2 shielding.
- Spray: high current above transition current, argon-rich gas (>80% Ar), flat/horizontal, smooth, deep fusion.
- Pulsed spray: spray-like transfer at lower average current, all positions, less heat.

## Shielding gases
- Argon: inert, stable arc, TIG and MIG of non-ferrous. Helium: hotter arc, faster on thick Al/Cu.
- CO2: cheap, deep penetration, more spatter (MAG of steel). Ar + 8–20% CO2: standard MAG mix for carbon steel. Ar + 2% O2 or 2% CO2: stainless spray transfer.

## Resistance and solid-state processes
- Spot welding: heat Q = I²·R·t. Parameters: current, weld time, electrode force, electrode tip diameter. Typical car body has 3000–5000 spot welds.
- Friction welding: rotating part pressed against stationary part; flash formed; great for dissimilar metals (e.g. Al–steel).
- Friction stir welding: non-consumable rotating tool with pin and shoulder; solid-state joining of aluminium alloys including non-weldable 2xxx/7xxx series; low distortion, no porosity.
- Laser beam welding: keyhole mode, high power density, low heat input, narrow HAZ; needs tight fit-up.
- Electron beam: in vacuum, very deep narrow welds (depth/width up to 20+).

## Heat input and metallurgy
- Arc energy E (kJ/mm) = U·I·60 / (v·1000), v in mm/min. Heat input Q = k·E.
- Thermal efficiency k (EN 1011-1): SAW 1.0; SMAW, MIG/MAG, FCAW 0.8; TIG and plasma 0.6.
- Weld zones: fusion zone (cast structure), heat-affected zone (HAZ: coarse-grain, fine-grain, intercritical, subcritical), unaffected base metal.
- Cooling time t8/5 (800 → 500 °C) controls HAZ hardness and toughness in steels.
- Carbon equivalent (IIW): CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15. Higher CE → harder HAZ, more cold-cracking risk → preheat.
- Hydrogen (cold) cracking needs: hydrogen + susceptible (hard, martensitic) microstructure + tensile stress. Control with low-hydrogen consumables (H4/H5), preheat, interpass control and post-heat.
- Hot (solidification) cracking: low-melting segregates (S, P), high depth/width ratio beads. Control with lower heat input, good bead shape, Mn:S ratio.
- Lamellar tearing: through-thickness strain on rolled plate with inclusions; use Z-quality steel.
- Stainless: austenitic grades need ferrite number ~3–10 to avoid hot cracking; use low-carbon (L) grades or stabilised grades to avoid sensitisation (chromium carbide at 450–850 °C).
- Aluminium: high thermal conductivity, oxide layer (melting point ~2050 °C vs ~660 °C metal), hydrogen porosity, HAZ softening in heat-treatable alloys.

## Weld defects (ISO 6520-1 groups)
- Cracks: longitudinal, transverse, crater, hydrogen, hot, lamellar.
- Porosity: gas pores from moisture, contamination, loss of shielding, wind.
- Solid inclusions: slag, tungsten inclusions (TIG electrode touching the pool).
- Lack of fusion / incomplete penetration: low heat, wrong angle, high travel speed.
- Shape defects: undercut (high current/voltage), overlap, excessive reinforcement, misalignment, spatter, arc strikes.
- Distortion: longitudinal and transverse shrinkage, angular distortion. Control: balanced welding sequence, back-step, presetting, clamping, minimal weld volume.

## Inspection (NDT)
- VT visual (ISO 17637) – always first. PT dye penetrant – surface cracks. MT magnetic particle – surface/near-surface in ferromagnetic steel. UT ultrasonic (incl. PAUT, TOFD) – volumetric, planar defects. RT radiography – volumetric, porosity and slag. Destructive tests: bend, tensile, macro-etch, Charpy impact, hardness.
- Quality levels per ISO 5817: B (stringent), C (intermediate), D (moderate).

## Weld joints and symbols
- Joint types: butt, tee, lap, corner, edge.
- Weld types: fillet, groove (square, single/double V, bevel, U, J), plug/slot, spot, seam, stud.
- Symbol arrow side vs other side: in AWS A2.4, the weld symbol below the reference line is arrow side; above is other side. ISO 2553 uses a continuous line plus a dashed identification line.
- Fillet size: AWS gives leg length; ISO uses "a" (throat) or "z" (leg) prefix. Throat a = 0.707 × leg for equal-leg fillets.
- Supplementary symbols: weld-all-around circle, field-weld flag, contour (flush/convex/concave).

## Welding positions
- ISO 6947 / AWS: PA = 1G/1F flat; PB = 2F horizontal fillet; PC = 2G horizontal; PF = 3G vertical up; PG = 3G vertical down; PE = 4G overhead; PD = 4F overhead fillet. Pipe: 5G (horizontal fixed), 6G (45° fixed, qualifies all positions).

## Consumable designations
- AWS A5.1 SMAW: E7018 = E (electrode), 70 (70 ksi min tensile), 1 (all positions), 8 (low-hydrogen potassium + iron powder, AC/DCEP).
- E6010: cellulosic, deep penetrating, DCEP, pipeline root passes. E6013: rutile, easy to use, light-duty sheet metal. E7024: iron powder, high deposition flat/horizontal fillets.
- AWS A5.18 GMAW wire: ER70S-6 (higher Mn/Si deoxidisers, tolerates mill scale). ER = electrode or rod.
- ISO 2560: e.g. E 42 3 B 32 H5 (yield 420 MPa, impact at −30 °C, basic coating, H5 hydrogen).

## Qualification
- WPS (welding procedure specification) is supported by a PQR/WPQR (procedure qualification record) per ISO 15614-1 or ASME IX. Welders qualified per ISO 9606-1 or ASME IX / AWS D1.1.
- Essential variables (change requires requalification) include base material group, process, thickness range, filler, preheat, PWHT, heat input (when impact tested).

## Safety
- Arc radiation (UV/IR): shade 10–13 filter. Fumes: hexavalent chromium from stainless, manganese, zinc (galvanised: metal fume fever) – use LEV/extraction. Electric shock, fire (hot work permit), compressed gas cylinders secured upright, confined space ventilation.
