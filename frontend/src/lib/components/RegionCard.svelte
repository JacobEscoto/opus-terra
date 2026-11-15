<script lang="ts">
  import type { RegionAnalizada } from '../types/analysis'
  import { unidadLegible } from '../data/capa'
  import TrendMark from './TrendMark.svelte'

  interface Props {
    region: RegionAnalizada
    /** Etiqueta del lado dentro del par ("Región A" / "Región B"). */
    etiqueta: string
    /** Unidad de la variable, viene del contrato. */
    unidad: string
    /** Contexto de la OMS, viene del contrato (sin diagnósticos). */
    contextoOms: string
  }

  let { region, etiqueta, unidad, contextoOms }: Props = $props()

  function cambioFormateado(valor: number): string {
    return `${valor > 0 ? '+' : ''}${valor.toFixed(1)} %`
  }

  /** Coordenadas en formato de bitácora: 22.9° S / 14.5° O. */
  function coordenadas(valor: RegionAnalizada): string {
    const lat = `${Math.abs(valor.lat).toFixed(1)}° ${valor.lat < 0 ? 'S' : 'N'}`
    const lon = `${Math.abs(valor.lon).toFixed(1)}° ${valor.lon < 0 ? 'O' : 'E'}`
    return `${lat} / ${lon}`
  }
</script>

<!-- Tarjeta de una región: tendencia + significancia + lectura numérica +
     explicación y contexto de la OMS. Todo proviene del JSON del contrato. -->
<article class="region" class:region--neutra={!region.significativa}>
  <header class="region__head">
    <span class="region__lado">{etiqueta}</span>
    <TrendMark tendencia={region.tendencia} significativa={region.significativa} conTexto />
  </header>

  <h3 class="region__nombre">{region.nombre}</h3>
  <p class="region__coords">{coordenadas(region)}</p>

  <p class="region__cambio">
    <strong>{cambioFormateado(region.cambio_porcentual)}</strong>
    <span>{unidadLegible(unidad)}</span>
  </p>

  {#if region.significativa}
    <span class="region__insignia region__insignia--ok">Cambio significativo</span>
  {:else}
    <span class="insignia-neutra">Cambio no significativo</span>
  {/if}

  <p class="region__explicacion">{region.explicacion}</p>

  <aside class="region__oms" role="note" aria-label="Contexto de la OMS">
    <span class="region__oms-etiqueta">Contexto OMS</span>
    <p>{contextoOms}</p>
  </aside>
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

  .region__lado {
    padding: 2px 7px;
    border: 1px solid var(--hairline);
    font: 9px/1.5 var(--mono);
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--faint);
  }

  .region__nombre {
    font-size: 15px;
    font-weight: 500;
    letter-spacing: -0.02em;
    color: var(--ink);
  }

  .region__coords {
    font: 10px var(--mono);
    color: var(--faint);
  }

  .region__cambio {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  /* Número de lectura grande en mono, como la pantalla de un instrumento. */
  .region__cambio strong {
    font: 500 21px var(--mono);
    color: var(--ink);
  }

  .region__cambio span {
    font: 10px var(--mono);
    color: var(--faint);
  }

  .region__insignia {
    justify-self: start;
    padding: 3px 8px;
    font: 9px/1.4 var(--mono);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .region__insignia--ok {
    border: 1px solid var(--hairline);
    color: var(--muted);
  }

  .region__explicacion {
    font-size: 13px;
    line-height: 1.65;
    color: var(--muted);
  }

  .region__oms {
    display: grid;
    gap: 5px;
    padding: 10px 0 0 11px;
    border-left: 2px solid var(--amber);
  }

  .region__oms-etiqueta {
    font: 10px var(--mono);
    letter-spacing: 0.08em;
    color: var(--amber);
  }

  .region__oms p {
    font: 10px/1.7 var(--mono);
    color: var(--faint);
  }
</style>
