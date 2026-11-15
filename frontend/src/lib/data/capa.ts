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
export const MAXIMO_CELDAS_CAPA = 1000

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
}

/** Formatea un número con separador de miles. */
export function formatearNumero(valor: number): string {
  return valor.toLocaleString('es-ES')
}

/**
 * Elige las celdas que se dibujan.
 *
 * La capa del globo solo marca pendientes al alza, así que el recorte por
 * `|pendiente|` se aplica sobre ese mismo conjunto: lo que se promete en el
 * panel es exactamente lo que aparece en el globo.
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
  }))
  const limitado = significativas.length > MAXIMO_CELDAS_CAPA
  return {
    celdas,
    significativas: significativas.length,
    alAlza: alAlza.length,
    probadas: datos.pixeles_probados,
    limitado,
    aviso: limitado
      ? `Se muestran las ${formatearNumero(celdas.length)} celdas con mayor tendencia de ${formatearNumero(
          significativas.length,
        )} totales`
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
  )} celdas significativas tras corrección FDR. Sin pares de contraste.`
}

/**
 * Indica si el JSON trae valores por año y por celda.
 *
 * Los JSON actuales solo traen el valor anual inicial y final de cada celda,
 * así que no hay serie anual que pueda alimentar el deslizador.
 */
export function tieneValoresAnuales(datos: AnalisisTendencias): boolean {
  return datos.resultados_pixeles.some((pixel) => {
    const registro = pixel as unknown as Record<string, unknown>
    return Array.isArray(registro.valores_anuales) || Array.isArray(registro.serie_anual)
  })
}
