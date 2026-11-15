import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { latLonToSpherePosition } from "./tendenciaLayer";

export interface EtiquetaGlobo {
  texto: string;
  lat: number;
  lon: number;
  tipo?: "pais" | "lugar";
}

const ALTURA = 1.03; // un poco por encima de los marcadores (1.018)
const UMBRAL_FRENTE = 0.2; // 1 = justo frente a la cámara; <0 = lado trasero

let etiquetas: { objeto: CSS2DObject; tipo: "pais" | "lugar" }[] = [];
let raizActual: THREE.Object3D | null = null;
let listaPendiente: EtiquetaGlobo[] = [];
const posicion = new THREE.Vector3();
const haciaCamara = new THREE.Vector3();

export function agregarEtiquetas(raiz: THREE.Object3D, lista: EtiquetaGlobo[]) {
  quitarEtiquetas();
  raizActual = raiz;
  for (const item of lista) {
    const elemento = document.createElement("div");
    const tipo = item.tipo ?? "lugar";
    elemento.className = `globo-etiqueta globo-etiqueta--${tipo}`;
    elemento.textContent = item.texto; // textContent, nunca innerHTML
    const objeto = new CSS2DObject(elemento);
    objeto.position.copy(latLonToSpherePosition(item.lat, item.lon, ALTURA));
    raiz.add(objeto);
    etiquetas.push({ objeto, tipo });
  }
}

/** Registra las etiquetas y las monta cuando la escena del globo está lista. */
export function registrarEtiquetas(lista: EtiquetaGlobo[]) {
  listaPendiente = lista;
  if (raizActual) agregarEtiquetas(raizActual, listaPendiente);
}

/** Sincroniza las etiquetas registradas con una raíz de escena disponible. */
export function sincronizarEtiquetas(raiz: THREE.Object3D) {
  raizActual = raiz;
  agregarEtiquetas(raiz, listaPendiente);
}

export function quitarEtiquetas() {
  for (const { objeto } of etiquetas) {
    objeto.removeFromParent();
    objeto.element.remove();
  }
  etiquetas = [];
  raizActual = null;
}

/** Oculta las etiquetas que quedaron en la cara trasera del planeta. */
export function actualizarVisibilidad(camara: THREE.Camera) {
  haciaCamara.copy(camara.position).normalize();
  for (const { objeto, tipo } of etiquetas) {
    objeto.getWorldPosition(posicion).normalize();
    objeto.visible =
      posicion.dot(haciaCamara) > UMBRAL_FRENTE &&
      (tipo !== "pais" || camara.position.length() < 5.5);
  }
}
