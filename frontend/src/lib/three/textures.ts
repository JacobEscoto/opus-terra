import * as THREE from "three";

/**
 * Small helper around THREE.TextureLoader that returns promises and keeps
 * track of the overall loading progress so the UI can show a real progress bar.
 */
export class TextureLoader {
  private manager: THREE.LoadingManager;
  private loader: THREE.TextureLoader;

  constructor(onProgress?: (ratio: number) => void) {
    this.manager = new THREE.LoadingManager();
    this.manager.onProgress = (_url, loaded, total) => {
      onProgress?.(total > 0 ? loaded / total : 0);
    };
    this.loader = new THREE.TextureLoader(this.manager);
  }

  /** Loads a texture and resolves once it is decoded. */
  load(
    url: string,
    { srgb = false, repeatX = 1, repeatY = 1 } = {},
  ): Promise<THREE.Texture> {
    return new Promise((resolve, reject) => {
      this.loader.load(
        url,
        (texture) => {
          if (srgb) texture.colorSpace = THREE.SRGBColorSpace;
          texture.wrapS = THREE.RepeatWrapping;
          texture.wrapT = THREE.ClampToEdgeWrapping;
          texture.repeat.set(repeatX, repeatY);
          texture.anisotropy = 8;
          texture.needsUpdate = true;
          resolve(texture);
        },
        undefined,
        () => reject(new Error(`No se pudo cargar la textura: ${url}`)),
      );
    });
  }

  /** Loads an image and hands back the raw <img> element (needed for pixel work). */
  loadImage(url: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      this.loader.load(
        url,
        (texture) => {
          const image = texture.image as HTMLImageElement;
          texture.dispose();
          resolve(image);
        },
        undefined,
        () => reject(new Error(`No se pudo cargar la imagen: ${url}`)),
      );
    });
  }
}

/**
 * Builds a roughness map out of the NASA specular (water) mask.
 *
 * The specular mask is white over the oceans and black over land, so the
 * inverse gives us "shiny water / matte land" which is what sells the
 * realism of the globe.
 */
export function createRoughnessFromSpecular(
  image: HTMLImageElement,
): THREE.CanvasTexture {
  const width = image.naturalWidth || image.width;
  const height = image.naturalHeight || image.height;

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error(
      "Canvas 2D no disponible para generar el mapa de rugosidad",
    );
  }

  context.drawImage(image, 0, 0, width, height);

  const pixels = context.getImageData(0, 0, width, height);
  const data = pixels.data;

  // water (specular = 1) -> roughness 0.34 ; land (specular = 0) -> roughness 0.95
  const LAND_ROUGHNESS = 0.95;
  const WATER_ROUGHNESS = 0.34;

  for (let i = 0; i < data.length; i += 4) {
    const water = data[i] / 255;
    const roughness =
      LAND_ROUGHNESS - (LAND_ROUGHNESS - WATER_ROUGHNESS) * water;
    const value = Math.round(roughness * 255);
    data[i] = value;
    data[i + 1] = value;
    data[i + 2] = value;
    data[i + 3] = 255;
  }

  context.putImageData(pixels, 0, 0);

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.anisotropy = 8;
  texture.needsUpdate = true;
  return texture;
}

/**
 * Builds the cloud shell texture out of the NASA cloud map.
 *
 * The NASA file stores the coverage in the alpha channel and paints the RGB
 * channels white, so we rebuild it with a boosted coverage curve (thin
 * cirrus stays subtle, solid cloud banks read clearly) and a very slightly
 * cool white so the clouds never look like flat paper.
 */
export function createCloudTexture(
  image: HTMLImageElement,
  boost = 0.82,
): THREE.CanvasTexture {
  const width = image.naturalWidth || image.width;
  const height = image.naturalHeight || image.height;

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Canvas 2D no disponible para generar el mapa de nubes");
  }

  context.drawImage(image, 0, 0, width, height);

  const pixels = context.getImageData(0, 0, width, height);
  const data = pixels.data;

  for (let i = 0; i < data.length; i += 4) {
    const sourceCoverage = data[i + 3] / 255;
    // Keep dense NASA cloud banks visible without turning them into an opaque
    // second globe over land.
    const coverage = Math.round(
      Math.min(1, Math.pow(sourceCoverage, 1.18) * boost) * 255,
    );
    data[i] = 244;
    data[i + 1] = 248;
    data[i + 2] = 255;
    data[i + 3] = coverage;
  }

  context.putImageData(pixels, 0, 0);

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  texture.needsUpdate = true;
  return texture;
}

/**
 * Procedural space environment used for the reflections on the oceans.
 *
 * This deliberately uses six initialized faces instead of PMREM's generated
 * render target. Firefox otherwise reports a lazy cubemap mipmap warning on
 * the first render, even though the environment is valid.
 */
export function createSpaceEnvironment(): THREE.CubeTexture {
  const colors = [
    "#0a1220",
    "#0b1220",
    "#101a2c",
    "#05080f",
    "#17243a",
    "#0b1220",
  ];
  const faces = colors.map((color) => {
    const canvas = document.createElement("canvas");
    canvas.width = 4;
    canvas.height = 4;
    const context = canvas.getContext("2d")!;
    context.fillStyle = color;
    context.fillRect(0, 0, 4, 4);
    return canvas;
  });

  const texture = new THREE.CubeTexture(faces);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;
  return texture;
}

/** Radial gradient used for the soft halo behind the planet. */
export function createRadialGlow(): THREE.CanvasTexture {
  const size = 256;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;

  const context = canvas.getContext("2d")!;
  const gradient = context.createRadialGradient(
    size / 2,
    size / 2,
    0,
    size / 2,
    size / 2,
    size / 2,
  );
  gradient.addColorStop(0, "rgba(255,255,255,0.9)");
  gradient.addColorStop(0.35, "rgba(255,255,255,0.32)");
  gradient.addColorStop(0.65, "rgba(255,255,255,0.08)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, size, size);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

/** Soft round dot used for the star field. */
export function createStarSprite(): THREE.CanvasTexture {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;

  const context = canvas.getContext("2d")!;
  const gradient = context.createRadialGradient(
    size / 2,
    size / 2,
    0,
    size / 2,
    size / 2,
    size / 2,
  );
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.25, "rgba(255,255,255,0.85)");
  gradient.addColorStop(0.55, "rgba(255,255,255,0.18)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, size, size);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}
