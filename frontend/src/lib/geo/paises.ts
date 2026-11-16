/**
 * Detección geográfica de países a partir de un GeoJSON.
 *
 * La selección de un país es puramente geográfica: solo dice qué territorio
 * se pulsó. La disponibilidad de datos científicos se decide aparte, en
 * `regionDePais`, para que ambas cosas no se mezclen.
 */

/** Un anillo de coordenadas en grados: [lon, lat]. */
type Anillo = Array<[number, number]>;

interface Poligono {
  externo: Anillo;
  agujeros: Anillo[];
  /** minLon, minLat, maxLon, maxLat */
  bbox: [number, number, number, number];
}

export interface PaisGeo {
  nombre: string;
  nombreEn: string;
  iso: string;
  poligonos: Poligono[];
  bbox: [number, number, number, number];
  /** Punto representativo, usado para decidir la región de datos. */
  punto: { lat: number; lon: number };
}

type Geometria =
  | { type: "Polygon"; coordinates: Anillo[] }
  | { type: "MultiPolygon"; coordinates: Anillo[][] };

interface FeatureGeo {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: Geometria;
}

/** Normaliza un nombre para comparaciones sin acentos. */
function normalizar(texto: string): string {
  return texto
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

function bboxAnillo(anillo: Anillo): [number, number, number, number] {
  let minLon = Infinity;
  let minLat = Infinity;
  let maxLon = -Infinity;
  let maxLat = -Infinity;
  for (const [lon, lat] of anillo) {
    if (lon < minLon) minLon = lon;
    if (lat < minLat) minLat = lat;
    if (lon > maxLon) maxLon = lon;
    if (lat > maxLat) maxLat = lat;
  }
  return [minLon, minLat, maxLon, maxLat];
}

function centroide(anillo: Anillo): [number, number] {
  let lon = 0;
  let lat = 0;
  for (const [x, y] of anillo) {
    lon += x;
    lat += y;
  }
  const total = anillo.length || 1;
  return [lon / total, lat / total];
}

function poligonosDe(geometry: Geometria): Poligono[] {
  const grupos: Anillo[][] =
    geometry.type === "Polygon"
      ? [geometry.coordinates]
      : geometry.coordinates;
  return grupos.map((grupo) => {
    const [externo, ...agujeros] = grupo;
    return {
      externo,
      agujeros,
      bbox: bboxAnillo(externo),
    };
  });
}

function bboxPais(poligonos: Poligono[]): [number, number, number, number] {
  let minLon = Infinity;
  let minLat = Infinity;
  let maxLon = -Infinity;
  let maxLat = -Infinity;
  for (const poligono of poligonos) {
    const [a, b, c, d] = poligono.bbox;
    if (a < minLon) minLon = a;
    if (b < minLat) minLat = b;
    if (c > maxLon) maxLon = c;
    if (d > maxLat) maxLat = d;
  }
  return [minLon, minLat, maxLon, maxLat];
}

function puntoRepresentativo(
  feature: FeatureGeo,
  poligonos: Poligono[],
): { lat: number; lon: number } {
  const { LABEL_X, LABEL_Y } = feature.properties;
  if (typeof LABEL_X === "number" && typeof LABEL_Y === "number") {
    return { lat: LABEL_Y, lon: LABEL_X };
  }
  // Sin etiqueta, usa el centro del polígono más grande por número de vértices.
  const mayor = [...poligonos].sort(
    (a, b) => b.externo.length - a.externo.length,
  )[0];
  const [lon, lat] = centroide(mayor.externo);
  return { lat, lon };
}

function convertirFeature(feature: FeatureGeo): PaisGeo {
  const poligonos = poligonosDe(feature.geometry);
  const propiedades = feature.properties;
  const nombre =
    (propiedades.NAME_ES as string | undefined) ??
    (propiedades.ADMIN as string | undefined) ??
    "Territorio";
  return {
    nombre,
    nombreEn: (propiedades.NAME_EN as string | undefined) ?? nombre,
    iso: (propiedades.ISO_A3 as string | undefined) ?? "",
    poligonos,
    bbox: bboxPais(poligonos),
    punto: puntoRepresentativo(feature, poligonos),
  };
}

let promesa: Promise<PaisGeo[]> | null = null;

/**
 * Lee el GeoJSON recortado de Centroamérica y sus países vecinos.
 * El archivo vive en `public/data/geo/centroamerica.geojson`.
 */
export function cargarPaisesGeo(): Promise<PaisGeo[]> {
  if (!promesa) {
    promesa = fetch(`${import.meta.env.BASE_URL}data/geo/centroamerica.geojson`)
      .then((respuesta) => {
        if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
        return respuesta.json();
      })
      .then((datos: unknown) => {
        if (
          typeof datos !== "object" ||
          datos === null ||
          !Array.isArray((datos as { features?: unknown }).features)
        ) {
          return [];
        }
        return ((datos as { features: FeatureGeo[] }).features)
          .filter((feature) => feature.geometry !== null)
          .map(convertirFeature);
      })
      .catch((error: unknown) => {
        console.error("[paises] No se pudo leer el GeoJSON de países.", error);
        return [];
      });
  }
  return promesa;
}

function enBbox(
  lon: number,
  lat: number,
  bbox: [number, number, number, number],
): boolean {
  return (
    lon >= bbox[0] && lon <= bbox[2] && lat >= bbox[1] && lat <= bbox[3]
  );
}

/** Prueba de cruce (ray casting) para un punto dentro de un anillo. */
function puntoEnAnillo(lon: number, lat: number, anillo: Anillo): boolean {
  let dentro = false;
  for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i, i += 1) {
    const [xi, yi] = anillo[i];
    const [xj, yj] = anillo[j];
    const cruza =
      yi > lat !== yj > lat &&
      lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;
    if (cruza) dentro = !dentro;
  }
  return dentro;
}

