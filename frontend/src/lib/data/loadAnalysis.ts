/**
 * Cargador del JSON de análisis.
 *
 * `mock.json` es la única fuente de datos de la interfaz: se lee por `fetch`
 * (la URL la resuelve Vite, funciona igual en dev y en build) para que la UI
 * tenga estados reales de carga y error cuando el JSON no está disponible.
 */
import mockUrl from './mock.json?url'
import type {
  AnalisisTendencias,
  ParRegiones,
  RegionAnalizada,
  Tendencia,
} from '../types/analysis'

/** URL resuelta por Vite del JSON de análisis. */
const URL_DATOS: string = mockUrl

/** Estado de la carga de datos para toda la interfaz. */
export type EstadoCarga =
  | { estado: 'cargando' }
  | { estado: 'error'; mensaje: string }
  | { estado: 'listo'; datos: AnalisisTendencias }

const TENDENCIAS_VALIDAS: Tendencia[] = ['alza', 'bajada']

function fallar(mensaje: string): never {
  throw new Error(mensaje)
}

/** Valida una región del contrato; devuelve un error claro si falta algo. */
function validarRegion(valor: unknown, etiqueta: string): RegionAnalizada {
  if (typeof valor !== 'object' || valor === null) {
    fallar(`La región ${etiqueta} no es un objeto válido.`)
  }
  const region = valor as Record<string, unknown>
  if (typeof region.nombre !== 'string' || region.nombre.length === 0) {
    fallar(`La región ${etiqueta} no tiene un nombre válido.`)
  }
  if (typeof region.lat !== 'number' || typeof region.lon !== 'number') {
    fallar(`La región ${etiqueta} no tiene coordenadas válidas.`)
  }
  if (region.tendencia !== 'alza' && region.tendencia !== 'bajada') {
    fallar(`La región ${etiqueta} tiene una tendencia desconocida.`)
  }
  if (typeof region.cambio_porcentual !== 'number') {
    fallar(`La región ${etiqueta} no tiene un cambio porcentual válido.`)
  }
  if (typeof region.significativa !== 'boolean') {
    fallar(`La región ${etiqueta} no declara si es significativa.`)
  }
  if (typeof region.explicacion !== 'string' || region.explicacion.length === 0) {
    fallar(`La región ${etiqueta} no tiene explicación.`)
  }
  return region as unknown as RegionAnalizada
}

/** Valida un par de regiones del contrato. */
function validarPar(valor: unknown, indice: number): ParRegiones {
  if (typeof valor !== 'object' || valor === null) {
    fallar(`El par ${indice + 1} no es un objeto válido.`)
  }
  const par = valor as Record<string, unknown>
  if (typeof par.id !== 'string' || par.id.length === 0) {
    fallar(`El par ${indice + 1} no tiene identificador.`)
  }
  return {
    id: par.id,
    region_a: validarRegion(par.region_a, `A del par "${par.id}"`),
    region_b: validarRegion(par.region_b, `B del par "${par.id}"`),
  }
}

/** Verifica que la respuesta tenga la forma mínima del contrato acordado. */
function validarAnalisis(datos: unknown): AnalisisTendencias {
  if (typeof datos !== 'object' || datos === null) {
    fallar('El JSON de análisis no es un objeto válido.')
  }
  const d = datos as Record<string, unknown>
  if (d.fuente !== 'mock') {
    console.warn('[datos] El campo "fuente" no es "mock"; revisar origen real.')
  }
  if (typeof d.variable !== 'string' || typeof d.nombre_variable !== 'string' || typeof d.unidad !== 'string') {
    fallar('El JSON de análisis no declara variable o unidad.')
  }
  if (
    typeof d.periodo !== 'object' ||
    d.periodo === null ||
    typeof (d.periodo as Record<string, unknown>).inicio !== 'number' ||
    typeof (d.periodo as Record<string, unknown>).fin !== 'number'
  ) {
    fallar('El JSON de análisis no declara un periodo válido.')
  }
  if (typeof d.contexto_oms !== 'string') {
    fallar('El JSON de análisis no incluye el contexto de la OMS.')
  }
  if (!Array.isArray(d.pares) || d.pares.length === 0) {
    fallar('El JSON de análisis no incluye pares de regiones.')
  }
  return {
    fuente: d.fuente as string,
    variable: d.variable as string,
    nombre_variable: d.nombre_variable as string,
    unidad: d.unidad as string,
    periodo: d.periodo as AnalisisTendencias['periodo'],
    contexto_oms: d.contexto_oms as string,
    pares: d.pares.map(validarPar),
  }
}

/** Lee y valida el JSON de análisis; lanza un error con mensaje claro. */
export async function cargarAnalisis(): Promise<AnalisisTendencias> {
  let respuesta: Response
  try {
    respuesta = await fetch(URL_DATOS)
  } catch {
    fallar('No se pudo conectar para leer el JSON de análisis.')
  }
  if (!respuesta.ok) {
    fallar(`El JSON de análisis no se pudo leer (HTTP ${respuesta.status}).`)
  }
  let datos: unknown
  try {
    datos = await respuesta.json()
  } catch {
    fallar('El JSON de análisis no es un documento válido.')
  }
  return validarAnalisis(datos)
}
