/**
 * Contrato JSON del análisis de tendencias.
 *
 * Este tipo es la descripción canónica del intercambio entre el backend y la
 * interfaz. Por ahora la única fuente de datos es `../data/mock.json`, que
 * sigue exactamente esta estructura.
 */

/** Dirección del cambio detectado en la serie de una región. */
export type Tendencia = 'alza' | 'bajada'

/** Una región analizada, con su tendencia, significancia y explicación. */
export interface RegionAnalizada {
  /** Nombre legible de la región. */
  nombre: string
  /** Centro aproximado de la región, en grados decimales. */
  lat: number
  lon: number
  /** Dirección del cambio detectado. */
  tendencia: Tendencia
  /** Cambio relativo acumulado en el periodo, en porcentaje. */
  cambio_porcentual: number
  /** ¿El cambio es estadísticamente significativo? */
  significativa: boolean
  /** Explicación en lenguaje sencillo, sin diagnósticos. */
  explicacion: string
}

/** Par de regiones con cambios comparables u opuestos. */
export interface ParRegiones {
  /** Identificador estable del par (p. ej. "benguela-guinea"). */
  id: string
  region_a: RegionAnalizada
  region_b: RegionAnalizada
}

/** Periodo temporal cubierto por el análisis, en años. */
export interface PeriodoAnalisis {
  inicio: number
  fin: number
}

/** Respuesta completa del análisis de tendencias. */
export interface AnalisisTendencias {
  /** Origen de los datos; "mock" marca que son datos de prueba. */
  fuente: string
  /** Identificador de la variable analizada (p. ej. "clorofila_a"). */
  variable: string
  /** Nombre legible de la variable. */
  nombre_variable: string
  /** Unidad de medida de la variable. */
  unidad: string
  /** Años cubiertos por el análisis. */
  periodo: PeriodoAnalisis
  /** Contexto general de la OMS para la variable, sin diagnósticos. */
  contexto_oms: string
  /** Pares de regiones propuestos por el análisis. */
  pares: ParRegiones[]
}
