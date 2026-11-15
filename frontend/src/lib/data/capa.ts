/**
 * Preparación de la capa de marcadores y de los textos que la explican.
 *
 * La capa del globo es una sola (`tendenciaLayer.ts`): recibe las celdas que
 * se dibujan y las filtra por significancia. Aquí se decide qué celdas se le
 * pasan y qué se le cuenta al usuario en el panel.
 */
import type { CeldaTendencia } from '../three/tendenciaLayer'
import type { AnalisisTendencias } from '../types/analysis'
import { CATALOGO, type VariableCatalogo } from './loadAnalysis'

/** Tope de marcadores que se dibujan en el globo. */
export const MAXIMO_CELDAS_CAPA = 2500

/** Celdas que se pasan a la capa, con los conteos que las explican. */
export interface PreparacionCapa {
  /** Celdas que se pasan a `agregarCapa`. */
  celdas: CeldaTendencia[]
  /** Celdas significativas que declara el JSON. */
  significativas: number
  /** Celdas significativas con pendiente al alza. */
  alAlza: number
  /** Celdas probadas que declara el JSON. */
  probadas: number
  /** La lista se recortó al tope de `MAXIMO_CELDAS_CAPA`. */
  limitado: boolean
  /** Aviso del panel cuando la lista se recortó. */
  aviso: string | null
  /** Máximo absoluto fijo para la escala de todos los años. */
  escalaMaxima: number
}

/** Formatea un número con separador de miles. */
export function formatearNumero(valor: number): string {
  return valor.toLocaleString('es-ES')
}

/**
 * Traduce el código de unidad del JSON a una forma que se lee sin conocerlo.
 *
 * El contrato conserva los códigos (`degC`, `mm/hr`); el panel muestra su
 * equivalente legible.
 */
export function unidadLegible(unidad: string): string {
  const equivalencias: Record<string, string> = {
    degC: '°C',
    'mm/hr': 'mm/h',
    'kg m-2 s-1': 'kg/m²/s',
    'NDVI (adimensional)': 'NDVI',
  }
  return equivalencias[unidad] ?? unidad
}

/**
 * Años que cubre el periodo analizado, contando el año inicial y el final
 * (MERRA-2: 2001–2024 son 24 años, los mismos que declara `anios_completos`).
 */
export function aniosDelPeriodo(datos: AnalisisTendencias): number {
  return datos.periodo.fin - datos.periodo.inicio + 1
}

/**
 * Frase resumen del panel, armada solo con los campos del JSON.
 *
 * Ejemplo (MERRA-2 T2M): «En 24 años, 45 de 110 zonas de Honduras se
 * calentaron de forma clara.» Los productos de promedio de área no tienen
 * celdas que analizar, así que la frase lo dice sin cifras inventadas.
 */
export function fraseResumen(datos: AnalisisTendencias): string {
  const anios = aniosDelPeriodo(datos)
  if (datos.pixeles_probados === 0) {
    return 'No hay zonas analizadas: este producto es un promedio de área.'
  }
  const cambio =
    datos.variable === 'merra2_t2m'
      ? 'se calentaron de forma clara'
      : 'mostraron un cambio claro'
  return `En ${anios} años, ${formatearNumero(datos.pixeles_significativos_fdr)} de ${formatearNumero(
    datos.pixeles_probados,
  )} zonas de Honduras ${cambio}.`
}

/**
 * Elige las celdas que se dibujan.
 *
 * Se incluyen las celdas significativas de ambos signos. El recorte por
 * `|pendiente|` mantiene acotado el número de puntos sin ocultar una de las
 * dos direcciones de cambio.
 */
export function prepararCapa(datos: AnalisisTendencias): PreparacionCapa {
  const significativas = datos.resultados_pixeles.filter((pixel) => pixel.significativa_fdr)
  const alAlza = significativas.filter((pixel) => pixel.sen_unidad_por_anio > 0)
  const ordenadas = [...alAlza].sort(
    (a, b) => Math.abs(b.sen_unidad_por_anio) - Math.abs(a.sen_unidad_por_anio),
  )
  const seleccion = ordenadas.slice(0, MAXIMO_CELDAS_CAPA)
  const celdas: CeldaTendencia[] = seleccion.map((pixel) => ({
    lat: pixel.lat,
    lon: pixel.lon,
    sen_unidad_por_anio: pixel.sen_unidad_por_anio,
    significativa_fdr: pixel.significativa_fdr,
    valores_anuales: pixel.valores_anuales,
  }))
  const limitado = significativas.length > MAXIMO_CELDAS_CAPA
  const valoresAnuales = significativas.flatMap((pixel) => pixel.valores_anuales ?? [])
  const valoresEscala = valoresAnuales.length
    ? valoresAnuales
    : significativas.map((pixel) => pixel.sen_unidad_por_anio)
  const escalaMaxima = valoresEscala.reduce(
    (maximo, valor) => (Number.isFinite(valor) ? Math.max(maximo, Math.abs(valor)) : maximo),
    0,
  )
  return {
    celdas,
    significativas: significativas.length,
    alAlza: alAlza.length,
    probadas: datos.pixeles_probados,
    limitado,
    escalaMaxima: escalaMaxima || 1,
    aviso: limitado
      ? `Se muestran ${formatearNumero(celdas.length)} de las ${formatearNumero(
          significativas.length,
        )} celdas significativas (ambos signos), priorizadas por magnitud`
      : null,
  }
}

/** Entrada del catálogo que corresponde a un JSON ya validado. */
export function entradaDe(datos: AnalisisTendencias): VariableCatalogo | undefined {
  return CATALOGO.find((variable) => variable.id === datos.variable)
}

/** Texto de la capa de marcadores, con los conteos reales del JSON. */
export function descripcionCapa(datos: AnalisisTendencias, entrada: VariableCatalogo): string {
  const periodo = `${datos.periodo.inicio}–${datos.periodo.fin}`
  if (datos.pixeles_probados === 0) {
    return `${entrada.tema} ${periodo} (${entrada.producto}): promedio de área, sin malla de píxeles que dibujar.`
  }
  return `Tendencia de ${entrada.tema} ${periodo}, ${entrada.producto}, ajustada por ENSO. ${formatearNumero(
    datos.pixeles_significativos_fdr,
  )} zonas donde el cambio es claro y no parece casualidad. No encontramos zonas con cambios opuestos.`
}

/**
 * Indica si el JSON trae valores por año y por celda.
 *
 * La serie es opcional porque los productos de precipitación son promedios de
 * área y no tienen una malla anual por celda.
 */
export function tieneValoresAnuales(datos: AnalisisTendencias): boolean {
  return datos.resultados_pixeles.some((pixel) => {
    const registro = pixel as unknown as Record<string, unknown>
    return Array.isArray(registro.valores_anuales) || Array.isArray(registro.serie_anual)
  })
}
