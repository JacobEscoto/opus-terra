import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CSS2DRenderer } from "three/addons/renderers/CSS2DRenderer.js";
import { actualizarVisibilidad } from "./etiquetasLayer";
import {
  TextureLoader,
  createCloudTexture,
  createRadialGlow,
  createRoughnessFromSpecular,
  createSpaceEnvironment,
  createStarSprite,
} from "./textures";

const TEXTURES = {
  day: `${import.meta.env.BASE_URL}textures/earth_day_4096.jpg`,
  night: `${import.meta.env.BASE_URL}textures/earth_night_4096.jpg`,
  specular: `${import.meta.env.BASE_URL}textures/earth_specular_2048.jpg`,
  normal: `${import.meta.env.BASE_URL}textures/earth_normal_2048.jpg`,
  clouds: `${import.meta.env.BASE_URL}textures/earth_clouds_1024.png`,
};

export interface EarthTelemetry {
  /** Degrees, positive towards the north pole. */
  lat: number;
  /** Degrees, negative towards the west. */
  lon: number;
}

export interface EarthSceneOptions {
  canvas: HTMLCanvasElement;
  /** Radians per second of planet rotation. */
  spinSpeed?: number;
  /** Start with the camera orbiting on its own. */
  autoRotate?: boolean;
  /** How far off-centre the planet sits, as a fraction of the canvas width. */
  horizontalOffset?: number;
  /** Uses even ambient lighting so data layers remain visible everywhere. */
  dataMode?: boolean;
  onProgress?: (ratio: number) => void;
  onTelemetry?: (telemetry: EarthTelemetry | null) => void;
  onInteraction?: () => void;
}

const AXIAL_TILT = THREE.MathUtils.degToRad(23.44);
const PLANET_RADIUS = 1;
const ATMOSPHERE_RADIUS = 1.18;

/**
 * A realistic, self-contained 3D Earth.
 *
 * Layers, from the inside out:
 *  1. Surface  — NASA Blue Marble albedo + normal map + ocean specular/roughness.
 *  2. Clouds   — translucent NASA cloud shell, drifting slightly faster.
 *  3. Atmosphere — Fresnel glow shell that reacts to the sun direction.
 *
 * The city lights (night map) are painted as emissive and masked by the
 * day/night terminator through a small shader patch, so they only glow on
 * the night side of the planet.
 */
export class EarthScene {
  private readonly options: EarthSceneOptions;
  private readonly canvas: HTMLCanvasElement;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly controls: OrbitControls;

  private readonly tiltGroup = new THREE.Group();
  private readonly spinGroup = new THREE.Group();
  private readonly cloudGroup = new THREE.Group();

  private readonly earthMaterial: THREE.MeshStandardMaterial;
  private readonly cloudMaterial: THREE.MeshStandardMaterial;
  private readonly atmosphereMaterial: THREE.ShaderMaterial;

  private readonly labelRenderer = new CSS2DRenderer();

  private readonly cameraSunDirection = new THREE.Vector3(
    0.7,
    0.25,
    0.67,
  ).normalize();
  private readonly sunDirection = new THREE.Vector3(
    0.85,
    0.32,
    0.55,
  ).normalize();
  private readonly sunDirectionView = new THREE.Vector3();
  private readonly sunLight = new THREE.DirectionalLight(0xfff6ec, 3.4);
  private readonly fillLight = new THREE.HemisphereLight(
    0x2c4266,
    0x060a12,
    0.35,
  );
  private readonly dataAmbientLight = new THREE.AmbientLight(0x9bbbe8, 0);
  private readonly disposables: Array<{ dispose: () => void }> = [];
  private readonly raycaster = new THREE.Raycaster();
  private readonly pointer = new THREE.Vector2();
  private readonly originalReleasePointerCapture: (pointerId: number) => void;
  private earthMesh: THREE.Mesh | null = null;

  private frame = 0;
  private lastTime = 0;
  private running = false;
  private readonly spinSpeed: number;
  private readonly reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  private resizeObserver: ResizeObserver;
  /** Ideal camera distance for the current viewport, recomputed on resize. */
  private idealDistance = 6.4;
  private userZoomed = false;
  private focusAnimation: {
    startedAt: number;
    duration: number;
    from: number;
    to: number;
    resolve: () => void;
    restoreAutoRotate: boolean;
  } | null = null;

