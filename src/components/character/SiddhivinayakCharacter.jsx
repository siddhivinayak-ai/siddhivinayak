// SiddhivinayakCharacter.jsx
//
// Mixamo boy character with breathing idle animation, high-res texture,
// and soft contact shadow on the platform.

import { useEffect, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { useGLTF, useTexture, useAnimations } from '@react-three/drei'
import * as THREE from 'three'

useGLTF.preload('/character/BreathingIdle.glb')
useTexture.preload('/character/Texture.png')

export default function SiddhivinayakCharacter({
  position = [0, 0.052, 0.0],
  scale = 1.22,
  voiceVolume = 0,
  thinking = false
}) {
  const groupRef = useRef()
  const characterRef = useRef()
  const headRef = useRef()
  const spineRef = useRef()
  const jawRef = useRef()

  const { scene, animations } = useGLTF('/character/BreathingIdle.glb')
  const { actions, names } = useAnimations(animations, characterRef)

  const texture = useTexture('/character/Texture.png')
  texture.flipY = false
  texture.colorSpace = THREE.SRGBColorSpace

  useEffect(() => {
    scene.traverse((obj) => {
      if (obj.isMesh) {
        obj.castShadow = true
        obj.receiveShadow = true

        if (obj.material) {
          obj.material.map = texture
          obj.material.color.set('#ffffff')
          obj.material.roughness = 0.58
          obj.material.metalness = 0.04
          obj.material.needsUpdate = true
        }
      }
      
      // Find neck/head, spine, and jaw bones
      if (obj.isBone) {
        const n = obj.name.toLowerCase()
        if (n.includes('neck') || obj.name === 'mixamorigHead') {
          headRef.current = obj
        }
        if (n.includes('spine2') || obj.name === 'mixamorigSpine2') {
          spineRef.current = obj
        }
        // Jaw bone for lip-sync animation
        if (n.includes('jaw') || obj.name === 'mixamorigJaw') {
          jawRef.current = obj
        }
      }
    })
  }, [scene, texture])

  useEffect(() => {
    if (names && names.length > 0) {
      const action = actions[names[0]]
      if (action) {
        action.reset().fadeIn(0.5).play()
      }
    }
  }, [actions, names])

  // Subtly rotate head and spine towards mouse cursor
  useFrame((state) => {
    // state.pointer holds normalized mouse coords (-1 to 1)
    let targetX = (state.pointer.x * Math.PI) / 5
    let targetY = (state.pointer.y * Math.PI) / 8

    if (thinking) {
      // Glance up and to the side while the brain works, with a slow drift
      const t = state.clock.getElapsedTime()
      targetX = -0.32 + Math.sin(t * 0.9) * 0.06
      targetY = 0.22 + Math.sin(t * 0.6) * 0.03
    } else if (voiceVolume > 0.02) {
      // While speaking, look at the viewer with small emphasis nods
      const t = state.clock.getElapsedTime()
      targetX = targetX * 0.3
      targetY = -0.04 + Math.sin(t * 7) * voiceVolume * 0.06
    }

    if (headRef.current) {
      // For Mixamo rigs, rotating Y and X on the neck usually turns the head. 
      // The exact axes can vary, but this is typical for standard Mixamo exports.
      headRef.current.rotation.y = THREE.MathUtils.lerp(headRef.current.rotation.y, -targetX, 0.08)
      headRef.current.rotation.x = THREE.MathUtils.lerp(headRef.current.rotation.x, targetY, 0.08)
    }
    if (spineRef.current) {
      spineRef.current.rotation.y = THREE.MathUtils.lerp(spineRef.current.rotation.y, -targetX * 0.4, 0.08)
      spineRef.current.rotation.x = THREE.MathUtils.lerp(spineRef.current.rotation.x, targetY * 0.4, 0.08)
    }

    // Jaw / mouth animation driven by voice volume
    if (jawRef.current) {
      // Open jaw proportional to voice volume (clamped, smooth)
      const jawOpen = voiceVolume * 0.35  // max ~20 degrees of rotation
      jawRef.current.rotation.x = THREE.MathUtils.lerp(
        jawRef.current.rotation.x,
        jawOpen,
        0.25 // faster lerp for snappy lip sync feel
      )
    } else if (headRef.current && voiceVolume > 0) {
      // Fallback: if no jaw bone, subtly scale the head Y to simulate talking
      const headNod = 1 + voiceVolume * 0.012
      headRef.current.scale.y = THREE.MathUtils.lerp(
        headRef.current.scale.y || 1,
        headNod,
        0.2
      )
    }
  })

  return (
    <group ref={groupRef} position={position}>
      {/* ── Soft contact shadow beneath character's feet on the platform ── */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.001, 0.02]}>
        <ringGeometry args={[0, 0.55, 32]} />
        <meshBasicMaterial
          color="#657e9f"
          transparent
          opacity={0.32}
          depthWrite={false}
        />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.001, 0.02]}>
        <ringGeometry args={[0, 0.32, 32]} />
        <meshBasicMaterial
          color="#425570"
          transparent
          opacity={0.28}
          depthWrite={false}
        />
      </mesh>

      {/* ── Character model ── */}
      <group ref={characterRef} scale={[scale, scale, scale]}>
        <primitive object={scene} />
      </group>
    </group>
  )
}
