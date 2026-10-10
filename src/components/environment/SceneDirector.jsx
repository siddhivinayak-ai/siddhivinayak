// SceneDirector.jsx
// Eases background, fog, rim light and floor tint toward the active scene,
// and runs a scene-specific particle system (sparks, bubbles, heat, chips, dust).

import { useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'
import { sceneOf } from '../../scenes'

const COUNT = 140

function spawn(type, p) {
  switch (type) {
    case 'sparks': {
      // Burst from a hidden "weld point" behind and to the right of the character
      const a = Math.random() * Math.PI * 2
      const s = 1.2 + Math.random() * 2.2
      return { x: 1.6, y: 0.9, z: -1.4, vx: Math.cos(a) * s * 0.6, vy: 1 + Math.random() * 2.4, vz: Math.sin(a) * s * 0.4, life: 0.5 + Math.random() * 0.8, g: -6, size: 0.012 }
    }
    case 'bubbles':
      return { x: (Math.random() - 0.5) * 9, y: -0.1, z: -1.5 - Math.random() * 5, vx: 0, vy: 0.25 + Math.random() * 0.35, vz: 0, life: 6 + Math.random() * 6, g: 0, size: 0.02 + Math.random() * 0.04, wobble: 1 }
    case 'heat':
      return { x: (Math.random() - 0.5) * 8, y: 0, z: -1 - Math.random() * 5, vx: 0, vy: 0.35 + Math.random() * 0.4, vz: 0, life: 3 + Math.random() * 3, g: 0, size: 0.03 + Math.random() * 0.03, wobble: 2 }
    case 'chips':
      return { x: (Math.random() - 0.5) * 9, y: 3 + Math.random() * 1.5, z: -1 - Math.random() * 5, vx: (Math.random() - 0.5) * 0.3, vy: -0.4 - Math.random() * 0.4, vz: 0, life: 7 + Math.random() * 3, g: 0, size: 0.018 + Math.random() * 0.02, spin: 1 }
    default: {
      // Keep dust behind the character so nothing drifts in front of the camera
      return { x: (Math.random() - 0.5) * 12, y: 0.3 + Math.random() * 2.4, z: -1.5 - Math.random() * 6, vx: 0, vy: 0.02, vz: 0, life: 8 + Math.random() * 8, g: 0, size: 0.015 + Math.random() * 0.01, wobble: 0.3, phase: p }
  }
  }
}

function SceneParticles({ type, color }) {
  const meshRef = useRef()
  const matRef = useRef()
  const dummy = useMemo(() => new THREE.Object3D(), [])
  const parts = useMemo(() => Array.from({ length: COUNT }, () => ({ age: Infinity, life: 0 })), [])
  const typeRef = useRef(type)
  typeRef.current = type
  const target = useMemo(() => new THREE.Color(), [])

  useFrame(({ clock }, dt) => {
    const mesh = meshRef.current
    if (!mesh) return
    dt = Math.min(dt, 0.05)
    const t = clock.getElapsedTime()
    const kind = typeRef.current
    const active = kind === 'sparks' ? COUNT : kind === 'dust' ? 30 : 70
    // Sparks come in short bursts like a real arc being struck
    const burst = kind !== 'sparks' || Math.sin(t * 1.3) + Math.sin(t * 3.1) > 0.2

    for (let i = 0; i < COUNT; i++) {
      const p = parts[i]
      p.age += dt
      if (p.age > p.life) {
        if (i < active && burst) Object.assign(p, spawn(kind, i), { age: 0 })
        else { p.life = 0; p.age = Infinity }
      }
      if (p.age === Infinity) {
        dummy.scale.setScalar(0)
      } else {
        p.vy += (p.g || 0) * dt
        p.x += p.vx * dt + (p.wobble ? Math.sin(t * 1.5 + i) * 0.002 * p.wobble : 0)
        p.y += p.vy * dt
        p.z += p.vz * dt
        if (kind === 'sparks' && p.y < 0.06) { p.y = 0.06; p.vy *= -0.3; p.vx *= 0.6 }
        const fade = Math.min(1, p.age * 4) * Math.max(0, 1 - p.age / p.life)
        dummy.position.set(p.x, p.y, p.z)
        dummy.scale.setScalar(p.size * (0.4 + fade))
        if (p.spin) dummy.rotation.set(t * 2 + i, t * 3 + i, 0)
      }
      dummy.updateMatrix()
      mesh.setMatrixAt(i, dummy.matrix)
    }
    mesh.instanceMatrix.needsUpdate = true
    target.set(color)
    matRef.current.color.lerp(target, 0.05)
    matRef.current.opacity = THREE.MathUtils.lerp(matRef.current.opacity, kind === 'dust' ? 0.25 : 0.85, 0.05)
  })

  return (
    <instancedMesh ref={meshRef} args={[null, null, COUNT]} frustumCulled={false}>
      {type === 'chips' ? <tetrahedronGeometry args={[1, 0]} /> : <sphereGeometry args={[1, 6, 6]} />}
      <meshBasicMaterial
        ref={matRef}
        color={color}
        transparent
        opacity={0.25}
        depthWrite={false}
        blending={type === 'sparks' || type === 'heat' ? THREE.AdditiveBlending : THREE.NormalBlending}
        toneMapped={false}
      />
    </instancedMesh>
  )
}

export default function SceneDirector({ sceneId = 'studio' }) {
  const s = sceneOf(sceneId)
  const { scene } = useThree()
  const rimRef = useRef()
  const flickerRef = useRef()
  const gridRef = useRef()
  const tmp = useMemo(() => new THREE.Color(), [])

  useMemo(() => {
    if (!(scene.background instanceof THREE.Color)) scene.background = new THREE.Color(s.bg)
    if (!scene.fog) scene.fog = new THREE.Fog(s.fog, 12, 35)
  }, [scene]) // eslint-disable-line react-hooks/exhaustive-deps

  useFrame(({ clock }) => {
    const k = 0.035
    scene.background.lerp(tmp.set(s.bg), k)
    scene.fog.color.lerp(tmp.set(s.fog), k)
    if (rimRef.current) rimRef.current.color.lerp(tmp.set(s.rim), k)
    // Welding arc flicker: a warm point light that pulses with the spark bursts
    if (flickerRef.current) {
      const t = clock.getElapsedTime()
      const want = sceneId === 'welding' ? 2.5 + Math.random() * 3 * (Math.sin(t * 1.3) + Math.sin(t * 3.1) > 0.2 ? 1 : 0.1) : 0
      flickerRef.current.intensity = THREE.MathUtils.lerp(flickerRef.current.intensity, want, 0.3)
    }
    if (gridRef.current) {
      const m = gridRef.current.material
      m.opacity = THREE.MathUtils.lerp(m.opacity, s.grid ? 0.35 : 0, 0.04)
      gridRef.current.visible = m.opacity > 0.01
    }
  })

  return (
    <>
      <pointLight ref={rimRef} color={s.rim} intensity={3.2} position={[-2.5, 2.6, -2.6]} distance={10} decay={2} />
      <pointLight ref={flickerRef} color="#FFB060" intensity={0} position={[1.6, 1.0, -1.2]} distance={6} decay={2} />
      <gridHelper ref={gridRef} args={[30, 60, '#4C7BE0', '#8FAAE6']} position={[0, -0.05, 0]}
        material-transparent material-opacity={0} material-depthWrite={false} />
      <SceneParticles type={s.particles} color={s.particleColor} />
    </>
  )
}
