/**
 * Preparación de la capa de marcadores y de los textos que la explican.
 *
 * La capa del globo es una sola (`tendenciaLayer.ts`): recibe las celdas que
 * se dibujan y las filtra por significancia. Aquí se decide qué celdas se le
 * pasan y qué se le cuenta al usuario en el panel.
 */
import type { CeldaTendencia } from "../three/tendenciaLayer";
import type { AnalisisTendencias } from "../types/analysis";
import { CATALOGO, type VariableCatalogo } from "./loadAnalysis";

/** Tope de marcadores que se dibujan en el globo. */
export const MAXIMO_CELDAS_CAPA = 2500;

/** Celdas que se pasan a la capa, con los conteos que las explican. */
export interface PreparacionCapa {
  /** Celdas limitadas que se muestran en la lista del panel. */
  celdas: CeldaTendencia[];
  /** Todas las celdas significativas que se muestran sobre el globo. */
  celdasCapa: CeldaTendencia[];
  /** Celdas significativas que declara el JSON. */
  significativas: number;
  /** Celdas significativas con pendiente al alza. */
  alAlza: number;
  /** Celdas significativas con pendiente a la baja. */
  aLaBaja: number;
  /** Celdas probadas que declara el JSON. */
  probadas: number;
  /** La lista se recortó al tope de `MAXIMO_CELDAS_CAPA`. */
  limitado: boolean;
  /** Aviso del panel cuando la lista se recortó. */
  aviso: string | null;
  /** Máximo absoluto fijo para la escala de todos los años. */
  escalaMaxima: number;
}

/** Formatea un número con separador de miles. */
export function formatearNumero(valor: number): string {
  return valor.toLocaleString("es-ES");
}

export function nombreCorto(region: {
  nombre: string;
  ciudad?: string | null;
  pais?: string | null;
}): string {
  const partes = [region.ciudad, region.pais].filter(Boolean);
  return partes.length ? partes.join(", ") : region.nombre;
}

/**
 * Traduce el código de unidad del JSON a una forma que se lee sin conocerlo.
 *
 * El contrato conserva los códigos (`degC`, `mm/hr`); el panel muestra su
 * equivalente legible.
 */
export function unidadLegible(unidad: string): string {
  const equivalencias: Record<string, string> = {
    degC: "°C",
    "mm/hr": "mm/h",
    "kg m-2 s-1": "kg/m²/s",
    "NDVI (adimensional)": "NDVI",
  };
  return equivalencias[unidad] ?? unidad;
}

/** Escala aproximada de una celda, expresada en unidades que entiende el usuario. */
export function escalaCelda(fuente: string): string {
  if (fuente.includes("MERRA-2")) return "unos 55 × 70 km";
  if (fuente.includes("MODIS")) return "unos 5 × 5 km";
  return "";
}

/**
 * Años que cubre el periodo analizado, contando el año inicial y el final
 * (MERRA-2: 2001–2024 son 24 años, los mismos que declara `anios_completos`).
 */
export function aniosDelPeriodo(datos: AnalisisTendencias): number {
  return datos.periodo.fin - datos.periodo.inicio + 1;
}

/**
 * Frase resumen del panel, armada solo con los campos del JSON.
 *
 * Ejemplo (MERRA-2 T2M): «En 24 años, 45 de 110 zonas de la región se
 * calentaron de forma clara.» Los productos de promedio de área no tienen
 * celdas que analizar, así que la frase lo dice sin cifras inventadas.
 */
export function fraseResumen(datos: AnalisisTendencias): string {
  if (datos.pixeles_probados === 0) {
    return "No hay zonas analizadas: este producto es un promedio de área.";
  }
  const significativas = datos.resultados_pixeles.filter(
    (pixel) => pixel.significativa_fdr,
  );
  const alAlza = significativas.filter((pixel) => pixel.sen_unidad_por_anio > 0).length;
  const aLaBaja = significativas.filter((pixel) => pixel.sen_unidad_por_anio < 0).length;
  if (datos.variable === "merra2_t2m") {
    return `${formatearNumero(alAlza)} de ${formatearNumero(significativas.length)} zonas se calentaron y ${formatearNumero(aLaBaja)} se enfriaron de forma clara`;
  }
  return `${formatearNumero(alAlza)} aumentaron y ${formatearNumero(aLaBaja)} disminuyeron`;
}