function puntoEnPoligono(
  lon: number,
  lat: number,
  poligono: Poligono,
): boolean {
  if (!enBbox(lon, lat, poligono.bbox)) return false;
  if (!puntoEnAnillo(lon, lat, poligono.externo)) return false;
  for (const agujero of poligono.agujeros) {
    if (puntoEnAnillo(lon, lat, agujero)) return false;
  }
  return true;
}

/** Devuelve el país que contiene el punto, o null si cae en el mar. */
export function paisEnPunto(
  paises: PaisGeo[],
  lat: number,
  lon: number,
): PaisGeo | null {
  for (const pais of paises) {
    if (!enBbox(lon, lat, pais.bbox)) continue;
    if (pais.poligonos.some((p) => puntoEnPoligono(lon, lat, p))) return pais;
  }
  return null;
}

export interface RegionDisponibleLocal {
  id: string;
  nombre: string;
  bbox: [number, number, number, number];
}

/**
 * Decide qué región de datos cubre un país, sin mezclarlo con la selección
 * geográfica. Si el país coincide con la región por nombre, se prefiere esa;
 * si no, se usa la región más pequeña cuyo recuadro lo contiene.
 */
export function regionDePais(
  pais: PaisGeo,
  regiones: RegionDisponibleLocal[],
): RegionDisponibleLocal | null {
  const nombrePais = normalizar(pais.nombre);
  const porNombre = regiones.find(
    (region) => normalizar(region.id) === nombrePais,
  );
  if (porNombre) return porNombre;

  const candidatas = regiones.filter((region) =>
    enBbox(pais.punto.lon, pais.punto.lat, region.bbox),
  );
  if (candidatas.length === 0) return null;

  const area = (region: RegionDisponibleLocal) => {
    const [minLon, minLat, maxLon, maxLat] = region.bbox;
    return (maxLon - minLon) * (maxLat - minLat);
  };
  return candidatas.sort((a, b) => area(a) - area(b))[0];
}
