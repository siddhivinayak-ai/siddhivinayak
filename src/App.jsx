import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { Suspense, useState, useCallback } from 'react'
import { SiddhivinayakEnvironment } from './components/environment'
import SceneDirector from './components/environment/SceneDirector'
import SiddhivinayakCharacter from './components/character/SiddhivinayakCharacter'
import InterfaceOverlay from './components/ui/InterfaceOverlay'
import useBrain from './hooks/useBrain'

export default function App() {
  const [voiceVolume, setVoiceVolume] = useState(0)
  const brain = useBrain()

  const handleVolumeChange = useCallback((v) => {
    setVoiceVolume(v)
  }, [])

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', overflow: 'hidden' }}>
      {/* 2D UI Overlay (Logo, Voice Orb, Radial Tool Orbit, Chat) */}
      <InterfaceOverlay brain={brain} onVolumeChange={handleVolumeChange} />

      {/* 3D Canvas with exact front-facing studio perspective */}
      <div className="stage-canvas">
      <Canvas
        shadows="soft"
        // Camera positioned at straight eye-level (y=1.05), perfectly framing the character
        camera={{ position: [0, 0.95, 6.4], fov: 36, near: 0.1, far: 80 }}
        gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      >
        {/* Background, fog, rim light and particles follow the conversation topic */}
        <SceneDirector sceneId={brain.scene} />

        <Suspense fallback={null}>
          <SiddhivinayakEnvironment />
          {/* Character standing proudly in the center at y=0.052 */}
          <SiddhivinayakCharacter
            position={[0, 0.052, 0]}
            scale={1.22}
            voiceVolume={voiceVolume}
            thinking={brain.thinking}
          />
        </Suspense>

        {/* OrbitControls: autoRotate is OFF so it defaults to the exact front view */}
        <OrbitControls
          enablePan={false}
          enableZoom={true}
          autoRotate={false}
          enableDamping={true}
          dampingFactor={0.08}
          minDistance={3.2}
          maxDistance={7.0}
          // Constrain vertical rotation to maintain the flattering eye-level angle
          minPolarAngle={Math.PI / 2.2}
          maxPolarAngle={Math.PI / 1.95}
          // Constrain horizontal rotation around front view (-35 deg to +35 deg)
          minAzimuthAngle={-Math.PI / 5}
          maxAzimuthAngle={Math.PI / 5}
          target={[0, 0.95, 0]}
        />
      </Canvas>
      </div>
    </div>
  )
}
