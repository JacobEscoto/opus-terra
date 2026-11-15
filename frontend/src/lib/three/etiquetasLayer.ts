import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { latLonToSpherePosition } from "./tendenciaLayer";

export interface EtiquetaGlobo {
  texto: string;
  lat: number;
  lon: number;
}

const ALTURA = 1.03; // un poco por encima de los marcadores (1.018)
const UMBRAL_FRENTE = 0.2; // 1 = justo frente a la cámara; <0 = lado trasero

let etiquetas: CSS2DObject[] = [];
const posicion = new THREE.Vector3();
const haciaCamara = new THREE.Vector3();

export function agregarEtiquetas(raiz: THREE.Object3D, lista: EtiquetaGlobo[]) {
  quitarEtiquetas();
  for (const item of lista) {
    const elemento = document.createElement("div");
    elemento.className = "globo-etiqueta";
    elemento.textContent = item.texto; // textContent, nunca innerHTML
    const objeto = new CSS2DObject(elemento);
    objeto.position.copy(latLonToSpherePosition(item.lat, item.lon, ALTURA));
    raiz.add(objeto);
    etiquetas.push(objeto);
  }
}

export function quitarEtiquetas() {
  for (const objeto of etiquetas) {
    objeto.removeFromParent();
    objeto.element.remove();
  }
  etiquetas = [];
}

/** Oculta las etiquetas que quedaron en la cara trasera del planeta. */
export function actualizarVisibilidad(camara: THREE.Camera) {
  haciaCamara.copy(camara.position).normalize();
  for (const objeto of etiquetas) {
    objeto.getWorldPosition(posicion).normalize();
    objeto.visible = posicion.dot(haciaCamara) > UMBRAL_FRENTE;
  }
}
