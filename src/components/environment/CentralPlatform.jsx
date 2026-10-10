// CentralPlatform.jsx
// Wide circular platform — pure white satin finish, smooth bevel, soft contact shadow.
// Top surface receives shadows from character.

import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'

export default function CentralPlatform() {
  const topRef = useRef()

  // Extremely subtle emissive breathing
  useFrame(({ clock }) => {
    if (topRef.current) {
      const t = clock.getElapsedTime()
      topRef.current.material.emissiveIntensity = 0.04 + Math.sin(t * 0.55) * 0.02
    }
  })

  return (
    <group position={[0, 0, 0]}>
      {/* ── Main platform cylinder body ── */}
      <mesh ref={topRef} castShadow receiveShadow position={[0, 0, 0]}>
        <cylinderGeometry args={[2.22, 2.26, 0.10, 128, 1]} />
        <meshStandardMaterial
          color="#FAFBFC"
          roughness={0.4}
          metalness={0.0}
          emissive="#DAEEFF"
          emissiveIntensity={0.04}
        />
      </mesh>

      {/* ── Top-face surface — receives character shadows ── */}
      <mesh position={[0, 0.051, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[2.2, 128]} />
        <meshStandardMaterial
          color="#FFFFFF"
          roughness={0.3}
          metalness={0.0}
        />
      </mesh>

      {/* ── Bevel ring on top edge (flat torus) ── */}
      <mesh position={[0, 0.052, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <torusGeometry args={[2.21, 0.012, 10, 128]} />
        <meshStandardMaterial color="#E2ECF8" roughness={0.25} metalness={0.0} />
      </mesh>

      {/* ── Soft contact shadow on the floor beneath platform ── */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.052, 0]}>
        <circleGeometry args={[2.85, 64]} />
        <meshBasicMaterial
          color="#9BB8DD"
          transparent
          opacity={0.12}
          depthWrite={false}
        />
      </mesh>

      {/* ── Outer soft floor glow ── */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.053, 0]}>
        <circleGeometry args={[3.8, 64]} />
        <meshBasicMaterial
          color="#BACEE8"
          transparent
          opacity={0.06}
          depthWrite={false}
        />
      </mesh>
    </group>
  )
}
