// Atmosphere.jsx — simplified, no custom shader class
// Radial glow via a sprite-like plane with meshBasicMaterial (transparent)
// + slow-drifting instanced particles + animated point light.

import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

// ── Animated blue atmospheric point light ──
function AtmosphericLight() {
  const ref = useRef()
  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    ref.current.intensity = 1.6 + Math.sin(t * 0.38) * 0.45
    ref.current.position.x = Math.sin(t * 0.22) * 1.8
    ref.current.position.z = -6 + Math.cos(t * 0.18) * 0.8
  })
  return (
    <pointLight
      ref={ref}
      color="#6AAAEE"
      intensity={1.6}
      position={[0, 3, -6]}
      distance={18}
      decay={2}
    />
  )
}

// ── Soft radial glow disc in background ──
// We use a circle geometry with vertex colors fading from center (blue) to edge (transparent)
function BackdropGlow() {
  const matRef = useRef()
  useFrame(({ clock }) => {
    if (matRef.current) {
      const t = clock.getElapsedTime()
      matRef.current.opacity = 0.22 + Math.sin(t * 0.33) * 0.07
    }
  })

  // Build a circle with vertex colors fading radially
  const geometry = useMemo(() => {
    const segments = 64
    const geo = new THREE.CircleGeometry(7, segments)
    const colors = []
    const posArr = geo.attributes.position.array

    for (let i = 0; i < posArr.length / 3; i++) {
      const x = posArr[i * 3]
      const y = posArr[i * 3 + 1]
      const dist = Math.sqrt(x * x + y * y) / 7
      const alpha = Math.max(0, 1 - dist)
      // Blend from sky-blue center to edge (edge will be same but alpha handled in material)
      colors.push(0.7 + alpha * 0.3, 0.82 + alpha * 0.18, 1.0)
    }
    geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
    return geo
  }, [])

  return (
    <mesh position={[0, 2.0, -10]} geometry={geometry}>
      <meshBasicMaterial
        ref={matRef}
        vertexColors
        transparent
        opacity={0.22}
        depthWrite={false}
        side={THREE.FrontSide}
      />
    </mesh>
  )
}

// ── Floating particles (instanced) ──
const COUNT = 20

function FloatingParticles() {
  const meshRef = useRef()
  const dummy = useMemo(() => new THREE.Object3D(), [])

  const data = useMemo(() => {
    const pos = [], phases = [], spd = []
    for (let i = 0; i < COUNT; i++) {
      const angle = Math.random() * Math.PI * 2
      const r = 4.0 + Math.random() * 4.5
      pos.push(Math.cos(angle) * r, 0.3 + Math.random() * 2.0, Math.sin(angle) * r - 1.5)
      phases.push(Math.random() * Math.PI * 2)
      spd.push(0.10 + Math.random() * 0.15)
    }
    return { pos, phases, spd }
  }, [])

  useFrame(({ clock }) => {
    const mesh = meshRef.current
    if (!mesh) return
    const t = clock.getElapsedTime()
    for (let i = 0; i < COUNT; i++) {
      dummy.position.set(
        data.pos[i * 3],
        data.pos[i * 3 + 1] + Math.sin(t * data.spd[i] + data.phases[i]) * 0.10,
        data.pos[i * 3 + 2]
      )
      dummy.scale.setScalar(0.018 + Math.sin(t * 0.28 + data.phases[i]) * 0.005)
      dummy.updateMatrix()
      mesh.setMatrixAt(i, dummy.matrix)
    }
    mesh.instanceMatrix.needsUpdate = true
  })

  return (
    <instancedMesh ref={meshRef} args={[null, null, COUNT]}>
      <sphereGeometry args={[1, 4, 4]} />
      <meshBasicMaterial color="#A4C0E0" transparent opacity={0.15} depthWrite={false} />
    </instancedMesh>
  )
}

export default function Atmosphere() {
  return (
    <group>
      <BackdropGlow />
      <AtmosphericLight />
      <FloatingParticles />
    </group>
  )
}
