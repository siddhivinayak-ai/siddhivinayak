// EnvironmentLights.jsx
// Professional studio 3-point character lighting setup:
// - Ambient + Hemisphere: bright, clean, shadow-softening baseline
// - Key Light: front-left above, casts gentle directional shadows
// - Fill Light: front-right, softens contrast
// - Portrait Face/Chest Fill: highlights facial features and clothing textures
// - Rim / Back Light: cool sky-blue behind character for edge separation

export default function EnvironmentLights() {
  return (
    <>
      {/* ── Overall ambient baseline ── */}
      <ambientLight intensity={1.8} color="#F0F5FF" />

      {/* ── Hemisphere light: sky=light-blue, ground=white ── */}
      <hemisphereLight
        skyColor="#D8E8FC"
        groundColor="#FFFFFF"
        intensity={1.2}
      />

      {/* ── KEY LIGHT — front-left above ── */}
      <directionalLight
        color="#FFFFFF"
        intensity={2.4}
        position={[-3, 5, 3.5]}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-near={0.5}
        shadow-camera-far={25}
        shadow-camera-left={-4}
        shadow-camera-right={4}
        shadow-camera-top={5}
        shadow-camera-bottom={-1}
        shadow-bias={-0.0005}
        shadow-radius={6}
      />

      {/* ── FILL LIGHT — front-right ── */}
      <directionalLight
        color="#F8FAFF"
        intensity={1.1}
        position={[3.5, 3.5, 4]}
        castShadow={false}
      />

      {/* ── CHARACTER PORTRAIT FILL — soft eye/torso illumination ── */}
      <directionalLight
        color="#FFFFFF"
        intensity={0.6}
        position={[0, 1.8, 3.5]}
        castShadow={false}
      />

      {/* ── RIM / BACK LIGHT — cool atmospheric blue separation behind character ── */}
      <pointLight
        color="#6EA8F4"
        intensity={2.4}
        position={[0, 2.4, -3.2]}
        distance={12}
        decay={2}
      />

      {/* ── Top down ambient bounce ── */}
      <directionalLight
        color="#EEF4FF"
        intensity={0.5}
        position={[0, 8, 0]}
        castShadow={false}
      />
    </>
  )
}
