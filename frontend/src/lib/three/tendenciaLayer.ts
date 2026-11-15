import * as THREE from "three";
import type { ResultadoPixel } from "../types/analysis";
import { sincronizarEtiquetas } from "./etiquetasLayer";

/** Celdas de la malla que pueden representarse sobre el globo. */
export type CeldaTendencia = Pick<
  ResultadoPixel,
  | "lat"
  | "lon"
  | "sen_unidad_por_anio"
  | "significativa_fdr"
  | "valores_anuales"
>;

const PLANET_RADIUS = 1;
const LAYER_RADIUS = 1.003;
const TEXTURE_WIDTH = 4096;
const TEXTURE_HEIGHT = 2048;

let capaActual: THREE.Mesh<THREE.SphereGeometry, THREE.MeshBasicMaterial> | null = null;
let texturaActual: THREE.CanvasTexture | null = null;
let lienzoActual: HTMLCanvasElement | null = null;
let celdasActuales: CeldaTendencia[] = [];
let aniosActuales: number[] = [];
let escalaMaximaActual = 1;
let anchoCelda = 0.5;
let altoCelda = 0.5;

const COLOR_FRIO = new THREE.Color("#3988c2");
const COLOR_NEUTRO = new THREE.Color("#d9d4c8");
const COLOR_CALIDO = new THREE.Color("#d99435");
const COLOR_NO_SIGNIFICATIVO = "#8b929b";

/** Convierte coordenadas geográficas a la convención usada por el globo. */
export function latLonToSpherePosition(
  lat: number,
  lon: number,
  radius = LAYER_RADIUS,
) {
  const latRad = THREE.MathUtils.degToRad(lat);
  const lonRad = THREE.MathUtils.degToRad(lon);
  const cosLat = Math.cos(latRad);
  return new THREE.Vector3(
    radius * cosLat * Math.cos(lonRad),
    radius * Math.sin(latRad),
    -radius * cosLat * Math.sin(lonRad),
  );
}

function colorParaValor(valor: number, color: THREE.Color): THREE.Color {
  const normalizado = THREE.MathUtils.clamp(valor / escalaMaximaActual, -1, 1);
  if (normalizado < 0) {
    return color.copy(COLOR_NEUTRO).lerp(COLOR_FRIO, Math.abs(normalizado));
  }
  return color.copy(COLOR_NEUTRO).lerp(COLOR_CALIDO, normalizado);
}

function diferenciaCelda(valores: number[]): number {
  const unicos = [...new Set(valores.filter(Number.isFinite))].sort((a, b) => a - b);
  let minima = Infinity;
  for (let indice = 1; indice < unicos.length; indice += 1) {
    const diferencia = unicos[indice] - unicos[indice - 1];
    if (diferencia > 0) minima = Math.min(minima, diferencia);
  }
  return Number.isFinite(minima) ? Math.min(minima, 1) : 0.5;
}

function pintarCanvas(anio: number) {
  if (!lienzoActual) return;
  const contexto = lienzoActual.getContext("2d");
  if (!contexto) return;
  contexto.clearRect(0, 0, TEXTURE_WIDTH, TEXTURE_HEIGHT);
  const indiceAnio = aniosActuales.indexOf(anio);
  const color = new THREE.Color();
  for (const celda of celdasActuales) {
    const valor =
      indiceAnio >= 0 && celda.valores_anuales?.[indiceAnio] !== undefined
        ? celda.valores_anuales[indiceAnio]
        : celda.sen_unidad_por_anio;
    contexto.fillStyle = celda.significativa_fdr
      ? (() => {
          colorParaValor(valor, color);
          return `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`;
        })()
      : COLOR_NO_SIGNIFICATIVO;
    const x = ((celda.lon + 180) / 360) * TEXTURE_WIDTH;
    const y = ((90 - celda.lat) / 180) * TEXTURE_HEIGHT;
    const mitadX = (anchoCelda / 360) * TEXTURE_WIDTH / 2;
    const mitadY = (altoCelda / 180) * TEXTURE_HEIGHT / 2;
    const izquierda = Math.floor(x - mitadX);
    const arriba = Math.floor(y - mitadY);
    const derecha = Math.max(izquierda + 1, Math.ceil(x + mitadX));
    const abajo = Math.max(arriba + 1, Math.ceil(y + mitadY));
    contexto.fillRect(izquierda, arriba, derecha - izquierda, abajo - arriba);
  }
  texturaActual!.needsUpdate = true;
}

/** Repinta la textura existente para el año elegido. */
export function actualizarColores(anio: number) {
  if (!capaActual || !texturaActual) return;
  pintarCanvas(anio);
}

/** Añade o reemplaza la esfera de tendencias y zonas sin cambio claro. */
export function agregarCapa(
  escena: THREE.Object3D,
  celdas: CeldaTendencia[],
  anios: number[] = [],
  escalaMaxima = 0,
) {
  quitarCapa();
  sincronizarEtiquetas(escena);
  const celdasValidas = celdas.filter(
    (celda) =>
      Number.isFinite(celda.lat) &&
      Number.isFinite(celda.lon) &&
      Number.isFinite(celda.sen_unidad_por_anio),
  );
  if (celdasValidas.length === 0) return;

  celdasActuales = celdasValidas;
  aniosActuales = anios;
  escalaMaximaActual = escalaMaxima > 0 ? escalaMaxima : 1;
  anchoCelda = diferenciaCelda(celdasValidas.map((celda) => celda.lon));
  altoCelda = diferenciaCelda(celdasValidas.map((celda) => celda.lat));

  lienzoActual = document.createElement("canvas");
  lienzoActual.width = TEXTURE_WIDTH;
  lienzoActual.height = TEXTURE_HEIGHT;
  texturaActual = new THREE.CanvasTexture(lienzoActual);
  texturaActual.colorSpace = THREE.SRGBColorSpace;
  texturaActual.needsUpdate = true;
  const material = new THREE.MeshBasicMaterial({
    map: texturaActual,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
    toneMapped: false,
  });
  const geometria = new THREE.SphereGeometry(LAYER_RADIUS, 128, 64);
  capaActual = new THREE.Mesh(geometria, material);
  capaActual.name = "tendencias-t2m";
  capaActual.renderOrder = 2;
  capaActual.raycast = () => undefined;
  escena.add(capaActual);
  pintarCanvas(anios.at(-1) ?? 0);
}

/** Retira la capa actual y libera geometría, material y textura. */
export function quitarCapa() {
  if (capaActual) {
    capaActual.removeFromParent();
    capaActual.geometry.dispose();
    capaActual.material.dispose();
  }
  texturaActual?.dispose();
  capaActual = null;
  texturaActual = null;
  lienzoActual = null;
  celdasActuales = [];
  aniosActuales = [];
  escalaMaximaActual = 1;
}
