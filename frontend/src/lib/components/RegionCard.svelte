<script lang="ts">
  import type { RegionAnalizada } from "../types/analysis";
  import { unidadLegible } from "../data/capa";
  import { EXPLICACIONES } from "../data/textos";
  import TrendMark from "./TrendMark.svelte";

  interface PropiedadesComponente {
    region: RegionAnalizada;
    /** Unidad de la variable, viene del contrato. */
    unidad: string;
    /** Pendiente de la zona, para presentar el cambio acumulado. */
    pendiente: number | null;
    /** Número de años mostrados. */
    anios: number;
    onEnfocar?: () => void;
  }

  let {
    region,
    unidad,
    pendiente,
    anios,
    onEnfocar,
  }: PropiedadesComponente = $props();

  function cambioFormateado(): string {
    if (pendiente === null) return "Cambio no disponible";
    const acumulado = pendiente * Math.max(anios - 1, 0);
    const signo = acumulado > 0 ? "+" : "";
    return `${signo}${acumulado.toFixed(1)} ${unidadLegible(unidad)} en ${anios} años`;
  }

</script>

<article class="region" class:region--neutra={!region.significativa}>
  <header class="region__head">
    <h3 class="region__nombre">{region.nombre}</h3>
    {#if region.pais}
      <p class="region__pais">{region.pais}</p>
    {/if}
    <TrendMark
      tendencia={region.tendencia}
      significativa={region.significativa}
      conTexto
    />
  </header>

  <p class="region__cambio">
    <strong>{cambioFormateado()}</strong>
  </p>

  {#if region.significativa}
    <p class="region__explicacion">{EXPLICACIONES.cambioClaro}</p>
  {:else}
    <p class="region__explicacion">Cambio poco claro.</p>
  {/if}
  {#if onEnfocar}
    <button type="button" class="region__focus" onclick={onEnfocar}>
      Enfocar esta zona <span aria-hidden="true">↗</span>
    </button>
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

  .region__pais {
    font: 10px var(--mono);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--amber);
  }

  .region__cambio {
    margin: 0;
  }

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

  .region__focus {
    justify-self: start;
    padding: 6px 0 4px;
    border-bottom: 1px solid var(--hairline);
    background: transparent;
    font: 10px var(--mono);
    color: var(--amber);
  }

  .region__focus:hover,
  .region__focus:focus-visible {
    border-color: var(--amber);
    color: var(--ink);
  }
</style>
