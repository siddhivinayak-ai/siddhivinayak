// StudioFloor.jsx — simplified, no custom shader class (avoids extend/HMR issues)
// Uses a large plane with meshStandardMaterial; fog handles infinite fade.

export default function StudioFloor() {
  return (
    <>
      {/* Main floor plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.055, 0]} receiveShadow>
        <planeGeometry args={[80, 80]} />
        <meshStandardMaterial color="#D8E5F2" roughness={1} metalness={0} />
      </mesh>

      {/* Soft central darkening — just a slightly darker large circle near origin */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.054, 0]}>
        <circleGeometry args={[8, 64]} />
        <meshBasicMaterial color="#C8D8EE" transparent opacity={0.35} depthWrite={false} />
      </mesh>
    </>
  )
}
