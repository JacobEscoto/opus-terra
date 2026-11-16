<script lang="ts">
  import { onMount } from "svelte";
  import { EarthScene, type EarthTelemetry } from "../three/earthScene";
  import {
    agregarCapa,
    actualizarColores,
    quitarCapa,
    type CeldaTendencia,
  } from "../three/tendenciaLayer";
  import { quitarEtiquetas } from "../three/etiquetasLayer";
  import { limpiarMapa, pintarMapa } from "../three/mapaLayer";
  import type { PaisGeo } from "../geo/paises";

  type FocusOn = (lat: number, lon: number, duracion: number) => Promise<void>;

  interface PropiedadesComponente {
    /** Fires with the latitude/longitude under the pointer, or null when off-globe. */
    onTelemetry?: (telemetry: EarthTelemetry | null) => void;
    /** Pulsación simple sobre un punto del planeta. */
    onSelect?: (lat: number, lon: number) => void;
    /** Territorios que se dibujan como fronteras. */
    geo?: PaisGeo[];
    /** País resaltado. */
    seleccion?: PaisGeo | null;
    /** Texture download progress, 0 → 1. */
    onProgress?: (ratio: number) => void;
    onReady?: (
      focusOn: FocusOn,
      cancelFocus: () => void,
      setAutoRotate: (enabled: boolean) => void,
    ) => void;
    onInteraction?: () => void;
    /** How far off-centre the planet sits, as a fraction of the canvas width. */
    horizontalOffset?: number;
    /** Keeps the whole globe readable when a data layer is active. */
    dataMode?: boolean;
    celdas?: CeldaTendencia[];
    capaVisible?: boolean;
    anio?: number;
    anios?: number[];
    escalaMaxima?: number;
  }

  let {
    onTelemetry,
    onSelect,
    onProgress,
    onReady,
    onInteraction,
    horizontalOffset = 0,
    dataMode = false,
    celdas = [],
    capaVisible = true,
    anio = 0,
    anios = [],
    escalaMaxima = 1,
    geo = [],
    seleccion = null,
  }: PropiedadesComponente = $props();

  let canvas: HTMLCanvasElement;
  let status = $state<"loading" | "ready" | "error">("loading");
  let sceneRef: EarthScene | null = null;
  /** Avisa a los efectos de que ya existe una escena a la que enganchar capas. */
  let escenaPreparada = $state(false);

  function acercar() {
    sceneRef?.zoomBy(0.8);
  }

  function alejar() {
    sceneRef?.zoomBy(1.25);
  }

  function restablecerVista() {
    sceneRef?.resetView();
  }

  function actualizarCapa() {
    const scene = sceneRef;
    if (!scene || !capaVisible) {
      quitarCapa();
      return;
    }
    try {
      agregarCapa(scene.getOverlayRoot(), celdas, anios, escalaMaxima);
    } catch (error: unknown) {
      console.error(
        "[tendenciaLayer] No se pudieron crear los marcadores.",
        error,
      );
      quitarCapa();
    }
  }

  onMount(() => {
    const scene = new EarthScene({
      canvas,
      onTelemetry,
      onSelect,
      onProgress,
      onInteraction,
      horizontalOffset,
      dataMode,
    });
    sceneRef = scene;
    escenaPreparada = true;
    actualizarCapa();

    scene
      .load()
      .then(() => {
        status = "ready";
        onReady?.(
          scene.focusOn.bind(scene),
          scene.cancelFocus.bind(scene),
          scene.setAutoRotate.bind(scene),
        );
      })
      .catch((error: unknown) => {
        console.error(error);
        status = "error";
      });

    return () => {
      sceneRef = null;
      escenaPreparada = false;
      quitarCapa();
      limpiarMapa();
      quitarEtiquetas();
      scene.dispose();
    };
  });

  $effect(() => {
    sceneRef?.setHorizontalOffset(horizontalOffset);
    sceneRef?.setDataMode(dataMode);
  });

  $effect(() => {
    actualizarCapa();
  });

  $effect(() => {
    const anioActivo = anio;
    if (sceneRef && capaVisible) actualizarColores(anioActivo);
  });

  // Fronteras y país seleccionado: se repintan al llegar el GeoJSON o al
  // cambiar la selección, sin tocar la capa de tendencias.
  $effect(() => {
    if (!escenaPreparada) return;
    const scene = sceneRef;
    if (!scene) return;
    pintarMapa(scene.getOverlayRoot(), geo, seleccion);
  });
</script>

<div class="globe">
  <canvas
    bind:this={canvas}
    aria-label="Globo terráqueo 3D del planeta Tierra"
    aria-describedby="globo-descripcion"
  ></canvas>
  <span id="globo-descripcion" class="sr-only">
    Pulsa el territorio de un país para ver su nombre y si tiene datos
    ambientales disponibles.
  </span>

  {#if status !== "ready"}
    <div class="boot" role="status" aria-live="polite">
      <div class="boot__rule"><span></span></div>
      <p class="boot__label">
        {status === "error"
          ? "No se pudieron preparar los datos del planeta"
          : "Preparando el planeta…"}
      </p>
    </div>
  {/if}

  <div class="globe-tools" aria-label="Controles del globo">
    <button type="button" onclick={acercar} aria-label="Acercar el globo"
      >+</button
    >
    <button type="button" onclick={alejar} aria-label="Alejar el globo"
      >−</button
    >
    <button
      type="button"
      class="globe-tools__reset"
      onclick={restablecerVista}
      aria-label="Restablecer vista del globo"
    >
      <span>Restablecer vista</span>
    </button>
  </div>
</div>

<style>
  .globe {
    position: fixed;
    inset: 0;
    z-index: 0;
  }

  canvas {
    display: block;
    width: 100%;
    height: 100%;
    touch-action: none;
    cursor: grab;
  }

  canvas:active {
    cursor: grabbing;
  }

  .globe-tools {
    position: absolute;
    right: 42px;
    bottom: 34px;
    z-index: 1;
    display: grid;
    grid-template-columns: 38px 38px;
    gap: 1px;
    pointer-events: auto;
  }

  .globe-tools button {
    min-height: 38px;
    border: 1px solid rgba(237, 243, 250, 0.2);
    background: rgba(11, 18, 32, 0.76);
    color: var(--ink);
    font: 20px/1 var(--sans);
    backdrop-filter: blur(8px);
  }

  .globe-tools button:hover,
  .globe-tools button:focus-visible {
    border-color: var(--amber);
    color: var(--amber);
  }

  .globe-tools__reset {
    grid-column: 1 / -1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    font: 9px var(--mono) !important;
    letter-spacing: 0.03em;
  }

  .boot {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    display: grid;
    justify-items: center;
    gap: 0.9rem;
    pointer-events: none;
  }

  .boot__rule {
    width: 160px;
    height: 1px;
    background: rgba(243, 247, 252, 0.14);
    overflow: hidden;
  }

  .boot__rule span {
    display: block;
    height: 100%;
    width: 40%;
    background: rgba(243, 247, 252, 0.65);
    animation: sweep 1.4s cubic-bezier(0.65, 0, 0.35, 1) infinite;
  }

  .boot__label {
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    color: var(--ink-3);
    text-align: center;
  }

  @keyframes sweep {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(250%);
    }
  }

  @media (max-width: 650px) {
    .globe-tools {
      right: 17px;
      bottom: 20px;
    }
  }
</style>
