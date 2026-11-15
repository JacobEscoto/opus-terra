<script lang="ts">
  import type { ParRegiones } from '../types/analysis'
  import TrendMark from './TrendMark.svelte'

  interface Props {
    pares: ParRegiones[]
    /** Identificador del par resaltado (null = ninguno). */
    seleccionadoId: string | null
    onSeleccionar: (id: string) => void
  }

  let { pares, seleccionadoId, onSeleccionar }: Props = $props()

  function num(valor: number): string {
    return `${valor > 0 ? '+' : ''}${valor.toFixed(1)}`
  }
</script>

<!-- Lista de pares: filas separadas por hairlines, con riel ámbar en la
     activa. Los pares sin señal significativa llevan insignia rayada. -->
<ul class="pares">
  {#each pares as par, indice (par.id)}
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
            <TrendMark tendencia={par.region_a.tendencia} significativa={par.region_a.significativa} />
            <span class="par__nombre">{par.region_a.nombre}</span>
            {#if !par.region_a.significativa}
              <span class="insignia-neutra">No significativa</span>
            {/if}
          </span>
          <span class="par__fila">
            <TrendMark tendencia={par.region_b.tendencia} significativa={par.region_b.significativa} />
            <span class="par__nombre">{par.region_b.nombre}</span>
            {#if !par.region_b.significativa}
              <span class="insignia-neutra">No significativa</span>
            {/if}
          </span>
        </span>
        <span class="par__cambios">
          <span class="par__cambio">{num(par.region_a.cambio_porcentual)} %</span>
          <span class="par__cambio">{num(par.region_b.cambio_porcentual)} %</span>
        </span>
      </button>
    </li>
  {/each}
</ul>

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
    font-size: 13px;
    color: var(--ink);
  }

  /* Lecturas alineadas a la derecha, como en un panel de instrumento: una
     por región, en el mismo orden que las filas. */
  .par__cambios {
    display: grid;
    gap: 7px;
    padding-top: 1px;
    text-align: right;
  }

  .par__cambio {
    font: 500 11px var(--mono);
    color: var(--muted);
    white-space: nowrap;
  }
</style>
