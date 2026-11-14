<script lang="ts">
  import { onMount } from 'svelte'
  import { EarthScene, type EarthTelemetry } from '../three/earthScene'

  interface Props {
    /** Fires with the latitude/longitude under the pointer, or null when off-globe. */
    onTelemetry?: (telemetry: EarthTelemetry | null) => void
    /** Texture download progress, 0 → 1. */
    onProgress?: (ratio: number) => void
    /** How far off-centre the planet sits, as a fraction of the canvas width. */
    horizontalOffset?: number
    /** Keeps the whole globe readable when a data layer is active. */
    dataMode?: boolean
  }

  let { onTelemetry, onProgress, horizontalOffset = 0, dataMode = false }: Props = $props()

  let canvas: HTMLCanvasElement
  let status = $state<'loading' | 'ready' | 'error'>('loading')
  let sceneRef: EarthScene | null = null

  onMount(() => {
    const scene = new EarthScene({
      canvas,
      onTelemetry,
      onProgress,
      horizontalOffset,
      dataMode,
    })
    sceneRef = scene

    scene
      .load()
      .then(() => {
        status = 'ready'
      })
      .catch((error: unknown) => {
        console.error(error)
        status = 'error'
      })

    return () => {
      sceneRef = null
      scene.dispose()
    }
  })

  $effect(() => {
    sceneRef?.setHorizontalOffset(horizontalOffset)
    sceneRef?.setDataMode(dataMode)
  })
</script>

<div class="globe">
  <canvas bind:this={canvas} aria-label="Globo terráqueo 3D del planeta Tierra"></canvas>

  {#if status !== 'ready'}
    <div class="boot" role="status" aria-live="polite">
      <div class="boot__rule"><span></span></div>
      <p class="boot__label">
        {status === 'error' ? 'No se pudieron cargar las texturas del mockup' : 'Cargando texturas del mockup'}
      </p>
    </div>
  {/if}
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
</style>