/**
 * Elige las celdas que se dibujan.
 *
 * Se incluyen las celdas significativas de ambos signos. El recorte por
   * `|pendiente|` mantiene la lista del panel acotada sin ocultar una de las
   * dos direcciones de cambio. El globo recibe la lista completa.
 */
export function prepararCapa(datos: AnalisisTendencias): PreparacionCapa {
  const significativas = datos.resultados_pixeles.filter(
    (pixel) => pixel.significativa_fdr,
  );
  const ordenadas = [...significativas].sort(
    (a, b) => Math.abs(b.sen_unidad_por_anio) - Math.abs(a.sen_unidad_por_anio),
  );
  const alAlza = significativas.filter(
    (pixel) => pixel.sen_unidad_por_anio > 0,
  );
  const seleccion = ordenadas.slice(0, MAXIMO_CELDAS_CAPA);
  const convertir = (pixel: (typeof significativas)[number]): CeldaTendencia => ({
    lat: pixel.lat,
    lon: pixel.lon,
    sen_unidad_por_anio: pixel.sen_unidad_por_anio,
    significativa_fdr: pixel.significativa_fdr,
    valores_anuales: pixel.valores_anuales,
  });
  const celdas: CeldaTendencia[] = seleccion.map(convertir);
  const celdasCapa: CeldaTendencia[] = ordenadas.map(convertir);
  const limitado = significativas.length > MAXIMO_CELDAS_CAPA;
  let escalaMaxima = 0;
  for (const pixel of significativas) {
    const valores = pixel.valores_anuales ?? [pixel.sen_unidad_por_anio];
    for (const valor of valores) {
      if (Number.isFinite(valor))
        escalaMaxima = Math.max(escalaMaxima, Math.abs(valor));
    }
  }
  return {
    celdas,
    celdasCapa,
    significativas: significativas.length,
    alAlza: alAlza.length,
    aLaBaja: significativas.filter((pixel) => pixel.sen_unidad_por_anio < 0).length,
    probadas: datos.pixeles_probados,
    limitado,
    escalaMaxima: escalaMaxima || 1,
    aviso: limitado
      ? `Se muestran ${formatearNumero(celdas.length)} de las ${formatearNumero(
          significativas.length,
        )} celdas significativas (ambos signos), priorizadas por magnitud`
      : null,
  };
}

/** Entrada del catálogo que corresponde a un JSON ya validado. */
export function entradaDe(
  datos: AnalisisTendencias,
): VariableCatalogo | undefined {
  return CATALOGO.find((variable) => variable.id === datos.variable);
}

/** Texto de la capa de marcadores, con los conteos reales del JSON. */
export function descripcionCapa(
  datos: AnalisisTendencias,
  entrada: VariableCatalogo,
): string {
  const periodo = `${datos.periodo.inicio}–${datos.periodo.fin}`;
  if (datos.pixeles_probados === 0) {
    return `${entrada.tema} ${periodo} (${entrada.producto}): promedio de área, sin malla de celdas que dibujar.`;
  }
  const significativas = datos.resultados_pixeles.filter((pixel) => pixel.significativa_fdr);
  const alAlza = significativas.filter((pixel) => pixel.sen_unidad_por_anio > 0).length;
  const aLaBaja = significativas.filter((pixel) => pixel.sen_unidad_por_anio < 0).length;
  const sentidos =
    alAlza > 0 && aLaBaja > 0
      ? ` Hay cambios en ambos sentidos: ${formatearNumero(alAlza)} aumentan y ${formatearNumero(aLaBaja)} disminuyen.`
      : "";
  return `Tendencia de ${entrada.tema} ${periodo}, ${entrada.producto}, ajustada por ENSO. ${formatearNumero(
    datos.pixeles_significativos_fdr,
  )} zonas de ${datos.region_nombre} donde el cambio es claro y no parece casualidad.${sentidos}`;
}

/**
 * Indica si el JSON trae valores por año y por celda.
 *
 * La serie es opcional porque los productos de precipitación son promedios de
 * área y no tienen una malla anual por celda.
 */
export function tieneValoresAnuales(datos: AnalisisTendencias): boolean {
  return datos.resultados_pixeles.some((pixel) => {
    const registro = pixel as unknown as Record<string, unknown>;
    return (
      Array.isArray(registro.valores_anuales) ||
      Array.isArray(registro.serie_anual)
    );
  });
}
