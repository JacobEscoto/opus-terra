<script lang="ts">
  import type { ParRegiones, ResultadoPixel } from '../types/analysis'
  import { unidadLegible } from '../data/capa'
  import TrendMark from './TrendMark.svelte'

  interface Props {
    pares: ParRegiones[]
    /** Identificador del par resaltado (null = ninguno). */
    seleccionadoId: string | null
    onSeleccionar: (id: string) => void
    resultados: ResultadoPixel[]
    unidad: string
    anios: number
  }

  let { pares, seleccionadoId, onSeleccionar, resultados, unidad, anios }: Props = $props()
  let cantidadVisible = $state(80)
  let referenciaPares: ParRegiones[] | null = null

  $effect(() => {
    if (pares !== referenciaPares) {
      referenciaPares = pares
      cantidadVisible = 80
    }
  })

  const pendientes = $derived(
    new Map(resultados.map((pixel) => [`${pixel.lat}:${pixel.lon}`, pixel.sen_unidad_por_anio])),
  )
  const paresVisibles = $derived(pares.slice(0, cantidadVisible))

  function pendienteDe(region: ParRegiones['region_a']): number | null {
    return pendientes.get(`${region.lat}:${region.lon}`) ?? null
  }

  function cambio(region: ParRegiones['region_a']): string {
    const pendiente = pendienteDe(region)
    if (pendiente === null) return 'Cambio no disponible'
    const acumulado = pendiente * Math.max(anios - 1, 0)
    return `${acumulado > 0 ? '+' : ''}${acumulado.toFixed(1)} ${unidadLegible(unidad)} en ${anios} años`
  }
</script>

<ul class="pares">
  {#each paresVisibles as par, indice (par.id)}
    <li>
      <button
        type="button"
        class="par"
        class:par--activo={par.id === seleccionadoId}
        aria-pressed={par.id === seleccionadoId}
        onclick={() => onSeleccionar(par.id)}
      >
        <span class="par__num" aria-hidden="true">{String(indice + 1).padStart(2, '0')}</span>
        <span class="par__cuerpo">
          <span class="par__fila">
            <span class="par__nombre">{par.region_a.nombre}</span>
            <TrendMark tendencia={par.region_a.tendencia} significativa={par.region_a.significativa} conTexto />
            <span class="par__cambio">{cambio(par.region_a)}</span>
          </span>
          <span class="par__fila">
            <span class="par__nombre">{par.region_b.nombre}</span>
            <TrendMark tendencia={par.region_b.tendencia} significativa={par.region_b.significativa} conTexto />
            <span class="par__cambio">{cambio(par.region_b)}</span>
          </span>
        </span>
      </button>
    </li>
  {/each}
</ul>

{#if cantidadVisible < pares.length}
  <div class="pares__mas">
    <p>Mostrando {cantidadVisible} de {pares.length} comparaciones.</p>
    <button type="button" onclick={() => (cantidadVisible += 80)}>Mostrar más</button>
  </div>
{/if}

<style>
  .pares {
    margin: 0;
    padding: 0;
    list-style: none;
    border-top: 1px solid var(--hairline);
  }

  .par {
    position: relative;
    display: flex;
    gap: 12px;
    align-items: flex-start;
    width: 100%;
    padding: 13px 4px 13px 10px;
    border-bottom: 1px solid var(--hairline);
    background: transparent;
    text-align: left;
    transition: background 0.15s ease;
  }

  .par::before {
    content: '';
    position: absolute;
    left: -1px;
    top: 0;
    bottom: -1px;
    width: 2px;
    background: transparent;
    transition: background 0.15s ease;
  }

  .par:hover {
    background: rgba(120, 185, 255, 0.05);
  }

  .par--activo {
    background: rgba(255, 181, 107, 0.05);
  }

  .par--activo::before {
    background: var(--amber);
  }

  .par__num {
    padding-top: 3px;
    font: 10px var(--mono);
    color: var(--faint);
  }

  .par__cuerpo {
    display: grid;
    gap: 7px;
    min-width: 0;
    flex: 1;
  }

  .par__fila {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    min-width: 0;
  }

  .par__nombre {
    min-width: 0;
    overflow: hidden;
    font-size: 13px;
    color: var(--ink);
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1 1 auto;
  }

  .par__cambio {
    width: 100%;
    font: 11px var(--mono);
    color: var(--muted);
    white-space: nowrap;
  }

  .pares__mas {
    display: grid;
    gap: 8px;
    padding: 14px 4px;
    color: var(--muted);
    font: 10px var(--mono);
  }

  .pares__mas p { margin: 0; }

  .pares__mas button {
    justify-self: start;
    padding: 7px 10px;
    border: 1px solid var(--hairline);
    background: transparent;
    color: var(--ink);
    font: inherit;
  }
</style>