  constructor(options: EarthSceneOptions) {
    this.options = options;
    this.canvas = options.canvas;
    this.spinSpeed = options.spinSpeed ?? 0.045;

    // OrbitControls releases the pointer unconditionally on pointerup. A
    // cancelled gesture (or a hot reload) may already have lost the capture.
    // Keep the control interaction, but make that cleanup operation harmless.
    this.originalReleasePointerCapture =
      options.canvas.releasePointerCapture.bind(options.canvas);
    options.canvas.releasePointerCapture = (pointerId: number) => {
      if (options.canvas.hasPointerCapture(pointerId)) {
        this.originalReleasePointerCapture(pointerId);
      }
    };

    this.renderer = new THREE.WebGLRenderer({
      canvas: options.canvas,
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
    });

    const capa = this.labelRenderer.domElement;
    capa.style.position = "absolute";
    capa.style.inset = "0";
    capa.style.pointerEvents = "none";
    options.canvas.parentElement?.appendChild(capa);

    this.renderer.setSize(
      options.canvas.clientWidth,
      options.canvas.clientHeight,
      false,
    );
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    // The canvas is opaque and matches the page background exactly, so the
    // additive glow and the stars blend into the layout without a seam.
    this.renderer.setClearColor(0x0b1220, 1);

    this.scene = new THREE.Scene();
    this.scene.environment = createSpaceEnvironment();
    this.scene.environmentIntensity = 0.45;

    this.camera = new THREE.PerspectiveCamera(
      36,
      options.canvas.clientWidth / Math.max(options.canvas.clientHeight, 1),
      0.1,
      5000,
    );
    this.camera.position.set(0, 0.55, 6.4);
    this.scene.add(this.camera);

    this.controls = new OrbitControls(this.camera, options.canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.enablePan = false;
    this.controls.rotateSpeed = 0.55;
    this.controls.zoomSpeed = 0.7;
    this.controls.minDistance = 2.2;
    this.controls.maxDistance = 14;
    this.controls.autoRotate = options.autoRotate ?? !this.reduceMotion;
    this.controls.autoRotateSpeed = 0.35;

    this.earthMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.82,
      metalness: 0,
      roughnessMap: null,
      normalMap: null,
      normalScale: new THREE.Vector2(0.2, 0.2),
      emissive: 0xffffff,
      emissiveIntensity: 1,
      envMapIntensity: 0.55,
    });
    this.patchNightLights(this.earthMaterial);

    this.cloudMaterial = new THREE.MeshStandardMaterial({
      color: 0xf4f8ff,
      transparent: true,
      opacity: 0.76,
      roughness: 1,
      metalness: 0,
      depthWrite: false,
      alphaTest: 0.015,
    });

