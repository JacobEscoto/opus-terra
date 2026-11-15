import * as THREE from 'three'
import type { ResultadoPixel } from '../types/analysis'

/** Píxeles de la malla que pueden representarse como marcadores. */
export type CeldaTendencia = Pick<
  ResultadoPixel,
  'lat' | 'lon' | 'sen_unidad_por_anio' | 'significativa_fdr'
>

const PLANET_RADIUS = 1
const MARKER_RADIUS = PLANET_RADIUS * 1.018
const MARKER_SIZE = 0.038
const MARKER_OPACITY = 0.86

let capaActual: THREE.Points | null = null

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

/** Añade o reemplaza la capa de celdas significativas sobre el globo. */
export function agregarCapa(escena: THREE.Object3D, celdas: CeldaTendencia[]) {
  quitarCapa()

  const significativas = celdas.filter(
    (celda) =>
      celda.significativa_fdr &&
      celda.sen_unidad_por_anio > 0 &&
      Number.isFinite(celda.lat) &&
      Number.isFinite(celda.lon) &&
      Number.isFinite(celda.sen_unidad_por_anio),
  )
  if (significativas.length === 0) return

  const pendientes = significativas.map((celda) => celda.sen_unidad_por_anio)
  const minimo = Math.min(...pendientes)
  const maximo = Math.max(...pendientes)
  const posiciones = new Float32Array(significativas.length * 3)
  const colores = new Float32Array(significativas.length * 3)
  const color = new THREE.Color()

  significativas.forEach((celda, indice) => {
    const posicion = latLonToSpherePosition(celda.lat, celda.lon)
    posiciones[indice * 3] = posicion.x
    posiciones[indice * 3 + 1] = posicion.y
    posiciones[indice * 3 + 2] = posicion.z

    // Una sola familia ámbar; la pendiente aumenta la luminosidad, no cambia de tono.
    const intensidad = maximo === minimo ? 0.72 : (celda.sen_unidad_por_anio - minimo) / (maximo - minimo)
    color.setHSL(0.105, 0.88, 0.48 + intensidad * 0.22)
    colores[indice * 3] = color.r
    colores[indice * 3 + 1] = color.g
    colores[indice * 3 + 2] = color.b
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
}

/** Retira la capa actual y libera sus recursos GPU. */
export function quitarCapa() {
  if (!capaActual) return

  capaActual.removeFromParent()
  capaActual.geometry.dispose()
  ;(capaActual.material as THREE.Material).dispose()
  capaActual = null
}
