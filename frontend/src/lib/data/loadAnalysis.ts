/**
 * Cargador de los JSON de análisis.
 *
 * Cada variable del selector tiene su propio JSON en `frontend/public/data/`.
 * Los archivos se leen por `fetch` para que la UI valide la misma estructura
 * que recibirá en producción, y se cachean para que cambiar de variable no
 * vuelva a pedir el archivo.
 */
import type {
  AnalisisTendencias,
  ParRegiones,
  RegionAnalizada,
  ResultadoPixel,
} from "../types/analysis";
import type { EtiquetaGlobo } from "../three/etiquetasLayer";

/** Variable disponible en el selector, con su JSON y su leyenda de capa. */
export interface VariableCatalogo {
  id: string;
  etiqueta: string;
  tema: string;
  producto: string;
}

export interface RegionDisponible {
  id: string;
  nombre: string;
  bbox: [number, number, number, number];
  variables: string[];
}

/** Catálogo de variables que la interfaz puede representar. */
export const CATALOGO: VariableCatalogo[] = [
  {
    id: "merra2_t2m",
    etiqueta: "Temperatura (T2M)",
    tema: "temperatura",
    producto: "MERRA-2",
  },
  {
    id: "merra2_precipitacion",
    etiqueta: "Precipitación MERRA-2",
    tema: "precipitación modelada",
    producto: "MERRA-2",
  },
  {
    id: "imerg_precipitacion",
    etiqueta: "Precipitación IMERG",
    tema: "precipitación observada",
    producto: "GPM IMERG",
  },
  {
    id: "mod13c2_ndvi",
    etiqueta: "Vegetación (NDVI)",
    tema: "vegetación (NDVI)",
    producto: "MODIS",
  },
];

/** Estado de la carga de datos para toda la interfaz. */
export type EstadoCarga =
  | { estado: "cargando" }
  | { estado: "error"; mensaje: string }
  | { estado: "listo"; datos: AnalisisTendencias };

const cacheEnMemoria = new Map<string, AnalisisTendencias>();

export async function cargarPaises(region: string): Promise<EtiquetaGlobo[]> {
  try {
    const respuesta = await fetch(`/data/${region}/paises.json`);
    if (!respuesta.ok) return [];
    const datos: unknown = await respuesta.json();
    if (!Array.isArray(datos)) return [];
    return datos
      .filter((pais): pais is Record<string, unknown> => typeof pais === "object" && pais !== null)
      .filter((pais) => typeof pais.nombre === "string" && typeof pais.lat === "number" && typeof pais.lon === "number")
      .map((pais) => ({
        texto: pais.nombre as string,
        lat: pais.lat as number,
        lon: pais.lon as number,
        tipo: "pais" as const,
      }));
  } catch {
    return [];
  }
}

function fallar(mensaje: string): never {
  throw new Error(mensaje);
}

export async function cargarRegiones(): Promise<RegionDisponible[]> {
  const respuesta = await fetch("/data/regiones.json");
  if (!respuesta.ok) {
    fallar(`No se pudo leer regiones.json (HTTP ${respuesta.status}).`);
  }

  const datos: unknown = await respuesta.json();
  if (!Array.isArray(datos)) {
    fallar("regiones.json debe contener una lista.");
  }
  return datos as RegionDisponible[];
}

/** Valida una región del contrato; devuelve un error claro si falta algo. */
function validarRegion(valor: unknown, etiqueta: string): RegionAnalizada {
  if (typeof valor !== "object" || valor === null) {
    fallar(`La región ${etiqueta} no es un objeto válido.`);
  }
  const region = valor as Record<string, unknown>;
  if (typeof region.nombre !== "string" || region.nombre.length === 0) {
    fallar(`La región ${etiqueta} no tiene un nombre válido.`);
  }
  if (typeof region.lat !== "number" || typeof region.lon !== "number") {
    fallar(`La región ${etiqueta} no tiene coordenadas válidas.`);
  }
  if (region.tendencia !== "alza" && region.tendencia !== "bajada") {
    fallar(`La región ${etiqueta} tiene una tendencia desconocida.`);
  }
  if (typeof region.cambio_porcentual !== "number") {
    fallar(`La región ${etiqueta} no tiene un cambio porcentual válido.`);
  }
  if (typeof region.significativa !== "boolean") {
    fallar(`La región ${etiqueta} no declara si es significativa.`);
  }
  if (
    typeof region.explicacion !== "string" ||
    region.explicacion.length === 0
  ) {
    fallar(`La región ${etiqueta} no tiene explicación.`);
  }
  return region as unknown as RegionAnalizada;
}

/** Valida un par de regiones del contrato. */
function validarPar(valor: unknown, indice: number): ParRegiones {
  if (typeof valor !== "object" || valor === null) {
    fallar(`El par ${indice + 1} no es un objeto válido.`);
  }
  const par = valor as Record<string, unknown>;
  if (typeof par.id !== "string" || par.id.length === 0) {
    fallar(`El par ${indice + 1} no tiene identificador.`);
  }
  return {
    id: par.id,
    region_a: validarRegion(par.region_a, `A del par "${par.id}"`),
    region_b: validarRegion(par.region_b, `B del par "${par.id}"`),
  };
}

