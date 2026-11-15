import * as THREE from 'three'
import type { ResultadoPixel } from '../types/analysis'

/** Celdas de la malla que pueden representarse como marcadores. */
export type CeldaTendencia = Pick<
  ResultadoPixel,
  'lat' | 'lon' | 'sen_unidad_por_anio' | 'significativa_fdr' | 'valores_anuales'
>

const PLANET_RADIUS = 1
const MARKER_RADIUS = PLANET_RADIUS * 1.018
const MARKER_SIZE = 0.038
const MARKER_OPACITY = 0.86

let capaActual: THREE.Points | null = null
let celdasActuales: CeldaTendencia[] = []
let aniosActuales: number[] = []
let escalaMaximaActual = 1

const COLOR_FRIO = new THREE.Color('#3988c2')
const COLOR_NEUTRO = new THREE.Color('#d9d4c8')
const COLOR_CALIDO = new THREE.Color('#d99435')

/**
 * Convierte coordenadas geográficas con la misma convención que EarthScene:
 * lon oeste es negativa y se proyecta mediante atan2(-z, x).
 */
export function latLonToSpherePosition(lat: number, lon: number, radius = MARKER_RADIUS) {
  const latRad = THREE.MathUtils.degToRad(lat)
  const lonRad = THREE.MathUtils.degToRad(lon)
  const cosLat = Math.cos(latRad)

  return new THREE.Vector3(
    radius * cosLat * Math.cos(lonRad),
    radius * Math.sin(latRad),
    -radius * cosLat * Math.sin(lonRad),
  )
}

function colorParaValor(valor: number, color: THREE.Color): THREE.Color {
  const normalizado = THREE.MathUtils.clamp(valor / escalaMaximaActual, -1, 1)
  if (normalizado < 0) {
    return color.copy(COLOR_NEUTRO).lerp(COLOR_FRIO, Math.abs(normalizado))
  }
  return color.copy(COLOR_NEUTRO).lerp(COLOR_CALIDO, normalizado)
}

/** Actualiza solo el atributo de color de la capa ya creada. */
export function actualizarColores(anio: number) {
  if (!capaActual) return

  const indiceAnio = aniosActuales.indexOf(anio)
  const colores = capaActual.geometry.getAttribute('color') as THREE.BufferAttribute
  const color = new THREE.Color()
  celdasActuales.forEach((celda, indice) => {
    const valor =
      indiceAnio >= 0 && celda.valores_anuales?.[indiceAnio] !== undefined
        ? celda.valores_anuales[indiceAnio]
        : celda.sen_unidad_por_anio
    colorParaValor(valor, color)
    colores.setXYZ(indice, color.r, color.g, color.b)
  })
  colores.needsUpdate = true
}

/** Añade o reemplaza la capa de celdas significativas sobre el globo. */
export function agregarCapa(
  escena: THREE.Object3D,
  celdas: CeldaTendencia[],
  anios: number[] = [],
  escalaMaxima = 0,
) {
  quitarCapa()

  const significativas = celdas.filter(
    (celda) =>
      celda.significativa_fdr &&
      Number.isFinite(celda.lat) &&
      Number.isFinite(celda.lon) &&
      Number.isFinite(celda.sen_unidad_por_anio),
  )
  if (significativas.length === 0) return

  celdasActuales = significativas
  aniosActuales = anios
  escalaMaximaActual = escalaMaxima > 0 ? escalaMaxima : 1
  const posiciones = new Float32Array(significativas.length * 3)
  const colores = new Float32Array(significativas.length * 3)

  significativas.forEach((celda, indice) => {
    const posicion = latLonToSpherePosition(celda.lat, celda.lon)
    posiciones[indice * 3] = posicion.x
    posiciones[indice * 3 + 1] = posicion.y
    posiciones[indice * 3 + 2] = posicion.z

  })

  const geometria = new THREE.BufferGeometry()
  geometria.setAttribute('position', new THREE.BufferAttribute(posiciones, 3))
  geometria.setAttribute('color', new THREE.BufferAttribute(colores, 3))

  const material = new THREE.PointsMaterial({
    size: MARKER_SIZE,
    sizeAttenuation: true,
    vertexColors: true,
    transparent: true,
    opacity: MARKER_OPACITY,
    depthWrite: false,
    depthTest: true,
  })

  capaActual = new THREE.Points(geometria, material)
  capaActual.name = 'tendencias-t2m'
  capaActual.renderOrder = 2
  capaActual.raycast = () => undefined
  escena.add(capaActual)
  actualizarColores(anios.at(-1) ?? 0)
}

/** Retira la capa actual y libera sus recursos GPU. */
export function quitarCapa() {
  if (!capaActual) return

  capaActual.removeFromParent()
  capaActual.geometry.dispose()
  ;(capaActual.material as THREE.Material).dispose()
  capaActual = null
  celdasActuales = []
  aniosActuales = []
  escalaMaximaActual = 1
}