    this.atmosphereMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: new THREE.Color(0x5f9bf0) },
        uSunDirection: { value: this.sunDirection.clone() },
        uPlanetRadius: { value: PLANET_RADIUS },
        uAtmosphereRadius: { value: ATMOSPHERE_RADIUS },
        uDensity: { value: 2.1 },
        uSunIntensity: { value: 0.95 },
      },
      vertexShader: /* glsl */ `
        varying vec3 vWorldPosition;

        void main() {
          vec4 worldPosition = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPosition.xyz;
          gl_Position = projectionMatrix * viewMatrix * worldPosition;
        }
      `,
      fragmentShader: /* glsl */ `
        uniform vec3 uColor;
        uniform vec3 uSunDirection;
        uniform float uPlanetRadius;
        uniform float uAtmosphereRadius;
        uniform float uDensity;
        uniform float uSunIntensity;

        varying vec3 vWorldPosition;

        void main() {
          vec3 rayOrigin = cameraPosition;
          vec3 rayDirection = normalize(vWorldPosition - rayOrigin);

          // Distance from the ray to the planet centre.
          float b = dot(rayOrigin, rayDirection);
          float c = dot(rayOrigin, rayOrigin) - uAtmosphereRadius * uAtmosphereRadius;
          float discriminant = b * b - c;
          if (discriminant < 0.0) discard;

          float root = sqrt(discriminant);
          float atmosphereStart = -b - root;
          float atmosphereEnd = -b + root;

          // Walk the ray until it hits the planet (if it does).
          float planetDiscriminant =
            b * b - (dot(rayOrigin, rayOrigin) - uPlanetRadius * uPlanetRadius);
          if (planetDiscriminant > 0.0) {
            atmosphereEnd = min(atmosphereEnd, -b + sqrt(planetDiscriminant));
          }
          atmosphereEnd = max(atmosphereEnd, atmosphereStart);

          // Integrate the density along the segment of the ray that is inside
          // the atmosphere. This is what gives the halo its soft falloff
          // instead of a hard silhouette.
          const int STEPS = 12;
          float stepLength = (atmosphereEnd - atmosphereStart) / float(STEPS);
          float opticalDepth = 0.0;
          float litDepth = 0.0;

          for (int i = 0; i < STEPS; i++) {
            float t = atmosphereStart + stepLength * (float(i) + 0.5);
            vec3 point = rayOrigin + rayDirection * t;

            float altitude = (length(point) - uPlanetRadius) /
                             (uAtmosphereRadius - uPlanetRadius);
            float density = exp(-max(altitude, 0.0) * 5.5);

            // Is the sample point in the planet's shadow?
            float sunlight = smoothstep(-0.18, 0.28, dot(normalize(point), uSunDirection));

            opticalDepth += density * stepLength;
            litDepth += density * stepLength * sunlight;
          }

          float alpha = 1.0 - exp(-opticalDepth * uDensity);
          float sunlit = litDepth / max(opticalDepth, 0.0001);

          // Warm glow towards the terminator, cool blue everywhere else.
          vec3 twilight = vec3(1.0, 0.66, 0.45);
          vec3 color = mix(uColor * 0.4, uColor, sunlit);
          color = mix(color, twilight, (1.0 - sunlit) * 0.16);

          gl_FragColor = vec4(color * alpha * uSunIntensity, alpha);
        }
      `,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true,
      depthWrite: false,
    });

    this.buildScene();
    this.setDataMode(options.dataMode ?? false);

    this.handleResize = this.handleResize.bind(this);
    this.handleVisibility = this.handleVisibility.bind(this);
    this.handlePointerMove = this.handlePointerMove.bind(this);
    this.handlePointerLeave = this.handlePointerLeave.bind(this);
    this.tick = this.tick.bind(this);
    this.handleControlStart = this.handleControlStart.bind(this);
    this.controls.addEventListener("start", this.handleControlStart);

    window.addEventListener("resize", this.handleResize);
    document.addEventListener("visibilitychange", this.handleVisibility);
    options.canvas.addEventListener("pointermove", this.handlePointerMove);
    options.canvas.addEventListener("pointerleave", this.handlePointerLeave);
    this.resizeObserver = new ResizeObserver(this.handleResize);
    this.resizeObserver.observe(options.canvas);

    this.lastTime = performance.now();
    this.running = true;
    this.frame = requestAnimationFrame(this.tick);

    if (import.meta.env.DEV) {
      const debugWindow = window as unknown as {
        __earth?: EarthScene;
        __THREE?: typeof THREE;
      };
      debugWindow.__earth = this;
      debugWindow.__THREE = THREE;
    }
  }

  private buildScene() {
    // --- lighting -----------------------------------------------------------
    this.sunLight.position.copy(this.sunDirection).multiplyScalar(100);
    this.scene.add(this.sunLight);
    this.disposables.push(this.sunLight);

    // subtle blue bounce so the night side never turns into a black hole
    this.scene.add(this.fillLight);
    this.scene.add(this.dataAmbientLight);
    this.disposables.push(this.fillLight, this.dataAmbientLight);

    // --- planet -------------------------------------------------------------
    this.tiltGroup.rotation.z = AXIAL_TILT;
    this.tiltGroup.add(this.spinGroup);
    this.scene.add(this.tiltGroup);

    const geometry = new THREE.SphereGeometry(PLANET_RADIUS, 160, 96);
    this.disposables.push(geometry);

    const earth = new THREE.Mesh(geometry, this.earthMaterial);
    this.spinGroup.add(earth);
    this.earthMesh = earth;

    const cloudGeometry = new THREE.SphereGeometry(
      PLANET_RADIUS * 1.008,
      96,
      64,
    );
    this.disposables.push(cloudGeometry);
    const clouds = new THREE.Mesh(cloudGeometry, this.cloudMaterial);
    this.cloudGroup.add(clouds);
    this.spinGroup.add(this.cloudGroup);

    const atmosphereGeometry = new THREE.SphereGeometry(
      ATMOSPHERE_RADIUS,
      96,
      64,
    );
    this.disposables.push(atmosphereGeometry);
    const atmosphere = new THREE.Mesh(
      atmosphereGeometry,
      this.atmosphereMaterial,
    );
    this.spinGroup.add(atmosphere);

    // --- star field ---------------------------------------------------------
    this.scene.add(this.createStarField());

    // --- background halo ---------------------------------------------------
    // Lives in camera space so it always sits right behind the planet and
    // fades out before reaching the edges of the canvas.
    const halo = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: createRadialGlow(),
        color: 0x2f5f9e,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        depthTest: false,
      }),
    );
    halo.position.set(0, 0, -7);
    halo.scale.set(7, 7, 1);
    halo.renderOrder = -10;
    this.camera.add(halo);
    this.disposables.push(halo.material);
  }

  private createStarField(): THREE.Points {
    const count = 4200;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    const color = new THREE.Color();

    for (let i = 0; i < count; i++) {
      // uniform distribution over the sphere
      const u = Math.random() * 2 - 1;
      const theta = Math.random() * Math.PI * 2;
      const radius = 600 + Math.random() * 900;
      const ring = Math.sqrt(1 - u * u);

      positions[i * 3] = radius * ring * Math.cos(theta);
      positions[i * 3 + 1] = radius * u;
      positions[i * 3 + 2] = radius * ring * Math.sin(theta);

      // mostly white with a few warm/cool outliers, like a real sky
      const tone = Math.random();
      if (tone > 0.93) color.setHSL(0.08, 0.55, 0.72);
      else if (tone > 0.86) color.setHSL(0.58, 0.45, 0.78);
      else color.setHSL(0.6, 0.12, 0.85 + Math.random() * 0.15);

      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    this.disposables.push(geometry);

    const sprite = createStarSprite();
    this.disposables.push(sprite);

    const material = new THREE.PointsMaterial({
      size: 2.4,
      sizeAttenuation: false,
      map: sprite,
      transparent: true,
      depthWrite: false,
      vertexColors: true,
      blending: THREE.AdditiveBlending,
    });
    this.disposables.push(material);

    const stars = new THREE.Points(geometry, material);
    stars.frustumCulled = false;
    return stars;
  }

  /**
   * Patches the standard material so the city lights only glow on the night
   * side of the planet (the terminator is computed from the sun direction).
   */
  private patchNightLights(material: THREE.MeshStandardMaterial) {
    material.onBeforeCompile = (shader) => {
      shader.uniforms.uSunDirection = { value: new THREE.Vector3() };
      shader.fragmentShader = shader.fragmentShader
        .replace(
          "#include <common>",
          "#include <common>\nuniform vec3 uSunDirection;",
        )
        .replace(
          "#include <emissivemap_fragment>",
          /* glsl */ `#include <emissivemap_fragment>
            float sunAmount = clamp(dot(normalize(vNormal), uSunDirection), -1.0, 1.0);
            float nightFactor = 1.0 - smoothstep(-0.18, 0.12, sunAmount);
            totalEmissiveRadiance *= nightFactor;
          `,
        );
      material.userData.shader = shader;
    };
    material.customProgramCacheKey = () => "earth-night-lights";
  }

  /** Moves the planet horizontally inside the canvas (0 = centred). */
  setHorizontalOffset(offset: number) {
    this.options.horizontalOffset = offset;
    this.handleResize();
  }

  /** Punto de enganche para capas visuales que deben girar con la superficie. */
  getOverlayRoot(): THREE.Group {
    return this.spinGroup;
  }

  /**
   * Gira la superficie hasta que un punto geográfico quede frente a la cámara.
   * La animación se resuelve en tick() para no crear un segundo reloj.
   */
  focusOn(lat: number, lon: number, duration: number): Promise<void> {
    this.cancelFocus();

    const point = new THREE.Vector3(
      Math.cos(THREE.MathUtils.degToRad(lat)) *
        Math.cos(THREE.MathUtils.degToRad(lon)),
      Math.sin(THREE.MathUtils.degToRad(lat)),
      -Math.cos(THREE.MathUtils.degToRad(lat)) *
        Math.sin(THREE.MathUtils.degToRad(lon)),
    );
    point.applyAxisAngle(new THREE.Vector3(0, 0, 1), AXIAL_TILT);

    // El eje Y rota la superficie. Solo necesitamos igualar el rumbo horizontal
    // del punto con el rumbo de la cámara; el ángulo más corto evita vueltas.
    const destino = Math.atan2(-point.x, point.z);
    const actual = this.spinGroup.rotation.y;
    const delta =
      THREE.MathUtils.euclideanModulo(destino - actual + Math.PI, Math.PI * 2) -
      Math.PI;
    const to = actual + delta;
    const restoreAutoRotate = this.controls.autoRotate;
    this.controls.autoRotate = false;

    if (this.reduceMotion || duration <= 0) {
      this.spinGroup.rotation.y = to;
      this.controls.autoRotate = restoreAutoRotate;
      return Promise.resolve();
    }

    return new Promise<void>((resolve) => {
      this.focusAnimation = {
        startedAt: performance.now(),
        duration,
        from: actual,
        to,
        resolve,
        restoreAutoRotate,
      };
    });
  }

  /** Cancela un enfoque activo y deja la escena lista para otra interacción. */
  cancelFocus() {
    const animation = this.focusAnimation;
    if (!animation) return;
    this.focusAnimation = null;
    this.controls.autoRotate = animation.restoreAutoRotate;
    animation.resolve();
  }

  setAutoRotate(enabled: boolean) {
    this.controls.autoRotate = enabled && !this.reduceMotion;
  }

  /** Downloads the NASA imagery and applies it to the materials. */
  async load(): Promise<void> {
    const loader = new TextureLoader(this.options.onProgress);

    const [day, night, specular, normal, cloudsImage] = await Promise.all([
      loader.load(TEXTURES.day, { srgb: true }),
      loader.load(TEXTURES.night, { srgb: true }),
      loader.load(TEXTURES.specular),
      loader.load(TEXTURES.normal),
      loader.loadImage(TEXTURES.clouds),
    ]);

    this.disposables.push(day, night, normal);

    this.earthMaterial.map = day;
    this.earthMaterial.emissiveMap = night;
    this.earthMaterial.emissiveIntensity = 1.25;
    const roughness = createRoughnessFromSpecular(
      specular.image as HTMLImageElement,
    );
    this.earthMaterial.roughnessMap = roughness;
    this.disposables.push(roughness);
    specular.dispose();
    this.earthMaterial.normalMap = normal;
    this.earthMaterial.needsUpdate = true;

    const clouds = createCloudTexture(cloudsImage);
    this.disposables.push(clouds);
    this.cloudMaterial.map = clouds;
    this.cloudMaterial.needsUpdate = true;
  }

  private handleResize() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    if (width === 0 || height === 0) return;

    this.camera.aspect = width / height;

    // Frame the planet so it always fits, whatever the viewport shape is.
    const fov = THREE.MathUtils.degToRad(this.camera.fov);
    const visibleHeight = Math.max(
      4.2,
      3.1 / Math.max(this.camera.aspect, 0.001),
    );
    this.idealDistance = visibleHeight / (2 * Math.tan(fov / 2));

    if (!this.userZoomed) {
      const direction = this.camera.position.clone().normalize();
      this.camera.position.copy(direction.multiplyScalar(this.idealDistance));
    }

    // Push the planet off-centre so the copy has room on the left.
    const offset = this.options.horizontalOffset ?? 0;
    if (offset !== 0) {
      this.camera.setViewOffset(
        width,
        height,
        -offset * width,
        0,
        width,
        height,
      );
    } else {
      this.camera.clearViewOffset();
    }

    this.camera.updateProjectionMatrix();
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(width, height, false);
    this.labelRenderer.setSize(width, height);
  }

  private handleVisibility() {
    if (document.hidden) {
      this.running = false;
      cancelAnimationFrame(this.frame);
    } else if (!this.running) {
      this.running = true;
      this.lastTime = performance.now();
      this.frame = requestAnimationFrame(this.tick);
    }
  }

  /** Uses camera-relative sunlight for exploration or even ambient light for data. */
  setDataMode(enabled: boolean) {
    this.fillLight.intensity = enabled ? 1.05 : 0.35;
    this.dataAmbientLight.intensity = enabled ? 0.72 : 0;
    this.sunLight.intensity = enabled ? 2.2 : 3.4;
  }

  private handleControlStart() {
    this.userZoomed = true;
    this.cancelFocus();
    this.options.onInteraction?.();
  }

  /**
   * Turns the pointer position into geographic coordinates. The globe keeps
   * rotating under the cursor, so the readout follows whatever is under the
   * pointer right now.
   */
  private handlePointerMove(event: PointerEvent) {
    if (!this.earthMesh || !this.options.onTelemetry) return;

    const rect = this.canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hit = this.raycaster.intersectObject(this.earthMesh, false)[0];
    if (!hit) {
      this.options.onTelemetry(null);
      return;
    }

    const local = this.earthMesh.worldToLocal(hit.point.clone()).normalize();
    const lat =
      90 - Math.acos(THREE.MathUtils.clamp(local.y, -1, 1)) * (180 / Math.PI);
    const lon = Math.atan2(-local.z, local.x) * (180 / Math.PI);

    this.options.onTelemetry({ lat, lon });
  }

  private handlePointerLeave() {
    this.options.onTelemetry?.(null);
  }

  private tick(now: number) {
    if (!this.running) return;

    const delta = Math.min((now - this.lastTime) / 1000, 0.1);
    this.lastTime = now;

    const focus = this.focusAnimation;
    if (focus) {
      const progress = THREE.MathUtils.clamp(
        (now - focus.startedAt) / focus.duration,
        0,
        1,
      );
      const eased = progress * progress * (3 - 2 * progress);
      this.spinGroup.rotation.y = THREE.MathUtils.lerp(
        focus.from,
        focus.to,
        eased,
      );
      if (progress >= 1) {
        this.focusAnimation = null;
        this.controls.autoRotate = focus.restoreAutoRotate;
        focus.resolve();
      }
    } else {
      this.spinGroup.rotation.y += this.spinSpeed * delta;
    }
    // clouds drift a little faster than the solid surface
    this.cloudGroup.rotation.y += this.spinSpeed * 0.06 * delta;

    this.controls.update();

    // Keep a stable terminator on the visible disk. Data mode adds ambient
    // light so a value never disappears just because it is on the night side.
    this.sunDirection
      .copy(this.cameraSunDirection)
      .transformDirection(this.camera.matrixWorld);
    this.sunLight.position.copy(this.sunDirection).multiplyScalar(100);
    this.sunDirectionView.copy(this.cameraSunDirection);
    this.atmosphereMaterial.uniforms.uSunDirection.value.copy(
      this.sunDirection,
    );
    const shader = this.earthMaterial.userData.shader;
    if (shader) {
      shader.uniforms.uSunDirection.value.copy(this.sunDirectionView);
    }

    this.renderer.render(this.scene, this.camera);
    actualizarVisibilidad(this.camera);
    this.labelRenderer.render(this.scene, this.camera);

    this.frame = requestAnimationFrame(this.tick);
  }

  dispose() {
    this.cancelFocus();
    this.running = false;
    cancelAnimationFrame(this.frame);

    window.removeEventListener("resize", this.handleResize);
    document.removeEventListener("visibilitychange", this.handleVisibility);
    this.canvas.removeEventListener("pointermove", this.handlePointerMove);
    this.canvas.removeEventListener("pointerleave", this.handlePointerLeave);
    this.resizeObserver.disconnect();

    this.labelRenderer.domElement.remove();

    // OrbitControls keeps document-level listeners while a gesture is active.
    // Remove them before disposing the control so an old HMR scene cannot
    // handle a later pointerup with a stale pointer id.
    const activeControls = this.controls as unknown as {
      _onPointerMove?: EventListener;
      _onPointerUp?: EventListener;
      _pointers?: number[];
    };
    if (activeControls._onPointerMove) {
      document.removeEventListener(
        "pointermove",
        activeControls._onPointerMove,
      );
    }
    if (activeControls._onPointerUp) {
      document.removeEventListener("pointerup", activeControls._onPointerUp);
    }
    for (const pointerId of activeControls._pointers ?? []) {
      if (this.canvas.hasPointerCapture(pointerId)) {
        this.originalReleasePointerCapture(pointerId);
      }
    }

    this.controls.dispose();
    this.canvas.releasePointerCapture = this.originalReleasePointerCapture;
    this.controls.removeEventListener("start", this.handleControlStart);
    this.earthMaterial.dispose();
    this.cloudMaterial.dispose();
    this.atmosphereMaterial.dispose();
    this.scene.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (mesh.geometry) mesh.geometry.dispose();
    });
    for (const item of this.disposables) item.dispose();
    this.renderer.dispose();
  }
}
