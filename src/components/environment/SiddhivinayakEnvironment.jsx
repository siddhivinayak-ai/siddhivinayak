// SiddhivinayakEnvironment.jsx
// Main composition — no drei Environment preset (avoids black HDR panels).
// Usage:
//   <Canvas>
//     <SiddhivinayakEnvironment />
//     <SiddhivinayakCharacter />   ← later
//   </Canvas>

import StudioFloor        from './StudioFloor'
import CentralPlatform    from './CentralPlatform'
import AmbientRings       from './AmbientRings'
import EnvironmentLights  from './EnvironmentLights'
import Atmosphere         from './Atmosphere'

export default function SiddhivinayakEnvironment() {
  return (
    <group>
      <EnvironmentLights />
      <StudioFloor />
      <CentralPlatform />
      <AmbientRings />
      <Atmosphere />
    </group>
  )
}
