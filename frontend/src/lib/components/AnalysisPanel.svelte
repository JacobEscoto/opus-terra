<script lang="ts">
  import type { EstadoCarga } from '../data/loadAnalysis'
  import type { ParRegiones } from '../types/analysis'
  import Legend from './Legend.svelte'
  import PairList from './PairList.svelte'
  import RegionCard from './RegionCard.svelte'

  interface Props {
    /** Estado de la lectura del JSON (cargando / error / listo). */
    carga: EstadoCarga
    /** Par elegido actualmente, o null para la vista de lista. */
    parSeleccionado: ParRegiones | null
    onSeleccionar: (id: string) => void
    onVolver: () => void
    onReintentar: () => void
  }

  let { carga, parSeleccionado, onSeleccionar, onVolver, onReintentar }: Props = $props()

  const datos = $derived(carga.estado === 'listo' ? carga.datos : null)
</script>

<section class="panel" aria-label="Análisis de tendencias por pares de regiones">
  <header class="panel__head">
    <div class="panel__fila">
      <p class="kicker"><span>02</span>Análisis de tendencias</p>
      {#if datos}
        <span class="panel__mock" title="Los datos provienen del archivo mock.json">
          Datos de prueba / {datos.fuente}
        </span>
      {/if}
    </div>
    <h2>{datos?.nombre_variable ?? '—'}</h2>
    {#if datos}
      <p class="panel__meta">
        {datos.variable}<span class="slash">/</span>{datos.unidad}<span class="slash">/</span>{datos.periodo.inicio}–{datos.periodo.fin}
      </p>    {/if}
  </header>

  {#if carga.estado === 'cargando'}
    <div class="estado" role="status" aria-live="polite">
      <p>Leyendo datos de análisis…</p>
      <div class="estado__barra"><span></span></div>
    </div>
  {:else if carga.estado === 'error'}
    <div class="estado estado--error" role="alert">
      <p>{carga.mensaje}</p>
      <button type="button" class="estado__reintentar" onclick={onReintentar}>Reintentar</button>
    </div>
  {:else if datos && parSeleccionado}
    <div class="detalle">
      <button type="button" class="panel__volver" onclick={onVolver}>← Volver a la lista</button>
      <p class="detalle__intro">
        Dos regiones del mismo par, con su tendencia y su marca de significancia.
      </p>
      <div class="detalle__regiones">
        <RegionCard
          region={parSeleccionado.region_a}
          etiqueta="Región A"
          unidad={datos.unidad}
          contextoOms={datos.contexto_oms}
        />
        <RegionCard
          region={parSeleccionado.region_b}
          etiqueta="Región B"
          unidad={datos.unidad}
          contextoOms={datos.contexto_oms}
        />
      </div>
    </div>
  {:else if datos}
    <div class="panel__cuerpo">
      <Legend />
      <PairList
        pares={datos.pares}
        seleccionadoId={parSeleccionado?.id ?? null}
        onSeleccionar={onSeleccionar}
      />
    </div>
  {/if}
</section>

<style>
  .panel {
    position: relative;
    padding: 18px 20px 20px;
    border: 1px solid var(--hairline);
    background: var(--panel-bg);
    backdrop-filter: blur(10px);
    max-height: calc(100svh - 145px);
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--hairline) transparent;
  }

  /* Esquinas de mira, como en un instrumento óptico: ámbar arriba a la
     izquierda, hairline abajo a la derecha. */
  .panel::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    width: 16px;
    height: 16px;
    border-top: 1px solid var(--amber);
    border-left: 1px solid var(--amber);
  }

  .panel::after {
    content: '';
    position: absolute;
    bottom: -1px;
    right: -1px;
    width: 16px;
    height: 16px;
    border-bottom: 1px solid var(--hairline);
    border-right: 1px solid var(--hairline);
  }

  .panel::-webkit-scrollbar {
    width: 8px;
  }

  .panel::-webkit-scrollbar-thumb {
    background: var(--hairline);
  }

  .panel__head {
    padding-bottom: 16px;
    border-bottom: 1px solid var(--hairline);
  }

  .panel__fila {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
  }

  .panel__head h2 {
    margin-top: 12px;
    font-size: 19px;
    font-weight: 500;
    letter-spacing: -0.03em;
  }

  .panel__mock {
    flex: none;
    padding: 3px 8px;
    border: 1px dashed var(--amber);
    font: 9px/1.4 var(--mono);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--amber);
  }

  .panel__meta {
    margin-top: 7px;
    font: 10px var(--mono);
    color: var(--faint);
  }

  .panel__cuerpo {
    display: grid;
    gap: 16px;
    padding-top: 15px;
  }

  .detalle {
    display: grid;
    gap: 12px;
    padding-top: 15px;
  }

  .panel__volver {
    justify-self: start;
    padding: 6px 0 5px;
    border-bottom: 1px solid var(--muted);
    background: transparent;
    font: 10px var(--mono);
    color: var(--ink);
  }

  .detalle__intro {
    font: 10px/1.6 var(--mono);
    color: var(--faint);
  }

  /* Regiones lado a lado; en pantallas angostas se apilan. */
  .detalle__regiones {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .estado {
    display: grid;
    justify-items: center;
    gap: 12px;
    padding: 34px 10px;
    font: 11px var(--mono);
    color: var(--muted);
    text-align: center;
  }

  .estado--error {
    color: var(--ink);
  }

  .estado__barra {
    width: 150px;
    height: 1px;
    background: var(--hairline);
    overflow: hidden;
  }

  .estado__barra span {
    display: block;
    width: 40%;
    height: 100%;
    background: var(--amber);
    animation: barrido 1.4s cubic-bezier(0.65, 0, 0.35, 1) infinite;
  }

  .estado__reintentar {
    padding: 7px 14px;
    border: 1px solid var(--muted);
    background: transparent;
    font: 10px var(--mono);
    color: var(--ink);
  }

  .estado__reintentar:hover {
    border-color: var(--amber);
    color: var(--amber);
  }

  @keyframes barrido {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(250%);
    }
  }

  @media (max-width: 999px) {
    .panel {
      max-height: none;
    }
  }

  @media (max-width: 650px) {
    .panel {
      padding: 15px 16px 17px;
    }

    .detalle__regiones {
      grid-template-columns: 1fr;
    }
  }
</style>
