// AmbientRings.jsx
// Flat concentric rings around the central platform.
// These look like the barely-visible elliptical lines in the reference image —
// like precision engineering layers on the floor, NOT sci-fi rings.

import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'

function Ring({ radius, tubeRadius, baseOpacity, color, phaseOffset, speed }) {
  const ref = useRef()

  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    ref.current.material.opacity =
      baseOpacity + Math.sin(t * speed + phaseOffset) * (baseOpacity * 0.25)
  })

  return (
    // rotation=[-PI/2,0,0] lays the torus flat in the XZ plane
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]}>
      <torusGeometry args={[radius, tubeRadius, 4, 160]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={baseOpacity}
        depthWrite={false}
      />
    </mesh>
  )
}

export default function AmbientRings() {
  return (
    <group>
      {/* Ring 1 — just outside platform */}
      <Ring radius={2.42} tubeRadius={0.006} baseOpacity={0.22} color="#A4BEE0" phaseOffset={0.0} speed={0.40} />
      {/* Ring 2 — mid distance */}
      <Ring radius={3.05} tubeRadius={0.004} baseOpacity={0.12} color="#AECAE8" phaseOffset={1.4} speed={0.30} />
      {/* Ring 3 — outer, barely visible */}
      <Ring radius={3.9}  tubeRadius={0.003} baseOpacity={0.07} color="#C0D4F0" phaseOffset={2.8} speed={0.22} />
    </group>
  )
}
