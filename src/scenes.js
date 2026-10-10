// Scene presets — the brain returns a scene id with every answer and the
// 3D world eases into that mood. Backgrounds stay light so the glass UI reads well.
export const SCENES = {
  studio: {
    label: 'Studio', bg: '#EAF0F8', fog: '#EDF2FA', rim: '#6EA8F4', key: '#FFFFFF',
    floor: '#D8E5F2', particles: 'dust', particleColor: '#A4C0E0',
  },
  welding: {
    label: 'Welding Bay', bg: '#F3E6DC', fog: '#F2E4D8', rim: '#FF7A2F', key: '#FFE9D6',
    floor: '#E2D2C4', particles: 'sparks', particleColor: '#FF9A3C',
  },
  fasteners: {
    label: 'Fastener Lab', bg: '#E4E9EF', fog: '#E6EBF1', rim: '#8FA6C2', key: '#F4F8FF',
    floor: '#CFD8E3', particles: 'dust', particleColor: '#7D8FA6',
  },
  fluids: {
    label: 'Fluid Lab', bg: '#E0F2F6', fog: '#E3F4F8', rim: '#2FB3D6', key: '#F2FCFF',
    floor: '#C9E6EE', particles: 'bubbles', particleColor: '#6CCDE8',
  },
  thermal: {
    label: 'Thermal Lab', bg: '#F8E7E0', fog: '#F8E9E2', rim: '#FF5A36', key: '#FFF1E8',
    floor: '#EBD3C8', particles: 'heat', particleColor: '#FF7B4D',
  },
  machining: {
    label: 'Machine Shop', bg: '#EFEBE2', fog: '#F0ECE4', rim: '#E0A030', key: '#FFF8EA',
    floor: '#DDD5C5', particles: 'chips', particleColor: '#C99A3A',
  },
  design: {
    label: 'Design Studio', bg: '#E5ECF8', fog: '#E8EEF9', rim: '#4C7BE0', key: '#F6F9FF',
    floor: '#D3DEF2', particles: 'dust', particleColor: '#7FA0E0', grid: true,
  },
}

export const sceneOf = (id) => SCENES[id] || SCENES.studio
