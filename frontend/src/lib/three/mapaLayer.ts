/**
 * Capa de territorios sobre el globo.
 *
 * Dibuja las fronteras de los países del GeoJSON y resalta el país
 * seleccionado. La capa es una textura equirectangular sobre una esfera,
 * igual que la capa de tendencias, con el mismo mapeo lat/lon → píxel.
 */
import * as THREE from "three";
import type { PaisGeo } from "../geo/paises";

const ANCHO = 4096;
const ALTO = 2048;
const RADIO = 1.0015;

let malla: THREE.Mesh<
  THREE.SphereGeometry,
  THREE.MeshBasicMaterial
> | null = null;
let textura: THREE.CanvasTexture | null = null;

function aX(lon: number): number {
  return ((lon + 180) / 360) * ANCHO;
}

function aY(lat: number): number {
  return ((90 - lat) / 180) * ALTO;
}

function trazarAnillo(
  contexto: CanvasRenderingContext2D,
  anillo: Array<[number, number]>,
) {
  anillo.forEach(([lon, lat], indice) => {
    const x = aX(lon);
    const y = aY(lat);
    if (indice === 0) contexto.moveTo(x, y);
    else contexto.lineTo(x, y);
  });
  contexto.closePath();
}

function trazarPoligono(
  contexto: CanvasRenderingContext2D,
  pais: PaisGeo,
  indice: number,
) {
  const poligono = pais.poligonos[indice];
  trazarAnillo(contexto, poligono.externo);
  for (const agujero of poligono.agujeros) trazarAnillo(contexto, agujero);
}

function pintar(
  contexto: CanvasRenderingContext2D,
  paises: PaisGeo[],
  seleccion: PaisGeo | null,
) {
  contexto.clearRect(0, 0, ANCHO, ALTO);

  // Fronteras discretas de todos los territorios: ayudan a saber dónde se
  // puede pulsar sin marcar la superficie de forma permanente.
  contexto.lineWidth = 1;
  contexto.strokeStyle = "rgba(237, 243, 250, 0.16)";
  contexto.beginPath();
  for (const pais of paises) {
    for (let i = 0; i < pais.poligonos.length; i += 1) {
      trazarPoligono(contexto, pais, i);
    }
  }
  contexto.stroke();

  if (!seleccion) return;

  contexto.beginPath();
  for (let i = 0; i < seleccion.poligonos.length; i += 1) {
    trazarPoligono(contexto, seleccion, i);
  }
  contexto.fillStyle = "rgba(255, 181, 107, 0.22)";
  contexto.fill("evenodd");
  contexto.lineWidth = 2;
  contexto.strokeStyle = "rgba(255, 181, 107, 0.95)";
  contexto.stroke();
}

function destruir() {
  if (malla) {
    malla.removeFromParent();
    malla.geometry.dispose();
    malla.material.dispose();
  }
  textura?.dispose();
  malla = null;
  textura = null;
}

/** Repinta fronteras y selección; se llama al cargar el GeoJSON y al elegir. */
export function pintarMapa(
  raiz: THREE.Object3D,
  paises: PaisGeo[],
  seleccion: PaisGeo | null,
) {
  destruir();
  if (paises.length === 0) return;

  const lienzo = document.createElement("canvas");
  lienzo.width = ANCHO;
  lienzo.height = ALTO;
  const contexto = lienzo.getContext("2d");
  if (!contexto) return;

  pintar(contexto, paises, seleccion);

  textura = new THREE.CanvasTexture(lienzo);
  textura.colorSpace = THREE.SRGBColorSpace;
  textura.needsUpdate = true;

  const material = new THREE.MeshBasicMaterial({
    map: textura,
    transparent: true,
    depthWrite: false,
    toneMapped: false,
  });
  const geometria = new THREE.SphereGeometry(RADIO, 128, 64);
  malla = new THREE.Mesh(geometria, material);
  malla.name = "mapa-fronteras";
  malla.renderOrder = 1;
  malla.raycast = () => undefined;
  raiz.add(malla);
}