/** Valida el resultado estadístico de una celda antes de mostrarlo. */
function validarPixel(valor: unknown, indice: number): ResultadoPixel {
  if (typeof valor !== "object" || valor === null) {
    fallar(`El resultado de celda ${indice + 1} no es un objeto válido.`);
  }
  const pixel = valor as Record<string, unknown>;
  const numericos = [
    "lat",
    "lon",
    "mann_kendall_z",
    "p_valor",
    "sen_unidad_por_anio",
  ];
  if (
    numericos.some(
      (campo) =>
        typeof pixel[campo] !== "number" || !Number.isFinite(pixel[campo]),
    )
  ) {
    fallar(
      `El resultado de celda ${indice + 1} tiene valores numéricos inválidos.`,
    );
  }
  if (
    pixel.valores_anuales !== undefined &&
    (!Array.isArray(pixel.valores_anuales) ||
      pixel.valores_anuales.some(
        (valor) => typeof valor !== "number" || !Number.isFinite(valor),
      ))
  ) {
    fallar(
      `El resultado de celda ${indice + 1} tiene valores anuales inválidos.`,
    );
  }
  if (
    typeof pixel.direccion !== "string" ||
    typeof pixel.significativa_fdr !== "boolean"
  ) {
    fallar(`El resultado de celda ${indice + 1} está incompleto.`);
  }
  return pixel as unknown as ResultadoPixel;
}

/** Verifica que la respuesta tenga la forma mínima del contrato acordado. */
function validarAnalisis(datos: unknown): AnalisisTendencias {
  if (typeof datos !== "object" || datos === null) {
    fallar("El JSON de análisis no es un objeto válido.");
  }
  const d = datos as Record<string, unknown>;
  if (
    typeof d.variable !== "string" ||
    typeof d.nombre_variable !== "string" ||
    typeof d.unidad !== "string"
  ) {
    fallar("El JSON de análisis no declara variable o unidad.");
  }
  if (typeof d.region !== "string" || d.region.length === 0) {
    fallar("El JSON de análisis no declara un identificador de región válido.");
  }
  if (typeof d.region_nombre !== "string" || d.region_nombre.length === 0) {
    fallar("El JSON de análisis no declara un nombre de región válido.");
  }
  if (
    typeof d.periodo !== "object" ||
    d.periodo === null ||
    typeof (d.periodo as Record<string, unknown>).inicio !== "number" ||
    typeof (d.periodo as Record<string, unknown>).fin !== "number"
  ) {
    fallar("El JSON de análisis no declara un periodo válido.");
  }
  if (
    !Number.isInteger(d.pixeles_probados) ||
    (d.pixeles_probados as number) < 0
  ) {
    fallar(
      "El JSON de análisis no declara un número válido de celdas probadas.",
    );
  }
  if (
    !Number.isInteger(d.pixeles_significativos_fdr) ||
    (d.pixeles_significativos_fdr as number) < 0 ||
    (d.pixeles_significativos_fdr as number) > (d.pixeles_probados as number)
  ) {
    fallar(
      "El JSON de análisis no declara un número válido de celdas significativas.",
    );
  }
  if (!Array.isArray(d.pares)) {
    fallar("El JSON de análisis no declara una lista de pares válida.");
  }
  if (!Array.isArray(d.resultados_pixeles)) {
    fallar(
      "El JSON de análisis no declara una lista de resultados por celda válida.",
    );
  }
  return {
    fuente: d.fuente as string,
    variable: d.variable as string,
    region: d.region as string,
    region_nombre: d.region_nombre as string,
    nombre_variable: d.nombre_variable as string,
    unidad: d.unidad as string,
    periodo: d.periodo as AnalisisTendencias["periodo"],

    pares: d.pares.map(validarPar),
    pixeles_probados: d.pixeles_probados as number,
    pixeles_significativos_fdr: d.pixeles_significativos_fdr as number,
    resultados_pixeles: d.resultados_pixeles.map(validarPixel),
    limitacion: typeof d.limitacion === "string" ? d.limitacion : undefined,
  };
}

/** Lee y valida el JSON de una variable; lanza un error con mensaje claro. */
export async function cargarVariable(
  id: string,
  region: string,
): Promise<AnalisisTendencias> {
  const entrada = CATALOGO.some((variable) => variable.id === id);
  if (!entrada) {
    fallar(`No hay ninguna variable registrada con el identificador "${id}".`);
  }

  const clave = `${region}/${id}`;
  const enCache = cacheEnMemoria.get(clave);
  if (enCache) return enCache;

  const url = `/data/${region}/${id}.json`;

  let respuesta: Response;
  try {
    respuesta = await fetch(url);
  } catch {
    fallar(`No se pudo conectar para leer ${url}.`);
  }
  if (!respuesta.ok) {
    fallar(
      `El JSON de análisis no se pudo leer (HTTP ${respuesta.status}): ${url}.`,
    );
  }
  let datos: unknown;
  try {
    datos = await respuesta.json();
  } catch {
    fallar(`El JSON de análisis no es válido: ${url}.`);
  }
  const analizados = validarAnalisis(datos);
  if (analizados.region !== region) {
    fallar(`${url} declara la región "${analizados.region}", no ${region}.`);
  }

  cacheEnMemoria.set(clave, analizados);
  return analizados;
}
