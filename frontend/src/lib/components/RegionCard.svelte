<script lang="ts">
  import type { RegionAnalizada } from '../types/analysis'
  import { escalaCelda, unidadLegible } from '../data/capa'
  import { EXPLICACIONES } from '../data/textos'
  import TrendMark from './TrendMark.svelte'

  interface Props {
    region: RegionAnalizada
    /** Unidad de la variable, viene del contrato. */
    unidad: string
    /** Fuente del producto, para mostrar su escala espacial cuando se conoce. */
    fuente: string
    /** Pendiente de la zona, para presentar el cambio acumulado. */
    pendiente: number | null
    /** Número de años mostrados. */
    anios: number
  }

  let { region, unidad, fuente, pendiente, anios }: Props = $props()

  function cambioFormateado(): string {
    if (pendiente === null) return 'Cambio no disponible'
    const acumulado = pendiente * Math.max(anios - 1, 0)
    const signo = acumulado > 0 ? '+' : ''
    return `${signo}${acumulado.toFixed(1)} ${unidadLegible(unidad)} en ${anios} años`
  }

  /** Coordenadas en formato de bitácora: 22.9° S / 14.5° O. */
  function coordenadas(valor: RegionAnalizada): string {
    const lat = `${Math.abs(valor.lat).toFixed(1)}° ${valor.lat < 0 ? 'S' : 'N'}`
    const lon = `${Math.abs(valor.lon).toFixed(1)}° ${valor.lon < 0 ? 'O' : 'E'}`
    return `${lat} / ${lon}`
  }

  const escala = $derived(escalaCelda(fuente))
</script>

<article class="region" class:region--neutra={!region.significativa}>
  <header class="region__head">
    <h3 class="region__nombre">{region.nombre}</h3>
    <TrendMark tendencia={region.tendencia} significativa={region.significativa} conTexto />
  </header>

  <details class="region__detalles">
    <summary>Ver detalles técnicos</summary>
    <p class="region__coords">{coordenadas(region)}</p>
  </details>

  {#if escala}
    <p class="region__escala">Cada zona representa {escala}</p>
  {/if}

  <p class="region__cambio">
    <strong>{cambioFormateado()}</strong>
  </p>

  {#if region.significativa}
    <p class="region__explicacion">{EXPLICACIONES.cambioClaro}</p>
  {:else}
    <p class="region__explicacion">Cambio poco claro.</p>
  {/if}
</article>

<style>
  .region {
    display: grid;
    gap: 10px;
    align-content: start;
    padding: 15px 15px 16px;
    border: 1px solid var(--hairline);
    background: rgba(16, 27, 44, 0.6);
  }

  .region--neutra {
    border-style: dashed;
  }

  .region__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--hairline);
  }

  .region__nombre {
    font-size: 15px;
    font-weight: 500;
    letter-spacing: -0.02em;
    color: var(--ink);
  }

  .region__coords {
    margin-top: 7px;
    font: 10px var(--mono);
    color: var(--faint);
  }

  .region__detalles summary {
    cursor: pointer;
    font: 10px var(--mono);
    color: var(--muted);
  }

  .region__detalles summary:hover,
  .region__detalles summary:focus-visible {
    color: var(--amber);
  }

  .region__escala {
    font: 10px/1.5 var(--mono);
    color: var(--faint);
  }

  .region__cambio { margin: 0; }

  /* Número de lectura grande en mono, como la pantalla de un instrumento. */
  .region__cambio strong {
    font: 500 21px var(--mono);
    color: var(--ink);
  }

  .region__explicacion {
    font-size: 13px;
    line-height: 1.65;
    color: var(--muted);
  }

</style>
